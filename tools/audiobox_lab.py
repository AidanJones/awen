"""Small resumable Audiobox diagnostic on verified existing WAVs; no automatic adoption."""
import argparse
import importlib.metadata
from pathlib import Path
import uuid

import score_lab as lab
from audiobox_backend import AudioboxBackend, PACKAGES, weighted_axes

ROOT = lab.ROOT
VERSION = 'awen-audiobox-probe-1'
FILES = ['tools/audiobox_lab.py', 'tools/audiobox_backend.py', 'tools/prepare_audiobox.py',
         'tools/score_lab.py', 'research/audiobox-model.json']


def sources():
    return {p: lab.sha((ROOT / p).read_bytes()) for p in FILES}


def identity(spec):
    packages = {p: importlib.metadata.version(p) for p in PACKAGES}
    if packages != spec['packages']:
        raise ValueError('Pinned model environment changed')
    return dict(spec=spec, packages=packages, backendSha256=lab.sha((ROOT / 'tools/audiobox_backend.py').read_bytes()),
                strictStateLoad=True, missingKeys=[], unexpectedKeys=[])


def import_rows(source):
    source = Path(source).resolve()
    report, manifest, state = [lab.read(source / p) for p in ['report.json', 'experiment.json', 'state.json']]
    if report['version'] != 'awen-multiobjective-prototype-1' or state['status'] != 'complete' or state['manifestSha256'] != lab.sha((source / 'experiment.json').read_bytes()) or report['sources'] != manifest['sources']:
        raise ValueError('Expected completed, internally consistent prototype')
    jobs = {lab.safe(source, j['result']): j for j in state['jobs'].values() if j['kind'] == 'render' and j['status'] == 'complete'}
    rows = []
    for group in report['scenes']:
        for row in group['initial'][:1]+group['controls']+group['initial'][1:]+group['children']:
            file = lab.safe(source, row['file'])
            if lab.sha(file.read_bytes()) != row['sha256']:
                raise ValueError('Source WAV checksum changed')
            if not row.get('control'):
                result_path = file.parent / 'result.json'
                job = jobs.get(result_path)
                if not job or lab.sha(result_path.read_bytes()) != job['resultSha256']:
                    raise ValueError('Unverified source render')
                input_path = lab.safe(source, job['input'])
                original = lab.read(input_path)
                if lab.sha(input_path.read_bytes()) != job['inputSha256'] or original['card'] != row['card'] or original['scene'] != group['scene']['index']:
                    raise ValueError('Wrong source card/scene lineage')
                envelope = lab.read(result_path)
                if envelope['requestSha256'] != job['inputSha256'] or envelope['result']['sha256'] != row['sha256']:
                    raise ValueError('Wrong source render identity')
            rows.append(dict(id=group['scene']['id']+'/'+row['card']['id'], scene=group['scene']['id'],
                             file=str(file), sha256=row['sha256'], control=row.get('control'),
                             originalGate=row['gate'], originalObjectives=row['objectives']))
    if len(rows) != 27 or len({r['id'] for r in rows}) != 27:
        raise ValueError('Expected frozen 18 musical clips and nine controls')
    return rows


def create(root, source, model_root):
    rows = import_rows(source)
    spec = lab.read(ROOT / 'research/audiobox-model.json')
    directory = Path(root).resolve() / (lab.stamp()+'-'+uuid.uuid4().hex)
    directory.mkdir(parents=True)
    raw = lab.encode(dict(version=VERSION, sources=sources(), rows=rows, identity=identity(spec),
                          modelRoot=str(Path(model_root).resolve()), sourceReportSha256=lab.sha((Path(source)/'report.json').read_bytes())))
    lab.atomic(directory/'experiment.json', raw, exclusive=True)
    lab.atomic(directory/'state.json', lab.encode(dict(manifestSha256=lab.sha(raw), status='created', jobs={}, renderer=None, judgeIdentity=None)), exclusive=True)
    return directory


class Engine(lab.Engine):
    def __init__(self, directory, log, max_new=None, factory=AudioboxBackend):
        self.directory = Path(directory).resolve()
        self.manifest, self.state = [lab.read(self.directory/p) for p in ['experiment.json', 'state.json']]
        if self.manifest['version'] != VERSION or self.manifest['sources'] != sources() or self.state['manifestSha256'] != lab.sha((self.directory/'experiment.json').read_bytes()):
            raise ValueError('Probe source/manifest changed')
        if self.manifest['identity'] != identity(self.manifest['identity']['spec']):
            raise ValueError('Evaluator identity changed')
        self.log, self.retry, self.fault_hook = log, set(), lambda *_: None
        self.backend, self.factory, self.max_new, self.new = None, factory, max_new, 0

    def verify(self, job, path):
        result = super().verify(job, path)
        payload = lab.read(lab.safe(self.directory, job['input']))
        if lab.sha(Path(payload['file']).read_bytes()) != payload['sha256'] or result['audioSha256'] != payload['sha256'] or result['identitySha256'] != lab.sha(lab.encode(self.manifest['identity'])):
            raise ValueError('Cached audio/model identity changed')
        axes = weighted_axes(result['windows'], self.manifest['identity']['spec']['axes'])
        if axes != result['axes']:
            raise ValueError('Aggregated scores disagree with saved windows')
        return result

    def execute(self, kind, payload):
        key, job = self.ensure_job(kind, payload)
        published = bool(job['attempts'] and job['status'] in ('running','uncertain','invalid-response') and
                         (lab.safe(self.directory, job['attempts'][-1]['directory'])/'result.json').exists())
        if job['status'] != 'complete' and not published and self.max_new is not None and self.new >= self.max_new:
            raise lab.Paused('Score chunk complete; resume to continue')
        return super().execute(kind, payload)

    def worker(self, command, input_path, output_path, log_path):
        if command != 'audiobox-score':
            raise ValueError('Unexpected evaluator job')
        payload = lab.read(input_path)
        if lab.sha(Path(payload['file']).read_bytes()) != payload['sha256']:
            raise ValueError('Input WAV changed')
        loaded = self.backend is None
        if loaded:
            self.backend = self.factory(self.manifest['identity']['spec'], self.manifest['modelRoot'])
        if self.backend.identity != self.manifest['identity']:
            raise ValueError('Loaded evaluator identity mismatch')
        pcm, rate = self.backend.read_pcm(payload['file'])
        equivalence = self.backend.official_equivalence(pcm[:, :rate*10], rate) if loaded else None
        result = self.backend.score_pcm(pcm, rate)
        result.update(audioSha256=payload['sha256'], identitySha256=lab.sha(lab.encode(self.backend.identity)),
                      modelLoadSeconds=self.backend.load_seconds if loaded else 0, officialEquivalence=equivalence)
        lab.atomic(log_path, lab.encode(dict(id=payload['id'], inferenceSeconds=result['inferenceSeconds'], modelLoaded=loaded)), exclusive=True)
        lab.atomic(output_path, lab.encode(dict(requestSha256=lab.sha(input_path.read_bytes()), result=result)), exclusive=True)
        self.new += 1

    def drive(self):
        self.state['status'] = 'running'
        self.save()
        rows, paused = [], False
        for row in self.manifest['rows']:
            try:
                result = self.execute('audiobox-score', row)
            except lab.Paused:
                paused = True
                break
            rows.append(dict(**row, result=result, selectable=False))
        report = dict(version=VERSION, sources=self.manifest['sources'], identity=self.manifest['identity'],
                      sourceReportSha256=self.manifest['sourceReportSha256'], status='paused' if paused else 'complete',
                      rows=rows, humanRatings=0, promotionAllowed=False,
                      warning='Raw aesthetics predictions, not scene fit, personal taste or reading comfort. Original synthetic-head outputs remain TEST ONLY.')
        lab.atomic(self.directory/'report.json', lab.encode(report))
        self.state['status'] = report['status']
        self.save()
        return report


def run(directory, max_new=None, factory=AudioboxBackend, fault_hook=None):
    with lab.RunLock(directory):
        log = lab.Invocation(directory)
        try:
            engine = Engine(directory, log, max_new, factory)
            if fault_hook:
                engine.fault_hook = fault_hook
            result = engine.drive()
            log.event(result['status'], newScores=engine.new, reportSha256=lab.sha((Path(directory)/'report.json').read_bytes()))
            return result
        except BaseException as error:
            log.event('failed', exception=type(error).__name__)
            raise
        finally:
            log.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['start','resume'])
    parser.add_argument('experiment', nargs='?', type=Path)
    parser.add_argument('--source', type=Path)
    parser.add_argument('--root', type=Path, default=ROOT/'.score-lab/audiobox-probe')
    parser.add_argument('--model-root', type=Path, default=ROOT/'.score-lab/audiobox-preflight')
    parser.add_argument('--max-new-scores', type=int)
    args = parser.parse_args()
    if args.command == 'start' and not args.source or args.command == 'resume' and not args.experiment or args.max_new_scores is not None and args.max_new_scores < 0:
        parser.error('Start needs --source; resume needs experiment; score budget must be nonnegative')
    directory = create(args.root, args.source, args.model_root) if args.command == 'start' else args.experiment.resolve()
    print('Experiment:', directory, flush=True)
    result = run(directory, args.max_new_scores)
    print(result['status'], len(result['rows']), 'scored clips')


if __name__ == '__main__':
    main()
