"""Bounded, resumable CLAP exploration of the exact browser grid; never deploys a winner."""
import argparse
import html
import json
from pathlib import Path
import shutil
import subprocess
import sys
import uuid
import wave

import score_lab as lab
import score_embeddings as emb
from clap_backend import ClapBackend
from exploration_page import build

VERSION = 'awen-grid-clap-1'
ROOT = lab.ROOT
SOURCES = ['index.html', 'tools/grid_clap.py', 'tools/grid-clap-worker.cjs',
           'tools/exploration_page.py', 'tools/exploration-review.html',
           'tools/score_lab.py', 'tools/score_embeddings.py', 'tools/clap_backend.py',
           'tools/score-lab-metrics.cjs', 'research/grid-clap-suite.json',
           'research/calibration-scenes.json', 'research/scoring-knowledge.json']


def sources():
    return {p: lab.sha((ROOT / p).read_bytes()) for p in SOURCES}


def create(root):
    directory = Path(root).resolve() / (lab.stamp()+'-'+uuid.uuid4().hex)
    directory.mkdir(parents=True)
    page = build(directory / 'public')
    spec = lab.read(ROOT / 'research/clap-probe-model.json')
    identity = emb.model_identity(spec)
    manifest = dict(version=VERSION, id=uuid.uuid4().hex, createdAt=lab.now(), sources=sources(),
                    suite=lab.read(ROOT / 'research/grid-clap-suite.json'), identity=identity,
                    identitySha256=lab.sha(lab.encode(identity)), pageSha256=lab.sha(page.read_bytes()),
                    cache=str(ROOT / '.score-lab/embedding-cache'), modelCache=str(ROOT / '.score-lab/huggingface'))
    raw = lab.encode(manifest)
    lab.atomic(directory / 'experiment.json', raw, exclusive=True)
    lab.atomic(directory / 'state.json', lab.encode(dict(version=VERSION, manifestSha256=lab.sha(raw),
        status='created', jobs={}, renderer=None, judgeIdentity=None, judgeCallsStarted=0,
        computedFeatures=0, featureCacheHits=0)))
    return directory


def objective(rows, keys=('target-1', 'target-2')):
    return sum(row[k] for row in rows for k in keys)/(len(rows)*len(keys))


class GridEngine(emb.EmbeddingEngine):
    def __init__(self, directory, log, max_renders=None, max_features=None):
        self.directory = Path(directory).resolve()
        self.manifest, self.state = lab.read(self.directory/'experiment.json'), lab.read(self.directory/'state.json')
        m = self.manifest
        if m['version'] != VERSION or self.state['manifestSha256'] != lab.sha((self.directory/'experiment.json').read_bytes()):
            raise ValueError('Experiment identity changed')
        if m['sources'] != sources() or m['identity'] != emb.model_identity(m['identity']['spec']):
            raise ValueError('Sources/packages changed; start a new experiment')
        self.page = self.directory/'public/explore.html'
        if lab.sha(self.page.read_bytes()) != m['pageSha256'] or m['identitySha256'] != lab.sha(lab.encode(m['identity'])):
            raise ValueError('Page/model identity changed')
        self.node = shutil.which('node')
        if not self.node:
            raise RuntimeError('Node required for isolated production rendering')
        self.log, self.retry, self.backend = log, set(), None
        self.max_new_renders, self.new_renders = max_renders, 0
        self.max_new, self.new_features = max_features, 0
        self.download, self.factory = False, ClapBackend
        self.fault_hook = lambda *_: None

    def verify(self, job, path):
        return super().verify(job, path) if job['kind'].startswith('embedding-') else lab.Engine.verify(self, job, path)

    def execute(self, kind, payload):
        return super().execute(kind, payload) if kind.startswith('embedding-') else lab.Engine.execute(self, kind, payload)

    def worker(self, command, input_path, output_path, log_path):
        if command.startswith('embedding-'):
            return super().worker(command, input_path, output_path, log_path)
        with Path(log_path).open('xb') as stream:
            result = subprocess.run([self.node, str(ROOT/'tools/grid-clap-worker.cjs'), command,
                                     str(input_path), str(output_path)], stdout=stream, stderr=subprocess.STDOUT)
        if result.returncode:
            raise RuntimeError(f'{command} failed; see {log_path}')

    def text(self, text):
        item = dict(kind='text', text=text, textSha256=lab.sha(text.encode()))
        item['cacheKey'] = emb.feature_key(self.manifest['identity'], item)
        return self.execute('embedding-text', item)['vector']

    def audio(self, file, start=0, silence=False):
        with wave.open(str(file), 'rb') as handle:
            if (handle.getnchannels(), handle.getsampwidth(), handle.getframerate()) != (1, 2, 24000):
                raise ValueError('Expected mono PCM16 24 kHz audio')
            handle.setpos(round(start*24000))
            pcm = handle.readframes(240000)
        if len(pcm) != 480000:
            raise ValueError('Audio window too short')
        if silence:
            pcm = bytes(len(pcm))
        item = dict(kind='audio', file=str(file.relative_to(self.directory)), wavSha256=lab.sha(file.read_bytes()),
                    startFrame=round(start*24000), frameCount=240000, silence=silence, pcmSha256=lab.sha(pcm))
        item['cacheKey'] = emb.feature_key(self.manifest['identity'], item)
        return self.execute('embedding-audio', item)['vector']

    def evaluate(self, card, seed, captions):
        s = self.manifest['suite']
        payload = dict(page=str(self.page), card=card, seed=seed, scene=s['sceneIndex'], seconds=s['seconds'])
        render = self.execute('render', payload)
        _, job = self.ensure_job('render', payload)
        file = lab.safe(self.directory, job['result']).parent / render['file']
        vectors = [self.audio(file, start) for start in s['windows']]
        scores = [{k: emb.cosine(vector, v) for k, v in captions.items()} for vector in vectors]
        row = dict(card=card, seed=seed, file=str(file.relative_to(self.directory)), sha256=render['sha256'],
                    gate=render['gate'], signal=render['signal'], structure=render['structure'],
                    scores=scores, objective=objective(scores), gain=render['gain'])
        self.log.event('candidate_scored', candidate=card['id'], seed=seed, objective=row['objective'], eligible=row['gate']['eligible'])
        print(card['id'], seed, round(row['objective'], 5), 'eligible' if row['gate']['eligible'] else render['gate']['reasons'], flush=True)
        return row

    def drive(self):
        self.state['status'] = 'running'
        self.save()
        m, s = self.manifest, self.manifest['suite']
        plan = self.execute('grid-plan', dict(page=str(self.page)))
        controls = [self.text(t) for t in m['identity']['spec']['textTowerSanity']['texts']]
        health = emb.text_tower_sanity(controls, m['identity']['spec']['textTowerSanity']['rejectIfMinimumPairwiseCosineAbove'])
        if not health['usable']:
            raise ValueError('Text tower failed sanity check')
        targets = {k: self.text(s['captions'][k]) for k in ('target-1', 'target-2')}
        pool = [self.evaluate(card, s['searchSeed'], targets) for card in plan['cards']]
        initial = list(pool)
        rounds = []
        rank = lambda rows: sorted((r for r in rows if r['gate']['eligible']), key=lambda r: (-r['objective'], r['card']['id']))
        if not rank(pool):
            raise ValueError('No grid candidates passed native gates')
        for generation in range(1, s['generations']+1):
            parents = [r['card'] for r in rank(pool)[:s['parents']]]
            children = self.execute('grid-children', dict(page=str(self.page), parents=parents,
                generation=generation, seed=s['searchSeed'], count=s['childrenPerGeneration']))
            rows = [self.evaluate(c, s['searchSeed'], targets) for c in children]
            pool.extend(rows)
            rounds.append(dict(generation=generation, parents=[p['id'] for p in parents],
                               children=rows, bestId=rank(pool)[0]['card']['id'], bestObjective=rank(pool)[0]['objective']))
            lab.atomic(self.directory/f'round-{generation}.json', lab.encode(rounds[-1]), exclusive=True)
            self.log.event('generation_complete', generation=generation, bestObjective=rank(pool)[0]['objective'])
        winner, grid_best, warm = rank(pool)[0], rank(initial)[0], next(r for r in initial if r['card']['id']=='warm')
        # No check descriptions or check-seed scores enter selection above.
        checks = {k: self.text(v) for k, v in s['captions'].items()}
        finalists = list({r['card']['id']: r['card'] for r in (warm, grid_best, winner)}.values())
        validation = [self.evaluate(c, seed, checks) for seed in (s['searchSeed'], s['checkSeed']) for c in finalists]
        silence_vector = self.audio(self.directory/winner['file'], silence=True)
        silence = {k: emb.cosine(silence_vector, v) for k, v in checks.items()}
        # Probe a pure level change with no compositional difference; it cannot become a search candidate.
        quiet = self.directory/'controls/half-level.wav'
        with wave.open(str(self.directory/winner['file']), 'rb') as handle:
            params, pcm = handle.getparams(), handle.readframes(handle.getnframes())
        import array
        values = array.array('h'); values.frombytes(pcm)
        if sys.byteorder != 'little': values.byteswap()
        values = array.array('h', (int(v*.5) for v in values))
        if sys.byteorder != 'little': values.byteswap()
        import io
        out = io.BytesIO()
        with wave.open(out, 'wb') as handle:
            handle.setparams(params); handle.writeframes(values.tobytes())
        lab.atomic(quiet, out.getvalue(), exclusive=True)
        quiet_vectors = [self.audio(quiet, start) for start in s['windows']]
        quiet_scores = [{k: emb.cosine(vector, v) for k, v in checks.items()} for vector in quiet_vectors]
        report = dict(version=VERSION, status='exploratory-search-only', experimentId=m['id'],
            suite=s, model=m['identity'], composer=plan['composer'], engineSha256=plan['engineSha256'],
            textTowerSanity=health, initial=initial, rounds=rounds, winner=winner,
            gridBest=grid_best, warm=warm, validation=validation, silenceScores=silence,
            halfLevelScores=quiet_scores, deploymentApproved=False, listenerPreferenceEstablished=False)
        lab.atomic(self.directory/'report.json', lab.encode(report), exclusive=True)
        self.listening(report, plan['scenes'][s['sceneIndex']])
        self.state['status'] = 'exploratory-search-only'
        self.save()

    def listening(self, report, scene):
        public = self.directory/'public'
        rows = []
        for i, (label, row) in enumerate([('Familiar warm ensemble', report['warm']), ('Highest-ranked original grid card', report['gridBest']), ('Highest-ranked after evolution', report['winner'])]):
            file = f'comparison-{i}.wav'
            lab.atomic(public/file, (self.directory/row['file']).read_bytes(), exclusive=True)
            card = row['card']
            profile = dict(version=1, genomeVersion='awen-genome-1', genome=card['genome'], history=[], pins=[], pinNames={})
            lab.atomic(public/f'profile-{i}.json', lab.encode(profile), exclusive=True)
            rows.append(f'<section><h2>{html.escape(label)}</h2><p>{html.escape(card["name"])} · palette: {html.escape(card["palette"])}</p><audio controls preload="none" src="{file}"></audio><p><a href="profile-{i}.json" download>Reader profile</a> · Select its palette separately.</p></section>')
        page = '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Awen CLAP experiment</title><style>body{color-scheme:light dark;font:17px/1.6 system-ui;max-width:980px;margin:auto;padding:24px;background:#202820;color:#eeeade}section{border:1px solid #9aa78d;border-radius:10px;padding:16px;margin:16px 0}audio{width:100%}a{color:#c8dcb5}button{font:inherit;padding:10px}</style><h1>CLAP-guided grid experiment</h1><p>A bounded development search, not a validated music judge. Compare while reading; numerical ranking does not establish a better accompaniment.</p><p>'+html.escape(scene['text'])+'</p><button onclick="document.querySelectorAll(\'audio\').forEach(a=>a.pause())">Stop all</button>'+''.join(rows)+'<p>Original grid and defaults unchanged. No listener ratings fabricated.</p><script>document.querySelectorAll("audio").forEach(a=>{a.volume=.7;a.addEventListener("play",()=>document.querySelectorAll("audio").forEach(b=>{if(a!==b)b.pause()}));});document.addEventListener("keydown",e=>{if(e.key==="Escape")document.querySelectorAll("audio").forEach(a=>a.pause())});</script></html>'
        lab.atomic(public/'comparison.html', page.encode(), exclusive=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('start', 'resume', 'status'))
    parser.add_argument('experiment', nargs='?', type=Path)
    parser.add_argument('--root', type=Path, default=ROOT/'.score-lab/grid-clap')
    parser.add_argument('--max-new-renders', type=int)
    parser.add_argument('--max-new-features', type=int)
    args = parser.parse_args()
    for limit in (args.max_new_renders, args.max_new_features):
        if limit is not None and limit < 0: parser.error('Budgets must be nonnegative')
    if args.command != 'start' and not args.experiment: parser.error('Experiment directory required')
    directory = create(args.root) if args.command=='start' else args.experiment.resolve()
    print('Experiment:', directory, flush=True)
    if args.command=='status':
        state = lab.read(directory/'state.json')
        print(json.dumps({k: state[k] for k in ('status', 'computedFeatures', 'featureCacheHits')}, indent=2)); return
    with lab.RunLock(directory):
        log = lab.Invocation(directory); engine = None
        try:
            engine = GridEngine(directory, log, args.max_new_renders, args.max_new_features)
            engine.drive(); print('Complete:', directory/'public/comparison.html', flush=True)
        except lab.Paused as error:
            engine.state['status']='paused'; engine.save(); log.event('paused', reason=str(error)); print(error, flush=True)
        except Exception as error:
            if engine: engine.state['status']='failed'; engine.save()
            log.event('failed', exception=type(error).__name__)
            raise
        finally:
            log.close()


if __name__ == '__main__':
    main()
