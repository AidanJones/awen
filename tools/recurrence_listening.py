"""Prepare a small frozen, blinded recurrence pilot; no inferred listener labels."""
import argparse
import itertools
import random
import subprocess
from pathlib import Path
import uuid

import score_lab as lab

VERSION = 'awen-recurrence-pilot-1'
TREATMENTS = ['cell', 'ostinato', 'varied', 'sustained']
SOURCE_FILES = ['index.html', 'tools/recurrence_listening.py', 'tools/recurrence-worker.cjs',
                'tools/recurrence-review.html', 'tools/recurrence_ratings.py', 'tools/score_lab.py', 'tools/score-lab.cjs',
                'tools/score-lab-metrics.cjs']


def sources():
    return {p: lab.sha((lab.ROOT/p).read_bytes()) for p in SOURCE_FILES}


def create(root):
    directory = Path(root).resolve()/(lab.stamp()+'-'+uuid.uuid4().hex)
    directory.mkdir(parents=True)
    manifest = dict(version=VERSION, id=uuid.uuid4().hex, sources=sources(),
        seed='recurrence-pilot-20261103', steps=192, treatments=TREATMENTS,
        reserved=dict(seeds=['recurrence-reserved-01', 'recurrence-reserved-02'],
                      palettes=['cello', 'pastoral'], rendered=False),
        scope='Authored arrangements; fixed harmony within each scene; two scene/timbre blocks, not a factorial style study.')
    raw=lab.encode(manifest)
    lab.atomic(directory/'experiment.json',raw,exclusive=True)
    lab.atomic(directory/'state.json',lab.encode(dict(manifestSha256=lab.sha(raw),status='created',jobs={},renderer=None)),exclusive=True)
    return directory


class Engine(lab.Engine):
    def __init__(self,directory,log,max_new_renders=None):
        self.directory=Path(directory).resolve()
        self.manifest,self.state=[lab.read(self.directory/p) for p in ['experiment.json','state.json']]
        if self.manifest['version']!=VERSION or self.manifest['sources']!=sources() or self.state['manifestSha256']!=lab.sha((self.directory/'experiment.json').read_bytes()):
            raise ValueError('Experiment/source identity changed; use a fresh run')
        self.log,self.retry,self.fault_hook=log,set(),lambda *_:None
        self.max_new_renders,self.new_renders=max_new_renders,0

    def worker(self,command,input_path,output_path,log_path):
        with Path(log_path).open('xb') as stream:
            subprocess.run(['node',str(lab.ROOT/'tools/recurrence-worker.cjs'),command,str(input_path),str(output_path)],cwd=lab.ROOT,stdout=stream,stderr=subprocess.STDOUT,check=True)

    def drive(self):
        self.state['status']='running';self.save()
        scenes=self.execute('plan',{})
        clips={}
        for scene in scenes:
            for treatment in TREATMENTS:
                payload=dict(scene=scene['id'],palette=scene['palette'],treatment=treatment,
                             transpose=0 if scene['id']=='rat' else -2,seed=self.manifest['seed'])
                result=self.execute('render',payload)
                _,job=self.ensure_job('render',payload)
                source=lab.safe(self.directory,job['result']).parent/result['file']
                # Opaque content identities do not expose treatment names in public URLs.
                name='audio/'+result['sha256'][:24]+'.wav'
                lab.atomic(self.directory/'public'/name,source.read_bytes(),exclusive=True)
                clips[scene['id'],treatment]=dict(file=name,seconds=result['seconds'],sha256=result['sha256'])
        packet,key=make_packet(self.manifest,scenes,clips)
        raw=lab.encode(packet);packet_sha=lab.sha(raw)
        template=(lab.ROOT/'tools/recurrence-review.html').read_text(encoding='utf-8')
        embedded=lab.encode(dict(packet=packet,packetSha256=packet_sha)).decode().replace('<','\\u003c')
        lab.atomic(self.directory/'private-key.json',lab.encode(key),exclusive=True)
        lab.atomic(self.directory/'packet.json',raw,exclusive=True)
        lab.atomic(self.directory/'public/review.html',template.replace('__CALIBRATION_DATA__',embedded).encode(),exclusive=True)
        report=dict(version=VERSION,packetSha256=packet_sha,clips=len(clips),trials=len(packet['trials']),
                    privateKeySha256=lab.sha(lab.encode(key)),
                    humanRatings=0,thresholdChanged=False,promotionAllowed=False,reserved=self.manifest['reserved'])
        lab.atomic(self.directory/'report.json',lab.encode(report),exclusive=True)
        self.state['status']='awaiting-listener';self.save()
        return report


def make_packet(manifest,scenes,clips):
    rng=random.Random(manifest['seed']);trials=[];key={}
    for scene in scenes:
        for a,b in itertools.combinations(TREATMENTS,2):
            if rng.randrange(2):a,b=b,a
            ident=uuid.uuid5(uuid.NAMESPACE_URL,manifest['id']+scene['id']+a+b).hex
            trials.append(dict(id=ident,scene=scene['id'],A=clips[scene['id'],a],B=clips[scene['id'],b]))
            key[ident]=dict(scene=scene['id'],A=a,B=b,repeatOf=None)
    # Two reversed repeats check individual consistency without declaring a correct answer.
    for original in [trials[0],trials[6]]:
        ident=uuid.uuid5(uuid.NAMESPACE_URL,manifest['id']+original['id']+'repeat').hex
        trials.append(dict(id=ident,scene=original['scene'],A=original['B'],B=original['A']))
        row=key[original['id']];key[ident]=dict(scene=row['scene'],A=row['B'],B=row['A'],repeatOf=original['id'])
    rng.shuffle(trials)
    return dict(id=manifest['id'],version=VERSION,instructions='Listen while reading, then judge each question separately. Excerpts last 86 seconds. You may pause, skip, choose a tie or stop. Use comfortable playback volume.',
                scenes=[{k:v for k,v in s.items() if k!='palette'} for s in scenes],trials=trials),key


def run(directory,max_new_renders=None,fault_hook=None):
    directory=Path(directory).resolve()
    with lab.RunLock(directory):
        log=lab.Invocation(directory)
        try:
            engine=Engine(directory,log,max_new_renders)
            if fault_hook:engine.fault_hook=fault_hook
            report=engine.drive();log.event('prepared',**report);return report
        except BaseException as e:
            log.event('stopped',exception=type(e).__name__);raise
        finally:log.close()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['start','resume']);p.add_argument('directory',nargs='?',type=Path)
    p.add_argument('--root',type=Path,default=lab.ROOT/'.score-lab/recurrence-listening');p.add_argument('--max-new-renders',type=int)
    args=p.parse_args()
    if args.command=='resume' and not args.directory:p.error('Resume needs a directory')
    if args.max_new_renders is not None and args.max_new_renders<0:p.error('Render budget must be nonnegative')
    directory=create(args.root) if args.command=='start' else args.directory.resolve()
    print('Experiment:',directory,flush=True)
    try:print(run(directory,args.max_new_renders))
    except lab.Paused as e:print('Paused:',e)


if __name__=='__main__':main()
