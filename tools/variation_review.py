"""Read-only variation diagnostics; repetition is not a universal quality penalty."""
import argparse
from pathlib import Path
import uuid

import score_lab as lab
import symbolic_critic as critic

ROOT = lab.ROOT
VERSION = 'awen-variation-review-1'


def sources():
    return {p: lab.sha((ROOT/p).read_bytes()) for p in
            ['tools/variation_review.py','tools/symbolic_critic.py','tools/score_lab.py']}


def diagnose(row):
    events, steps, chords = row['events'], row['steps'], row.get('chords')
    critic.evaluate(events, steps, chords, row['style'], row['profile'])  # Bounds only; no waveform.
    complete = steps//32
    grid = [[] for _ in range(complete*32)]
    for e in events:
        if e['step'] < len(grid):
            grid[e['step']].append((e['layer'], e['midi'], round(e['duration'],3), e.get('instrument','unknown')))
    grid = [tuple(sorted(slot)) for slot in grid]
    phrases = [grid[n*32:(n+1)*32] for n in range(complete)]
    full = [tuple(phrase) for phrase in phrases]
    notes = [tuple(tuple((e[0],e[1]) for e in slot) for slot in phrase) for phrase in phrases]
    contours = []
    for phrase in phrases:
        origins = {}
        contour = []
        for slot in phrase:
            parts = []
            for layer, midi, duration, instrument in slot:
                origins.setdefault(layer,midi)
                parts.append((layer,midi-origins[layer]))
            contour.append(tuple(parts))
        contours.append(tuple(contour))
    period = next((p for p in [1,2,4,8,16,32] if grid and any(grid) and all(grid[i]==grid[i%p] for i in range(len(grid)))),None)
    harmony = [tuple(sorted(set(c))) for c in chords] if chords is not None else None
    changes = sum(a!=b for a,b in zip(harmony,harmony[1:])) if harmony else None
    flags = []
    if complete < 2:
        flags.append('Less than two complete phrases: between-phrase variation is under-observed.')
    if complete >= 2 and len(set(notes)) == 1:
        flags.append('Four-bar note material repeats; this may be intentional.')
    if len(set(full)) > len(set(notes)):
        flags.append('Some phrase distinctions come only from duration/instrument details, not note/onset changes.')
    if period is not None and period <= 8:
        flags.append('A one-bar-or-shorter grid cell repeats; musical suitability remains style/context dependent.')
    if not events:
        flags.append('Empty scheduled score; no positive musical conclusion.')
    return dict(id=row['id'], declaredStyle=row['style'], originalGate=row.get('originalGate'),
                diagnostics=dict(completePhrases=complete,partialTailSlots=steps%32,
                    millisecondDurationInstrumentPhrasePatterns=len(set(full)),pitchRhythmPhrasePatterns=len(set(notes)),
                    layerRelativeContourPhrasePatterns=len(set(contours)),shortestExactGridPeriodSlots=period,
                    completeWindowDistinctPitches=len({e[1] for slot in grid for e in slot}),
                    completeWindowOnsetSlots=sum(bool(slot) for slot in grid),explicitHarmonicChanges=changes),
                flags=flags, qualityScore=None, promotionAllowed=False, thresholdChanged=False,
                limitations=['Full saved scheduled trace, not guaranteed to equal a cropped listening interval.',
                             'Layer-relative contours do not establish independent voice identity.',
                             'Continuous bed, acoustic envelopes, perceived repetition and listener tolerance are not assessed.'])


def controls():
    def row(id, events, steps=64, chords=None):
        return dict(id='CONTROL/'+id, events=events, steps=steps, chords=chords or [[0,4,7]]*steps,
                    style='figured', profile='neutral', originalGate=None, provenance='authored-notation-control')
    def note(step,midi,duration=.4):
        return dict(step=step,midi=midi,layer=2,duration=duration,instrument='felt')
    ostinato = [note(bar*8+slot,midi) for bar in range(8) for slot,midi in [(0,60),(2,64),(4,67),(6,64)]]
    jitter = [dict(e,duration=.4 if e['step']<32 else .402) for e in ostinato]
    transpose = [dict(e,midi=e['midi']+(2 if e['step']>=32 else 0)) for e in ostinato]
    return [row('ostinato',ostinato),row('short-cell',[note(s,60) for s in range(0,64,2)]),
            row('duration-jitter',jitter),row('transposed-figure',transpose,chords=[[0,4,7]]*32+[[2,6,9]]*32),
            row('single-phrase',ostinato[:16],32),row('sparse-line',[note(0,60,2),note(48,64,2)]),row('empty',[])]


def create(root, source):
    source = Path(source).resolve()
    manifest, state, report = [lab.read(source/p) for p in ['experiment.json','state.json','report.json']]
    if manifest['version'] != critic.VERSION or state['status'] != 'complete' or state['manifestSha256'] != lab.sha((source/'experiment.json').read_bytes()) or report['sourceReportSha256'] != manifest['sourceReportSha256']:
        raise ValueError('Expected verified completed archived symbolic analysis')
    jobs = {j['inputSha256']:j for j in state['jobs'].values() if j['kind']=='symbolic' and j['status']=='complete'}
    rows = []
    for row in manifest['rows']:
        digest = lab.sha(lab.encode(row))
        job = jobs.get(digest)
        if not job:
            raise ValueError('No verified archived symbolic job')
        input_path, result_path = [lab.safe(source,job[k]) for k in ['input','result']]
        if lab.sha(input_path.read_bytes()) != digest or lab.read(input_path) != row or lab.sha(result_path.read_bytes()) != job['resultSha256']:
            raise ValueError('Archived symbolic artifact changed')
        envelope = lab.read(result_path)
        if envelope['requestSha256'] != digest or envelope['result']['traceSha256'] != row['traceSha256'] or envelope['result']['id'] != row['id']:
            raise ValueError('Wrong archived result identity')
        rows.append(dict(row,provenance='verified-archived-scheduled-trace'))
    if len(rows) != 18:
        raise ValueError('This review is bounded to the existing eighteen musical traces')
    rows += controls()
    for row in rows:
        diagnose(row)
    directory = Path(root).resolve()/(lab.stamp()+'-'+uuid.uuid4().hex)
    directory.mkdir(parents=True)
    raw = lab.encode(dict(version=VERSION,sources=sources(),rows=rows,
        sourceManifestSha256=lab.sha((source/'experiment.json').read_bytes()),sourceReportSha256=lab.sha((source/'report.json').read_bytes()),
        archivedSources=manifest['sources'],skippedWaveformControls=manifest['skippedControls']))
    lab.atomic(directory/'experiment.json',raw,exclusive=True)
    lab.atomic(directory/'state.json',lab.encode(dict(manifestSha256=lab.sha(raw),status='created',jobs={},renderer=None,judgeIdentity=None)),exclusive=True)
    return directory


class Engine(lab.Engine):
    def __init__(self,directory,log):
        self.directory = Path(directory).resolve()
        self.manifest,self.state = [lab.read(self.directory/p) for p in ['experiment.json','state.json']]
        if self.manifest['version'] != VERSION or self.manifest['sources'] != sources() or self.state['manifestSha256'] != lab.sha((self.directory/'experiment.json').read_bytes()):
            raise ValueError('Variation review identity changed')
        self.log,self.retry,self.fault_hook = log,set(),lambda *_:None
    def worker(self,command,input_path,output_path,log_path):
        if command != 'variation-review':raise ValueError('Unexpected review job')
        row = lab.read(input_path)
        lab.atomic(log_path,b'Read-only note/context diagnostics; no waveform, model or threshold change.\n',exclusive=True)
        lab.atomic(output_path,lab.encode(dict(requestSha256=lab.sha(input_path.read_bytes()),result=diagnose(row))),exclusive=True)
    def drive(self):
        self.state['status']='running';self.save()
        rows=[self.execute('variation-review',row) for row in self.manifest['rows']]
        report=dict(version=VERSION,sources=self.manifest['sources'],sourceReportSha256=self.manifest['sourceReportSha256'],
            rows=rows,humanRatings=0,thresholdChanged=False,promotionAllowed=False,skippedWaveformControls=self.manifest['skippedWaveformControls'])
        lab.atomic(self.directory/'report.json',lab.encode(report));self.state['status']='complete';self.save();return report


def run(directory,fault_hook=None):
    with lab.RunLock(directory):
        log=lab.Invocation(directory)
        try:
            engine=Engine(directory,log)
            if fault_hook:engine.fault_hook=fault_hook
            result=engine.drive();log.event('complete',reportSha256=lab.sha((Path(directory)/'report.json').read_bytes()));return result
        except BaseException as e:
            log.event('failed',exception=type(e).__name__);raise
        finally:log.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['start','resume']);parser.add_argument('experiment',nargs='?',type=Path)
    parser.add_argument('--source',type=Path);parser.add_argument('--root',type=Path,default=ROOT/'.score-lab/variation-review')
    args=parser.parse_args()
    if args.command=='start' and not args.source or args.command=='resume' and not args.experiment:parser.error('Start needs --source; resume needs experiment')
    directory=create(args.root,args.source) if args.command=='start' else args.experiment.resolve()
    print('Experiment:',directory,flush=True);result=run(directory);print('Complete:',len(result['rows']),'note streams')


if __name__=='__main__':main()
