"""Small resumable MuQ/CLAP diagnostic on identical, previously rendered grid clips."""
import argparse
import array
import io
import json
from pathlib import Path
import sys
import uuid
import wave

import score_lab as lab
import score_embeddings as emb
import muq_backend as muq

VERSION='awen-muq-clap-comparison-1'
ROOT=lab.ROOT
SOURCES=['tools/compare_muq.py','tools/muq_backend.py','tools/clap_backend.py','tools/score_embeddings.py',
         'tools/score_lab.py','research/muq-model.json','research/muq-comparison-suite.json']
def sources(): return {p:lab.sha((ROOT/p).read_bytes()) for p in SOURCES}


def diagnostics(rows,silence,quiet):
    def mean(row,key):return sum(w[key] for w in row['scores'])/len(row['scores'])
    wording_flips=window_flips=0
    for i,a in enumerate(rows):
        for b in rows[i+1:]:
            wording_flips+=(mean(a,'target-1')-mean(b,'target-1'))*(mean(a,'target-2')-mean(b,'target-2'))<0
            margins=[sum(a['scores'][w][k]-b['scores'][w][k] for k in ['target-1','target-2']) for w in range(2)]
            window_flips+=margins[0]*margins[1]<0
    target_silence=(silence['target-1']+silence['target-2'])/2
    unused_silence=(silence['check-1']+silence['check-2'])/2
    original=next(r for r in rows if r['id']=='g2-2-8kqe3d')
    return dict(pairCount=len(rows)*(len(rows)-1)//2,wordingRankFlipPairs=wording_flips,windowRankFlipPairs=window_flips,
        silenceAboveTargetMean=[r['id'] for r in rows if target_silence>r['targetMean']],
        silenceAboveUnusedMean=[r['id'] for r in rows if unused_silence>r['unusedMean']],
        halfAmplitudeTargetDelta=sum(w[k] for w in quiet for k in ['target-1','target-2'])/4-original['targetMean'],
        positiveSpecificity=sum(r['specificity']>0 for r in rows))


def create(root,source):
    source=Path(source).resolve();raw=(source/'report.json').read_bytes();report=json.loads(raw)
    if report['version']!='awen-grid-clap-1' or report['status']!='exploratory-search-only': raise ValueError('Expected completed grid source')
    suite=lab.read(ROOT/'research/muq-comparison-suite.json');spec=lab.read(ROOT/'research/muq-model.json')
    identity=muq.identity(spec); directory=Path(root).resolve()/(lab.stamp()+'-'+uuid.uuid4().hex)
    directory.mkdir(parents=True)
    pool=report['initial']+[row for g in report['rounds'] for row in g['children']]
    rows=[];assets={}
    for id in suite['cards']:
        row=next(r for r in pool if r['card']['id']==id)
        if not row['gate']['eligible']: raise ValueError('Selected clip failed native gates')
        file=lab.safe(source,row['file']);data=file.read_bytes()
        if lab.sha(data)!=row['sha256']: raise ValueError('Source WAV changed')
        relative='assets/'+row['sha256']+'.wav';lab.atomic(directory/relative,data,exclusive=True)
        assets[relative]=row['sha256'];rows.append({**row,'file':relative})
    winner=next(r for r in rows if r['card']['id']=='g2-2-8kqe3d')
    with wave.open(str(directory/winner['file']),'rb') as handle:
        params=handle.getparams();values=array.array('h');values.frombytes(handle.readframes(handle.getnframes()))
    if sys.byteorder!='little':values.byteswap()
    values=array.array('h',(int(v*.5) for v in values))
    if sys.byteorder!='little':values.byteswap()
    buffer=io.BytesIO()
    with wave.open(buffer,'wb') as handle:handle.setparams(params);handle.writeframes(values.tobytes())
    lab.atomic(directory/'assets/half.wav',buffer.getvalue(),exclusive=True);assets['assets/half.wav']=lab.sha(buffer.getvalue())
    manifest=dict(version=VERSION,id=uuid.uuid4().hex,sources=sources(),suite=suite,identity=identity,
        identitySha256=lab.sha(lab.encode(identity)),assets=assets,rows=rows,
        captions={k:report['suite']['captions'][k] for k in suite['captionKeys']},
        clapIdentity=report['model'],clapIdentitySha256=lab.sha(lab.encode(report['model'])),
        sourceReportSha256=lab.sha(raw),cache=str(ROOT/'.score-lab/embedding-cache'),
        modelCache=str(ROOT/'.score-lab/muq-model'),createdAt=lab.now())
    raw=lab.encode(manifest);lab.atomic(directory/'experiment.json',raw,exclusive=True)
    lab.atomic(directory/'state.json',lab.encode(dict(version=VERSION,manifestSha256=lab.sha(raw),status='created',jobs={},
        renderer=None,judgeIdentity=None,judgeCallsStarted=0,computedFeatures=0,featureCacheHits=0)))
    return directory


class Engine(emb.EmbeddingEngine):
    def __init__(self,directory,log,max_new=None):
        self.directory=Path(directory).resolve();self.manifest=lab.read(self.directory/'experiment.json');self.state=lab.read(self.directory/'state.json')
        m=self.manifest
        if m['version']!=VERSION or self.state['manifestSha256']!=lab.sha((self.directory/'experiment.json').read_bytes()):raise ValueError('Manifest changed')
        if m['sources']!=sources() or m['identity']!=muq.identity(m['identity']['spec']):raise ValueError('Source/package identity changed')
        if m['identitySha256']!=lab.sha(lab.encode(m['identity'])):raise ValueError('Model identity checksum mismatch')
        self.log,self.retry=log,set();self.max_new_renders,self.new_renders=None,0
        self.max_new,self.new_features,self.download,self.backend=max_new,0,False,None
        self.factory,self.fault_hook=muq.MuQBackend,lambda *_:None

    def feature(self,model,kind,payload):
        identity=self.manifest['identity'] if model=='muq' else self.manifest['clapIdentity']
        payload={**payload,'kind':kind};payload['cacheKey']=emb.feature_key(identity,payload)
        if model=='muq':return self.execute('embedding-'+kind,payload)['vector']
        identity_sha=self.manifest['clapIdentitySha256']
        file=Path(self.manifest['cache'])/identity_sha/payload['cacheKey']/'vector.json'
        if not file.exists():raise ValueError('Required CLAP cache missing; compute with its original environment, never substitute encoders')
        return emb.vector_valid(lab.read(file),payload['cacheKey'],identity_sha,512)['vector']

    def audio_payload(self,file,start,silence=False):
        file=self.directory/file
        with wave.open(str(file),'rb') as handle:
            if (handle.getnchannels(),handle.getsampwidth(),handle.getframerate())!=(1,2,24000):raise ValueError('Wrong WAV format')
            handle.setpos(round(start*24000));pcm=handle.readframes(240000)
        if len(pcm)!=480000:raise ValueError('Short audio window')
        if silence:pcm=bytes(len(pcm))
        return dict(file=str(file.relative_to(self.directory)),wavSha256=lab.sha(file.read_bytes()),startFrame=round(start*24000),
                    frameCount=240000,silence=silence,pcmSha256=lab.sha(pcm))

    def drive(self):
        self.state['status']='running';self.save();m=self.manifest
        for file,checksum in m['assets'].items():
            if lab.sha(lab.safe(self.directory,file).read_bytes())!=checksum:raise ValueError('Pinned WAV changed')
        reports={}
        for model in ['clap','muq']:
            texts={key:self.feature(model,'text',dict(text=text,textSha256=lab.sha(text.encode()))) for key,text in m['captions'].items()}
            sanity=[self.feature(model,'text',dict(text=text,textSha256=lab.sha(text.encode()))) for text in m['identity']['spec']['textTowerSanity']['texts']]
            health=emb.text_tower_sanity(sanity,.995)
            if not health['usable']:raise ValueError(model+' text tower failed extreme-collapse check')
            rows=[]
            for row in m['rows']:
                vectors=[self.feature(model,'audio',self.audio_payload(row['file'],start)) for start in m['suite']['windows']]
                scores=[{key:emb.cosine(v,text) for key,text in texts.items()} for v in vectors]
                target=sum(w[k] for w in scores for k in ['target-1','target-2'])/4
                unused=sum(w[k] for w in scores for k in ['check-1','check-2'])/4
                specificity=target-sum(w['contrast'] for w in scores)/2
                rows.append(dict(id=row['card']['id'],name=row['card']['name'],scores=scores,targetMean=target,unusedMean=unused,specificity=specificity))
                print(model,row['card']['id'],round(target,5),round(unused,5),flush=True)
            silence_vector=self.feature(model,'audio',self.audio_payload(m['rows'][0]['file'],0,True))
            silence={k:emb.cosine(silence_vector,v) for k,v in texts.items()}
            quiet_vectors=[self.feature(model,'audio',self.audio_payload('assets/half.wav',start)) for start in m['suite']['windows']]
            quiet=[{k:emb.cosine(v,t) for k,t in texts.items()} for v in quiet_vectors]
            rank=lambda key:[r['id'] for r in sorted(rows,key=lambda r:(-r[key],r['id']))]
            reports[model]=dict(identity=m['clapIdentity'] if model=='clap' else m['identity'],textTowerSanity=health,
                rows=rows,targetRanking=rank('targetMean'),unusedRanking=rank('unusedMean'),silenceScores=silence,halfLevelScores=quiet,
                diagnostics=diagnostics(rows,silence,quiet))
        result=dict(version=VERSION,status='diagnostic-comparison-only',experimentId=m['id'],sourceReportSha256=m['sourceReportSha256'],
            suite=m['suite'],captions=m['captions'],models=reports,humanLabels=0,runtimeModified=False,deploymentApproved=False)
        lab.atomic(self.directory/'report.json',lab.encode(result),exclusive=True)
        self.state['status']='diagnostic-comparison-only';self.save()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['start','resume','status']);p.add_argument('experiment',nargs='?',type=Path)
    p.add_argument('--source',type=Path);p.add_argument('--root',type=Path,default=ROOT/'.score-lab/muq-comparison');p.add_argument('--max-new-features',type=int)
    a=p.parse_args()
    if a.command=='start' and not a.source:p.error('--source required')
    if a.command!='start' and not a.experiment:p.error('Experiment directory required')
    if a.max_new_features is not None and a.max_new_features<0:p.error('Budget must be nonnegative')
    directory=create(a.root,a.source) if a.command=='start' else a.experiment.resolve();print('Experiment:',directory,flush=True)
    if a.command=='status':print(lab.read(directory/'state.json')['status']);return
    with lab.RunLock(directory):
        log=lab.Invocation(directory);engine=None
        try:engine=Engine(directory,log,a.max_new_features);engine.drive();print('Complete:',directory/'report.json',flush=True)
        except lab.Paused as error:
            engine.state['status']='paused';engine.save();log.event('paused',reason=str(error));print(error,flush=True)
        except Exception as error:
            if engine:engine.state['status']='failed';engine.save()
            log.event('failed',exception=type(error).__name__);raise
        finally:log.close()


if __name__=='__main__':main()
