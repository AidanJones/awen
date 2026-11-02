"""Analyse declared DSL parts with explicit per-step chapter/harmony context."""
import argparse
from pathlib import Path
import uuid

import score_lab as lab
import symbolic_critic as critic

VERSION = 'awen-symbolic-score-1'
EXTRA_SOURCES = ['tools/symbolic_score.py']


def identities():
    return {name: lab.sha((lab.ROOT / name).read_bytes()) for name in EXTRA_SOURCES}


def evaluate_score(score, profile='neutral'):
    if score.get('version') != VERSION:
        raise ValueError('Unsupported score representation')
    expected = {name: lab.sha((lab.ROOT / name).read_bytes()) for name in
                ['index.html', 'tools/score-lab.cjs', 'tools/symbolic-score.cjs']}
    if score.get('sources') != expected:
        raise ValueError('Exporter/runtime source identity changed; export a new score')
    coverage = score.get('coverage', {})
    if coverage != dict(plannedNotes=True, scheduledNotes=False, voiceIdentity='explicit-dsl-part',
                        physicalOscillatorIdentity=False, bed='harmonic-target-only', acousticEnvelope=False, waveformRead=False):
        raise ValueError('Unsupported coverage claims')
    steps, start = score['steps'], score['startStep']
    if type(steps) is not int or not 1 <= steps <= 4096 or type(start) is not int or not 0 <= start <= 100000000:
        raise ValueError('Invalid score bounds')
    voices = [v['id'] for v in score['voices']]
    if not voices or len(voices) > 16 or len(set(voices)) != len(voices) or any(not isinstance(v, str) or len(v) > 80 for v in voices):
        raise ValueError('Invalid declared voices')
    contexts = score['contexts']
    if len(contexts) != steps or len(score['chords']) != steps:
        raise ValueError('Missing per-step context')
    for n, c in enumerate(contexts):
        if c['step'] != n or c['absoluteStep'] != start+n or c['chord'] != score['chords'][n] or c['style'] not in ('lyric', 'figured'):
            raise ValueError('Inconsistent harmonic/clock context')
        if type(c['epoch']) is not int or not 0 <= c['epoch'] <= start+n or c['epoch'] % 32 or c['transpose'] not in (0, 5, 7):
            raise ValueError('Invalid chapter epoch or tonal region')
    for e in score['events']:
        if e.get('voice') not in voices or type(e.get('step')) is not int or e.get('absoluteStep') != start+e['step']:
            raise ValueError('Missing or inconsistent authored voice/clock identity')
    # Validate all note bounds and harmonic context before indexing or partitioning.
    critic.evaluate(score['events'], steps, score['chords'], profile=profile, start_step=start)
    segments = []
    def identity(c):
        return c['activeChapter'], c['preset'], c['epoch'], c['transpose'], c['style']
    bounds = [0] + [n for n in range(1, steps) if identity(contexts[n]) != identity(contexts[n-1])] + [steps]
    for begin, end in zip(bounds, bounds[1:]):
        c = contexts[begin]
        parts = []
        for voice in voices:
            # Declare one authored part as the analysis line, never infer it from layer/pitch.
            events = [dict(e, step=e['step']-begin, layer=2) for e in score['events']
                      if e['voice'] == voice and begin <= e['step'] < end]
            result = critic.evaluate(events, end-begin, score['chords'][begin:end], c['style'], profile, start+begin)
            parts.append(dict(voice=voice, notes=len(events), metrics=result['metrics'],
                              advisoryScores=result['advisoryScores'], monophonic=result['coverage']['monophonicMelody']))
        segments.append(dict(startStep=start+begin, endStep=start+end, chapter=c['activeChapter'],
                             preset=c['preset'], epoch=c['epoch'], transpose=c['transpose'], style=c['style'], parts=parts))
    return dict(version=VERSION, id=score.get('id'), ruleBased=True, promotionAllowed=False,
                humanPreferenceValidated=False, coverage=score['coverage'], segments=segments,
                warnings=['Authored parts are not independent contrapuntal voices; no fifths/parallel-motion penalty.',
                          'Activity here describes each part; it is not whole-score activity or reading comfort.',
                          'Bar pattern metrics use local segment bars; partial bars are not global phrase claims.'] + score['limitations'])


def create(root, input_path, profile='neutral'):
    input_path = Path(input_path)
    scores = lab.read(input_path)
    if not isinstance(scores, list) or len(scores) > 100:
        raise ValueError('Bounded exported score batch required')
    for score in scores:
        evaluate_score(score, profile)
    directory = Path(root).resolve() / (lab.stamp() + '-' + uuid.uuid4().hex)
    directory.mkdir(parents=True)
    manifest = dict(version=critic.VERSION, sources=critic.sources(), contextSources=identities(),
                    inputSha256=lab.sha(input_path.read_bytes()), scores=scores, profile=profile)
    raw = lab.encode(manifest)
    lab.atomic(directory / 'experiment.json', raw, exclusive=True)
    lab.atomic(directory / 'state.json', lab.encode(dict(manifestSha256=lab.sha(raw), jobs={},
               status='created', renderer=None, judgeIdentity=None)), exclusive=True)
    return directory


class Engine(critic.Engine):
    def __init__(self, directory, log):
        super().__init__(directory, log)
        if self.manifest['contextSources'] != identities():
            raise ValueError('Context evaluator source changed')

    def worker(self, command, input_path, output_path, log_path):
        if command != 'score-context':
            raise ValueError('Unexpected context job')
        row = lab.read(input_path)
        result = evaluate_score(row['score'], row['profile'])
        lab.atomic(log_path, b'Declared parts and harmonic targets only; no waveform access.\n', exclusive=True)
        lab.atomic(output_path, lab.encode(dict(requestSha256=lab.sha(input_path.read_bytes()), result=result)), exclusive=True)

    def drive(self):
        self.state['status'] = 'running'
        self.save()
        rows = [self.execute('score-context', dict(score=s, profile=self.manifest['profile'])) for s in self.manifest['scores']]
        report = dict(version=VERSION, promotionAllowed=False, humanRatings=0, sources=self.manifest['sources'],
                      contextSources=self.manifest['contextSources'], inputSha256=self.manifest['inputSha256'], rows=rows)
        lab.atomic(self.directory / 'report.json', lab.encode(report))
        self.state['status'] = 'complete'
        self.save()
        return report


def run(directory, fault_hook=None):
    with lab.RunLock(directory):
        log = lab.Invocation(directory)
        try:
            engine = Engine(directory, log)
            if fault_hook:
                engine.fault_hook = fault_hook
            report = engine.drive()
            log.event('complete', reportSha256=lab.sha((Path(directory) / 'report.json').read_bytes()))
            return report
        except BaseException as error:
            log.event('failed', exception=type(error).__name__)
            raise
        finally:
            log.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['start', 'resume'])
    parser.add_argument('experiment', nargs='?', type=Path)
    parser.add_argument('--input', type=Path)
    parser.add_argument('--root', type=Path, default=lab.ROOT / '.score-lab/symbolic-score')
    parser.add_argument('--profile', choices=critic.PROFILES, default='neutral')
    args = parser.parse_args()
    if args.command == 'start' and not args.input or args.command == 'resume' and not args.experiment:
        parser.error('Start requires --input; resume requires an experiment directory')
    directory = create(args.root, args.input, args.profile) if args.command == 'start' else args.experiment.resolve()
    print('Experiment:', directory, flush=True)
    run(directory)
    print('Complete:', directory / 'report.json')


if __name__ == '__main__':
    main()
