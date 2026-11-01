"""Resumable native-audio Pareto prototype: real optional CLAP + synthetic-label test regressors.

Never deploys a winner. All enjoyment/comfort predictions are TEST ONLY.
"""
import argparse
import array
import html
import io
import math
from pathlib import Path
import shutil
import sys
import uuid
import wave

import score_lab as lab
import score_embeddings as emb
from grid_clap import GridEngine
from clap_backend import ClapBackend
from exploration_page import build
import reward_test_models as rewards

ROOT=lab.ROOT
VERSION='awen-multiobjective-prototype-1'
SOURCES=['index.html','tools/multiobjective_lab.py','tools/reward_test_models.py',
         'tools/grid_clap.py','tools/grid-clap-worker.cjs','tools/score_lab.py',
         'tools/score_embeddings.py','tools/clap_backend.py','tools/score-lab-metrics.cjs',
         'tools/exploration_page.py','tools/exploration-review.html',
         'research/multiobjective-suite.json','research/calibration-scenes.json',
         'research/scoring-knowledge.json','research/clap-probe-model.json']


def sources():
    return {name:lab.sha((ROOT/name).read_bytes()) for name in SOURCES}


def create(root, fit='test'):
    if fit not in ('test','clap'):raise ValueError('Unknown fit backend')
    suite=lab.read(ROOT/'research/multiobjective-suite.json')
    if suite['version']!=1 or suite['seconds']!=32 or suite['generations']!=1 or len(suite['scenes'])!=3 or len(set(suite['cardIds']))!=4 or suite['childrenPerScene']!=2 or suite['windows']!=[2,18] or suite['controls']!=['silence','half-level','two-second-loop']:
        raise ValueError('This pilot is bounded to three scenes, four roots and one generation')
    if len({s['id'] for s in suite['scenes']})!=3 or any(type(s['index']) is not int or not 0<=s['index']<6 or len(s['briefs'])!=2 or any(not isinstance(t,str) or not 1<=len(t)<400 for t in s['briefs']+[s['checkBrief']]) or s['checkBrief'] in s['briefs'] or not 0<=s['testTargetDensity']<=1 for s in suite['scenes']):
        raise ValueError('Invalid frozen scene/brief bounds')
    spec=lab.read(ROOT/'research/clap-probe-model.json')
    identity=emb.model_identity(spec) if fit=='clap' else {'backend':'synthetic-fit-test-only'}
    directory=Path(root).resolve()/(lab.stamp()+'-'+uuid.uuid4().hex);directory.mkdir(parents=True)
    page=build(directory/'public');model=rewards.train();model_raw=lab.encode(model)
    lab.atomic(directory/'test-models.json',model_raw,exclusive=True)
    manifest=dict(version=VERSION,id=uuid.uuid4().hex,createdAt=lab.now(),sources=sources(),suite=suite,
                  fitBackend=fit,identity=identity,identitySha256=lab.sha(lab.encode(identity)),
                  pageSha256=lab.sha(page.read_bytes()),testModelsSha256=lab.sha(model_raw),
                  cache=str(ROOT/'.score-lab/embedding-cache'),modelCache=str(ROOT/'.score-lab/huggingface'))
    raw=lab.encode(manifest);lab.atomic(directory/'experiment.json',raw,exclusive=True)
    lab.atomic(directory/'state.json',lab.encode(dict(version=VERSION,manifestSha256=lab.sha(raw),
        status='created',jobs={},renderer=None,judgeIdentity=None,judgeCallsStarted=0,
        computedFeatures=0,featureCacheHits=0)))
    return directory


def transform_control(file, kind):
    with wave.open(str(file),'rb') as wav:
        params=wav.getparams();values=array.array('h');values.frombytes(wav.readframes(wav.getnframes()))
    if sys.byteorder!='little':values.byteswap()
    if kind=='silence':values=array.array('h',[0])*len(values)
    elif kind=='half-level':values=array.array('h',(int(v*.5) for v in values))
    elif kind=='two-second-loop':
        segment=values[24000:72000];values=(segment*((len(values)+len(segment)-1)//len(segment)))[:len(values)]
    else:raise ValueError('Unknown control')
    peak=max(abs(v) for v in values)/32768.;rms=math.sqrt(sum((v/32768.)**2 for v in values)/len(values))
    if sys.byteorder!='little':values.byteswap()
    out=io.BytesIO()
    with wave.open(out,'wb') as wav:wav.setparams(params);wav.writeframes(values.tobytes())
    return out.getvalue(),dict(peak=peak,rms=rms,finite=True)


def validate_prediction(result, model_hash):
    if result.get('modelSha256')!=model_hash or result.get('testOnly') is not True or set(result.get('objectives',{}))!=set(rewards.AXES):
        raise ValueError('Reward result identity/axes changed')
    if not all(type(v) in (int,float) and math.isfinite(v) and 0<=v<=1 for v in result['objectives'].values()):
        raise ValueError('Invalid learned test score')
    return result


class Engine(GridEngine):
    def __init__(self,directory,log,max_renders=None,max_features=None):
        self.directory=Path(directory).resolve();self.manifest=lab.read(self.directory/'experiment.json');self.state=lab.read(self.directory/'state.json');m=self.manifest
        if m['version']!=VERSION or self.state['version']!=VERSION or self.state['manifestSha256']!=lab.sha((self.directory/'experiment.json').read_bytes()):raise ValueError('Experiment identity changed')
        if m['sources']!=sources():raise ValueError('Source changed; start a new experiment')
        if m['fitBackend']=='clap' and m['identity']!=emb.model_identity(m['identity']['spec']):raise ValueError('CLAP packages/model identity changed')
        if m['identitySha256']!=lab.sha(lab.encode(m['identity'])):raise ValueError('Model identity hash mismatch')
        self.page=self.directory/'public/explore.html'
        if lab.sha(self.page.read_bytes())!=m['pageSha256']:raise ValueError('Embedded renderer changed')
        if lab.sha((self.directory/'test-models.json').read_bytes())!=m['testModelsSha256']:raise ValueError('Test-model artifact changed')
        self.models=lab.read(self.directory/'test-models.json');self.node=shutil.which('node')
        if not self.node:raise RuntimeError('Node required')
        self.log,self.retry,self.backend=log,set(),None
        self.max_new_renders,self.new_renders=max_renders,0
        self.max_new,self.new_features=max_features,0
        self.download,self.factory=False,ClapBackend;self.fault_hook=lambda *_:None

    def verify(self,job,path):
        result=super().verify(job,path)
        if job['kind']=='test-reward':validate_prediction(result,self.manifest['testModelsSha256'])
        return result

    def worker(self,command,input_path,output_path,log_path):
        if command!='test-reward':return super().worker(command,input_path,output_path,log_path)
        payload=lab.read(input_path)
        if payload['modelSha256']!=self.manifest['testModelsSha256']:raise ValueError('Wrong test-model request')
        result=dict(testOnly=True,modelSha256=payload['modelSha256'],objectives=rewards.predict(self.models,payload['features'],payload['density']))
        validate_prediction(result,self.manifest['testModelsSha256'])
        with Path(log_path).open('x',encoding='utf-8') as stream:stream.write('Synthetic-label fitted ridge model inference; not human feedback.\n')
        lab.atomic(output_path,lab.encode(dict(requestSha256=lab.sha(input_path.read_bytes()),result=result)),exclusive=True)

    def score_file(self,file,scene,captions,sha256):
        features=self.features(file,sha256)
        learned=self.execute('test-reward',dict(features=features,density=scene['testTargetDensity'],
            wavSha256=sha256,modelSha256=self.manifest['testModelsSha256']))
        objectives=dict(learned['objectives']);window_scores=[]
        if self.manifest['fitBackend']=='clap':
            for start in self.manifest['suite']['windows']:
                v=self.audio(file,start)
                window_scores.append({id:sum(emb.cosine(v,t) for t in vv)/len(vv) for id,vv in captions.items()})
            own=sum(w[scene['id']] for w in window_scores)/len(window_scores)
            other=sum(value for w in window_scores for key,value in w.items() if key!=scene['id'])/(len(window_scores)*(len(captions)-1))
            objectives['fit']=own-other
        return dict(objectives=objectives,features=features,clapWindowSceneMeans=window_scores,
                    rawTestPredictions=learned['objectives'])

    def features(self,file,sha256):
        if lab.sha(file.read_bytes())!=sha256:raise ValueError('Audio changed before feature extraction')
        path=self.directory/'audio-features'/(sha256+'.json')
        if path.exists():
            cached=lab.read(path);features=cached.get('features')
            if cached.get('wavSha256')!=sha256 or cached.get('extractorSha256')!=self.manifest['sources']['tools/reward_test_models.py'] or cached.get('featuresSha256')!=lab.sha(lab.encode(features)):
                raise ValueError('Audio feature cache changed')
            rewards.basis(features,0.)
            self.log.event('audio_features_cache_hit',wavSha256=sha256)
            return features
        features=rewards.audio_features(file)
        lab.atomic(path,lab.encode(dict(wavSha256=sha256,extractorSha256=self.manifest['sources']['tools/reward_test_models.py'],features=features,featuresSha256=lab.sha(lab.encode(features)))),exclusive=True)
        self.log.event('audio_features_computed',wavSha256=sha256)
        return features

    def evaluate_card(self,card,scene,captions):
        payload=dict(page=str(self.page),card=card,seed=self.manifest['suite']['seed']+'|'+scene['id'],scene=scene['index'],seconds=self.manifest['suite']['seconds'])
        render=self.execute('render',payload);_,job=self.ensure_job('render',payload)
        file=lab.safe(self.directory,job['result']).parent/render['file']
        row=dict(card=card,sceneId=scene['id'],file=str(file.relative_to(self.directory)),sha256=render['sha256'],
                 gate=render['gate'],signal=render['signal'],structure=render['structure'],renderer=render['renderer'])
        row.update(self.score_file(file,scene,captions,row['sha256']))
        self.log.event('vector_scored',scene=scene['id'],candidate=card['id'],objectives=row['objectives'],eligible=row['gate']['eligible'])
        print(scene['id'],card['id'],row['objectives'],flush=True)
        return row

    def control(self,base,scene,captions,kind):
        raw,signal=transform_control(self.directory/base['file'],kind)
        relative='controls/'+scene['id']+'-'+kind+'.wav';file=self.directory/relative;lab.atomic(file,raw,exclusive=True)
        row=dict(card=dict(id='control-'+kind,name=kind),sceneId=scene['id'],control=kind,file=relative,
                 sha256=lab.sha(raw),signal=signal,gate=dict(eligible=False,reasons=['diagnostic control; excluded from selection']))
        row.update(self.score_file(file,scene,captions,row['sha256']));return row

    def drive(self):
        self.state['status']='running';self.save();m=self.manifest;s=m['suite']
        plan=self.execute('grid-plan',dict(page=str(self.page),startingSet='classical'))
        cards={c['id']:c for c in plan['cards']};captions={};sanity=None
        if m['fitBackend']=='clap':
            vectors=[self.text(t) for t in m['identity']['spec']['textTowerSanity']['texts']]
            sanity=emb.text_tower_sanity(vectors,m['identity']['spec']['textTowerSanity']['rejectIfMinimumPairwiseCosineAbove'])
            if not sanity['usable']:raise ValueError('Text tower failed sanity guard')
            captions={scene['id']:[self.text(t) for t in scene['briefs']] for scene in s['scenes']}
        results=[]
        for scene in s['scenes']:
            context=plan['scenes'][scene['index']]
            if context['id']!=scene['id'] or context['book']['id']!=scene['book']:raise ValueError('Scene definition changed')
            roots=[self.evaluate_card(cards[id],scene,captions) for id in s['cardIds']]
            parents=rewards.parents(roots,2)
            if not parents:raise ValueError('No eligible parents')
            children=self.execute('grid-children',dict(page=str(self.page),parents=[r['card'] for r in parents],
                generation=1,seed=s['seed']+'|'+scene['id'],count=s['childrenPerScene']))
            offspring=[self.evaluate_card(card,scene,captions) for card in children]
            pool=roots+offspring
            controls=[self.control(roots[0],scene,captions,kind) for kind in s['controls']]
            # Unused wording is scored only after the front is fixed, never entering selection.
            check={}
            if m['fitBackend']=='clap':
                text=self.text(scene['checkBrief'])
                for row in rewards.pareto(pool):
                    check[row['card']['id']]=sum(emb.cosine(self.audio(self.directory/row['file'],start),text) for start in s['windows'])/len(s['windows'])
            result=dict(scene=scene,context=context,initial=roots,parents=[r['card']['id'] for r in parents],
                        children=offspring,paretoIds=[r['card']['id'] for r in rewards.pareto(pool)],controls=controls,unusedWordingScores=check)
            lab.atomic(self.directory/('scene-'+scene['id']+'.json'),lab.encode(result),exclusive=True);results.append(result)
        report=dict(version=VERSION,status='engineering-only',testOnly=True,promotionAllowed=False,
            humanRatings=0,fitBackend=m['fitBackend'],fitInterpretation='CLAP association margin; not validated scene fit' if captions else 'synthetic-label test regressor',
            otherObjectives='fitted regressors trained only on rule-generated synthetic labels; not enjoyment/comfort evidence',
            modelIdentity=m['identity'],testModelsSha256=m['testModelsSha256'],syntheticHoldoutMSE=self.models['syntheticHoldoutMSE'],
            sources=m['sources'],suite=s,scenes=results,textTowerSanity=sanity,
            computedFeatures=self.state['computedFeatures'],featureCacheHits=self.state['featureCacheHits'],renderer=self.state['renderer'])
        lab.atomic(self.directory/'report.json',lab.encode(report))
        self.listening_page(report);self.state['status']='complete';self.save()
        self.log.event('complete',reportSha256=lab.sha(lab.encode(report)))
        return report

    def listening_page(self,report):
        parts=['<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Multi-objective score prototype</title><style>body{max-width:1080px;margin:auto;padding:24px;background:#f4f1e8;color:#26352d;font:16px/1.5 system-ui}table{border-collapse:collapse}td,th{padding:10px;border:1px solid #9caa9e;text-align:left}audio{width:230px;max-width:100%}.scroll{overflow:auto}button{font:inherit;padding:8px}blockquote{margin:16px 0}.control{opacity:.75}</style><h1>Multi-objective score prototype</h1><p><strong>Engineering test. No validated reward, listener labels or automatic adoption.</strong></p><p>Fit: '+html.escape(report['fitInterpretation'])+'. Enjoyment and unobtrusiveness: synthetic-label fitted test models. Higher is the model’s preference, not evidence of better reading music.</p><button id="stop">Stop all audio</button>']
        for group in report['scenes']:
            parts+=['<h2>'+html.escape(group['scene']['id'])+'</h2><blockquote>'+html.escape(group['context']['text'])+'</blockquote><p>Pareto candidates are trade-offs under these test objectives, not recommended winners.</p><div class="scroll"><table><tr><th>Direction</th><th>Playback</th><th>Fit</th><th>Test enjoyment</th><th>Test unobtrusiveness</th><th>Status</th></tr>']
            for row in group['initial']+group['children']+group['controls']:
                source=self.directory/row['file'];raw=source.read_bytes()
                if lab.sha(raw)!=row['sha256']:raise ValueError('Audio changed before publishing review')
                filename=row['sha256']+'.wav';lab.atomic(self.directory/'public/audio'/filename,raw,exclusive=True)
                status='control; excluded' if row.get('control') else 'rejected: '+', '.join(row['gate']['reasons']) if not row['gate']['eligible'] else 'Pareto trade-off' if row['card']['id'] in group['paretoIds'] else 'dominated'
                parts+=['<tr class="'+('control' if row.get('control') else '')+'"><td>'+html.escape(row['card']['name'])+'</td><td><audio controls preload="none" src="audio/'+filename+'"></audio></td>'+''.join('<td>'+format(row['objectives'][key],'.4f')+'</td>' for key in rewards.AXES)+'<td>'+html.escape(status)+'</td></tr>']
            parts+=['</table></div><p>Source: '+html.escape(group['context']['book']['title'])+' · '+html.escape(group['context']['book']['url'])+'</p>']
        parts+=['<script>const stop=()=>document.querySelectorAll("audio").forEach(a=>a.pause());document.getElementById("stop").onclick=stop;document.addEventListener("keydown",e=>{if(e.key==="Escape")stop()});document.addEventListener("play",e=>document.querySelectorAll("audio").forEach(a=>{if(a!==e.target)a.pause()}),true);document.addEventListener("visibilitychange",()=>{if(document.hidden)stop()});</script></html>']
        lab.atomic(self.directory/'public/multiobjective.html',''.join(parts).encode('utf-8'))


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['start','resume','status']);parser.add_argument('experiment',nargs='?',type=Path)
    parser.add_argument('--root',type=Path,default=ROOT/'.score-lab/multiobjective');parser.add_argument('--fit',choices=['test','clap'],default='test')
    parser.add_argument('--max-new-renders',type=int);parser.add_argument('--max-new-features',type=int)
    args=parser.parse_args(argv)
    if any(v is not None and v<0 for v in [args.max_new_renders,args.max_new_features]):parser.error('Nonnegative budgets required')
    if args.command!='start' and not args.experiment:parser.error('Experiment path required')
    directory=create(args.root,args.fit) if args.command=='start' else args.experiment.resolve()
    print('Experiment:',directory,flush=True)
    print('TEST ONLY enjoyment/comfort heads; no validated reward or automatic adoption.',flush=True)
    if args.command=='status':print(lab.read(directory/'state.json')['status']);return
    with lab.RunLock(directory):
        log=lab.Invocation(directory);engine=None
        try:
            engine=Engine(directory,log,args.max_new_renders,args.max_new_features);engine.drive()
            print('Complete:',directory/'public/multiobjective.html',flush=True)
        except lab.Paused as error:
            if engine:engine.state['status']='paused';engine.save()
            log.event('paused',reason=str(error));print(str(error),flush=True)
        except BaseException as error:
            if engine:engine.state['status']='failed';engine.save()
            log.event('failed',exception=type(error).__name__);raise
        finally:log.close()


if __name__=='__main__':main()
