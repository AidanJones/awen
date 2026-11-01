"""Small notation-only contrast experiment; expectations are authored, not listener labels."""
import argparse
from pathlib import Path
import uuid

import score_lab as lab
import symbolic_critic as critic

ROOT = lab.ROOT
VERSION = 'awen-symbolic-contrasts-1'
FILES = ['tools/calibrate_symbolic.py', 'research/symbolic-contrasts.json']


def identities():
    return {name: lab.sha((ROOT / name).read_bytes()) for name in FILES}


def create(root):
    suite = lab.read(ROOT / FILES[1])
    rows = []
    for case in suite['cases']:
        events = [dict(step=s, midi=m, layer=layer, duration=d) for s, m, layer, d in case['notes']]
        row = dict(id=case['id'], events=events, steps=case.get('steps', 32),
                   chords=[case['chord']] * case.get('steps', 32) if case.get('chord') else None,
                   style=case.get('style', 'lyric'), profile=case.get('profile', 'neutral'),
                   traceSha256=lab.sha(lab.encode(events)), originalGate=None)
        critic.evaluate(events, row['steps'], row['chords'], row['style'], row['profile'])
        rows.append(row)
    if len({r['id'] for r in rows}) != len(rows):
        raise ValueError('Duplicate fixture IDs')
    directory = Path(root).resolve() / (lab.stamp() + '-' + uuid.uuid4().hex)
    directory.mkdir(parents=True)
    manifest = dict(version=critic.VERSION, sources=critic.sources(), calibrationSources=identities(),
                    calibrationVersion=VERSION, rows=rows, comparisons=suite['comparisons'],
                    sourceReportSha256=None, skippedControls=0, controlReason='Notation-only controls',
                    profileInterpretation='Authored theory expectations, not preference or text-classifier truth')
    raw = lab.encode(manifest)
    lab.atomic(directory / 'experiment.json', raw, exclusive=True)
    lab.atomic(directory / 'state.json', lab.encode(dict(manifestSha256=lab.sha(raw), jobs={},
               status='created', renderer=None, judgeIdentity=None)), exclusive=True)
    return directory


def compare(report, comparisons):
    rows = {r['id']: r for r in report['rows']}
    def value(ref):
        row, group, field = ref.split('/')
        return rows[row][group][field]
    results = []
    for check in comparisons:
        left = value(check['left'])
        right = value(check['right']) if 'right' in check else check.get('value')
        op = check['op']
        if op not in ('eq', 'gt', 'null'):
            raise ValueError('Unknown contrast operator')
        passed = left is None if op == 'null' else (left == right if op == 'eq' else
                 left is not None and right is not None and left > right)
        results.append(dict(**check, observedLeft=left, observedRight=right, passed=passed))
    return dict(version=VERSION, status='engineering-contrasts-only', humanRatings=0,
                promotionAllowed=False, checks=results, passed=sum(r['passed'] for r in results),
                total=len(results), limitations=[
                    'Expected relations authored alongside rules; not independent musical validation.',
                    'No waveform, timbre, perceived annoyance, chapter-state or listener assessment.',
                    'Passing contrasts does not calibrate thresholds against human preferences.'])


def run(directory, fault_hook=None):
    directory = Path(directory).resolve()
    with lab.RunLock(directory):
        manifest = lab.read(directory / 'experiment.json')
        if manifest.get('calibrationVersion') != VERSION or manifest.get('calibrationSources') != identities():
            raise ValueError('Calibration sources changed; start a new experiment')
        log = lab.Invocation(directory)
        try:
            engine = critic.Engine(directory, log)
            if fault_hook:
                engine.fault_hook = fault_hook
            report = engine.drive()
            result = compare(report, manifest['comparisons'])
            result.update(sources=manifest['sources'], calibrationSources=manifest['calibrationSources'],
                          manifestSha256=lab.sha((directory / 'experiment.json').read_bytes()),
                          reportSha256=lab.sha((directory / 'report.json').read_bytes()))
            lab.atomic(directory / 'contrasts.json', lab.encode(result))
            log.event('contrasts-complete', passed=result['passed'], total=result['total'])
            return result
        except BaseException as error:
            log.event('failed', exception=type(error).__name__)
            raise
        finally:
            log.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['start', 'resume'])
    parser.add_argument('experiment', nargs='?', type=Path)
    parser.add_argument('--root', type=Path, default=ROOT / '.score-lab/symbolic-contrasts')
    args = parser.parse_args()
    if args.command == 'resume' and not args.experiment:
        parser.error('Resume requires an experiment directory')
    directory = create(args.root) if args.command == 'start' else args.experiment
    print('Experiment:', directory, flush=True)
    result = run(directory)
    print(f"Contrasts: {result['passed']}/{result['total']}")
    if result['passed'] != result['total']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
