"""Score-only advisory critic. No waveform access, ML or claim of reading comfort."""
import argparse
from collections import Counter
import math
from pathlib import Path
import shutil
import subprocess
import uuid

import score_lab as lab

VERSION='awen-symbolic-advisory-1'
ROOT=lab.ROOT
SOURCES=['tools/symbolic_critic.py','tools/symbolic-plan.cjs','tools/symbolic-score.cjs','tools/score_lab.py',
         'tools/score-lab.cjs','index.html']
PROFILES={'calm':(.25,1.2),'neutral':(.4,2.4),'active':(1.,2.6)}


def sources():return {p:lab.sha((ROOT/p).read_bytes()) for p in SOURCES}


def evaluate(events,steps,chords=None,style='lyric',profile='neutral',start_step=0):
    if type(start_step) is not int or not 0<=start_step<=100000000:
        raise ValueError('Invalid absolute phrase origin')
    if type(steps) is not int or not 1<=steps<=4096 or not isinstance(events,list) or len(events)>50000 or style not in ['lyric','figured'] or profile not in PROFILES:
        raise ValueError('Unsupported score/profile bounds')
    if chords is not None and (len(chords)!=steps or any(not isinstance(c,list) or not 1<=len(c)<=12 or any(type(n) is not int or not 0<=n<12 for n in c) for c in chords)):
        raise ValueError('Invalid harmonic context')
    for e in events:
        if any(type(e.get(k)) is not int for k in ['step','midi','layer']) or not 0<=e['step']<steps or not 0<=e['midi']<=127 or not 0<=e['layer']<=3 or type(e.get('duration')) not in (int,float) or not math.isfinite(e['duration']) or not 0<e['duration']<=16:
            raise ValueError('Invalid note event')
    ordered=sorted(events,key=lambda e:(e['step'],e['layer'],e['midi']));seconds=steps*5/12
    melody=[e for e in ordered if e['layer']==2];mono=len({e['step'] for e in melody})==len(melody)
    transitions=[(a,b) for a,b in zip(melody,melody[1:]) if (a['step']+start_step)//32==(b['step']+start_step)//32 and b['step']-a['step']<=8] if mono else []
    leaps=[abs(b['midi']-a['midi']) for a,b in transitions];limit=12 if style=='figured' else 7
    nonchord=[(i,e) for i,e in enumerate(melody) if e['midi']%12 not in chords[e['step']]] if chords is not None and mono else []
    resolved=[]
    for i,e in nonchord:
        nxt=melody[i+1] if i+1<len(melody) else None
        resolved.append(bool(nxt and 0<nxt['step']-e['step']<=2 and 0<abs(nxt['midi']-e['midi'])<=3 and nxt['midi']%12 in chords[nxt['step']]))
    overlap_pairs=semitones=tritones=0;active=[]
    for e in ordered:
        start=e['step']*5/12;active=[a for a in active if a[0]>start+.04]
        if len(active)>256:raise ValueError('Excessive overlap complexity')
        for end,old in active:
            if min(end,start+e['duration'])-start<.04:continue
            pc=abs(e['midi']-old['midi'])%12;pc=min(pc,12-pc)
            overlap_pairs+=1;semitones+=pc==1;tritones+=pc==6
        active.append((start+e['duration'],e))
    bars=[tuple(e['step']%8 for e in melody if e['step']//8==bar) for bar in range(steps//8)]
    contours=[]
    for bar in range(steps//8):
        notes=[e for e in melody if e['step']//8==bar]
        contours.append(tuple((e['step']%8,e['midi']-notes[0]['midi']) for e in notes))
    attacks=len({e['step'] for e in ordered})/seconds;lo,hi=PROFILES[profile]
    activity=1. if lo<=attacks<=hi else max(0.,1-min(abs(attacks-lo),abs(attacks-hi))/max(hi,1.))
    warnings=['Advisory style-dependent rules; not musical quality or reading comfort.',
              'Only scheduled notes are covered; continuous bed, timbre, mix, rendering and perceived loudness are not assessed.',
              'Parallel/hidden fifths and full counterpoint require stable voice identities and are not implemented.']
    if not mono:warnings.append('Polyphonic melody layer: melodic line and ornament scores abstain.')
    if len(contours)<3:warnings.append('Too few complete bars for motif interpretation.')
    if chords is None:warnings.append('No explicit harmonic context: chord/ornament analysis abstains.')
    if not ordered:warnings.append('Empty score; not a selectable musical winner.')
    return dict(version=VERSION,ruleBased=True,humanPreferenceValidated=False,
        coverage=dict(waveformRead=False,scheduledNotesOnly=True,explicitHarmony=chords is not None,monophonicMelody=mono),
        profile=profile,style=style,metrics=dict(notes=len(ordered),seconds=seconds,notesPerSecond=len(ordered)/seconds,
            attacksPerSecond=attacks,melodicTransitions=len(leaps),largeLeaps=sum(v>limit for v in leaps),maximumLeap=max(leaps,default=None),
            nonChordMelodyNotes=len(nonchord) if chords is not None and mono else None,resolvedOrnaments=sum(resolved),
            chordToneFraction=sum(e['midi']%12 in chords[e['step']] for e in ordered)/len(ordered) if chords is not None and ordered else None,
            completeBars=len(bars),uniqueRhythmBars=len(set(bars)),uniqueContourBars=len(set(contours)),
            adjacentContourRepeatFraction=sum(a==b for a,b in zip(contours,contours[1:]))/(len(contours)-1) if len(contours)>1 else None,
            overlappingNotePairs=overlap_pairs,semitoneClassOverlapFraction=semitones/overlap_pairs if overlap_pairs else None,
            tritoneClassOverlapFraction=tritones/overlap_pairs if overlap_pairs else None),
        advisoryScores=dict(melodicEconomy=1-sum(v>limit for v in leaps)/len(leaps) if leaps else None,
            ornamentResolution=sum(resolved)/len(resolved) if resolved else None,
            activityTargetMatch=activity if ordered else None),warnings=warnings)


def create(root,source):
    source=Path(source).resolve();report=lab.read(source/'report.json');manifest=lab.read(source/'experiment.json')
    if report.get('version')!='awen-multiobjective-prototype-1' or report.get('status')!='engineering-only':raise ValueError('Expected completed prototype source')
    if manifest['sources']['index.html']!=lab.sha((ROOT/'index.html').read_bytes()):raise ValueError('Runtime changed; cannot infer old harmonic plans with current code')
    state=lab.read(source/'state.json')
    if state['status']!='complete' or state['manifestSha256']!=lab.sha((source/'experiment.json').read_bytes()) or report['sources']!=manifest['sources']:raise ValueError('Incomplete/changed source experiment')
    jobs={lab.safe(source,j['result']):j for j in state['jobs'].values() if j['kind']=='render' and j['status']=='complete'}
    directory=Path(root).resolve()/(lab.stamp()+'-'+uuid.uuid4().hex);directory.mkdir(parents=True)
    rows=[];plans=[];profiles={'rat-escape':'active','riders-landscape':'calm','time-discussion':'neutral'}
    for group in report['scenes']:
        for row in group['initial']+group['children']:
            # Read trace/result JSON only. No WAV is opened, decoded or played.
            audio_path=lab.safe(source,row['file']);folder=audio_path.parent;result_path=folder/'result.json';job=jobs.get(result_path)
            if not job or lab.sha(result_path.read_bytes())!=job['resultSha256']:raise ValueError('Unverified source render result')
            input_path=lab.safe(source,job['input'])
            if lab.sha(input_path.read_bytes())!=job['inputSha256']:raise ValueError('Source render input changed')
            original=lab.read(input_path)
            if original['card']!=row['card'] or original['scene']!=group['scene']['index']:raise ValueError('Report score/scene disagrees with archived renderer input')
            envelope=lab.read(result_path);result=envelope['result']
            if envelope['requestSha256']!=job['inputSha256']:raise ValueError('Wrong source result request')
            if result['sha256']!=row['sha256']:raise ValueError('Source render identity mismatch')
            trace_path=lab.safe(source,str((folder/result['traceFile']).relative_to(source)))
            if lab.sha(trace_path.read_bytes())!=result['traceSha256']:raise ValueError('Source trace changed')
            trace=lab.read(trace_path);id=group['scene']['id']+'/'+row['card']['id'];steps=len(trace['trace'])
            rows.append(dict(id=id,events=trace['events'],steps=steps,profile=profiles[group['scene']['id']],traceSha256=result['traceSha256'],originalGate=row['gate']))
            plans.append(dict(id=id,steps=steps,genome=row['card']['genome']))
    lab.atomic(directory/'plan-input.json',lab.encode(plans),exclusive=True)
    with (directory/'plan-worker.log').open('xb') as log:
        proc=subprocess.run([shutil.which('node') or 'node',str(ROOT/'tools/symbolic-plan.cjs'),str(directory/'plan-input.json'),str(directory/'plans.json')],stdout=log,stderr=subprocess.STDOUT)
    if proc.returncode:raise RuntimeError('Symbolic plan export failed; see plan-worker.log')
    expected={p['id']:p for p in lab.read(directory/'plans.json')}
    for row in rows:row.update(chords=expected[row['id']]['chords'],style=expected[row['id']]['style'])
    spec=dict(version=VERSION,id=uuid.uuid4().hex,sourceReportSha256=lab.sha((source/'report.json').read_bytes()),
        sources=sources(),rows=rows,profileInterpretation='developer-authored scene targets, not validated text classifications',
        skippedControls=sum(len(g['controls']) for g in report['scenes']),controlReason='waveform-only transformations have no corresponding transformed score; do not reuse original notes as their score')
    raw=lab.encode(spec);lab.atomic(directory/'experiment.json',raw,exclusive=True)
    lab.atomic(directory/'state.json',lab.encode(dict(version=VERSION,manifestSha256=lab.sha(raw),status='created',jobs={},renderer=None,judgeIdentity=None)))
    return directory


class Engine(lab.Engine):
    def __init__(self,directory,log):
        self.directory=Path(directory).resolve();self.manifest=lab.read(self.directory/'experiment.json');self.state=lab.read(self.directory/'state.json')
        if self.manifest['version']!=VERSION or self.state['manifestSha256']!=lab.sha((self.directory/'experiment.json').read_bytes()) or self.manifest['sources']!=sources():raise ValueError('Symbolic source/identity changed')
        self.log=log;self.retry=set();self.fault_hook=lambda *_:None
    def worker(self,command,input_path,output_path,log_path):
        if command!='symbolic':raise ValueError('Unexpected symbolic job')
        row=lab.read(input_path);result=evaluate(row['events'],row['steps'],row['chords'],row['style'],row['profile']);result['id']=row['id'];result['traceSha256']=row['traceSha256'];result['originalGate']=row['originalGate']
        lab.atomic(log_path,b'Score-only rules; no waveform access or learned feedback.\n',exclusive=True)
        lab.atomic(output_path,lab.encode(dict(requestSha256=lab.sha(input_path.read_bytes()),result=result)),exclusive=True)
    def drive(self):
        self.state['status']='running';self.save()
        rows=[self.execute('symbolic',row) for row in self.manifest['rows']]
        report=dict(version=VERSION,ruleBased=True,promotionAllowed=False,humanRatings=0,sourceReportSha256=self.manifest['sourceReportSha256'],rows=rows,
            skippedControls=self.manifest['skippedControls'],controlReason=self.manifest['controlReason'],profileInterpretation=self.manifest['profileInterpretation'])
        lab.atomic(self.directory/'report.json',lab.encode(report));self.state['status']='complete';self.save();return report


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['start','resume']);p.add_argument('experiment',nargs='?',type=Path);p.add_argument('--source',type=Path);p.add_argument('--root',type=Path,default=ROOT/'.score-lab/symbolic-critic');args=p.parse_args(argv)
    if args.command=='start' and not args.source:p.error('Source experiment required')
    if args.command=='resume' and not args.experiment:p.error('Experiment path required')
    directory=create(args.root,args.source) if args.command=='start' else args.experiment.resolve();print('Experiment:',directory,flush=True)
    with lab.RunLock(directory):
        log=lab.Invocation(directory);engine=Engine(directory,log)
        try:engine.drive();log.event('complete',reportSha256=lab.sha((directory/'report.json').read_bytes()));print('Complete:',directory/'report.json')
        except BaseException as error:engine.state['status']='failed';engine.save();log.event('failed',exception=type(error).__name__);raise
        finally:log.close()


if __name__=='__main__':main()
