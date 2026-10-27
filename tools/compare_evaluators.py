"""Resumable post-hoc CLAP objective comparison; reuses verified grid audio/features."""
import argparse
import html
import json
from pathlib import Path
import uuid

import grid_clap as grid
import score_lab as lab
import score_embeddings as emb

EXTRA_SOURCES = ['tools/compare_evaluators.py', 'research/evaluator-comparison-suite.json']


def extra_sources():
    return {p: lab.sha((grid.ROOT/p).read_bytes()) for p in EXTRA_SOURCES}


def score(rows, method):
    if method=='single-1': return grid.objective(rows, ('target-1',))
    if method=='single-2': return grid.objective(rows, ('target-2',))
    if method=='ensemble': return grid.objective(rows)
    if method=='contrastive': return grid.objective(rows)-grid.objective(rows, ('contrast',))
    raise ValueError('Unknown selection method')


def choose(rows, method):
    if method in ('incumbent', 'warm'):
        return next(r for r in rows if r['card']['id']==('pursuit' if method=='incumbent' else 'warm'))
    eligible = [r for r in rows if r['gate']['eligible']]
    if not eligible: raise ValueError('No eligible candidates')
    return min(eligible, key=lambda r: (-score(r['scores'], method), r['card']['id']))


def create(root, source):
    source = Path(source).resolve()
    raw = (source/'report.json').read_bytes()
    report = json.loads(raw)
    if report['version']!=grid.VERSION or report['status']!='exploratory-search-only':
        raise ValueError('A completed grid experiment is required')
    directory = grid.create(root)
    manifest = lab.read(directory/'experiment.json')
    if manifest['identity']!=report['model']:
        raise ValueError('Do not mix encoders or package versions')
    rows = report['initial']+[r for generation in report['rounds'] for r in generation['children']]
    assets = {}
    for row in rows:
        original = lab.safe(source, row['file'])
        if lab.sha(original.read_bytes())!=row['sha256']: raise ValueError('Source WAV changed')
        asset = 'assets/'+row['sha256']+'.wav'
        lab.atomic(directory/asset, original.read_bytes(), exclusive=True)
        row['file'] = asset
        assets[asset] = row['sha256']
    lab.atomic(directory/'source-report.json', raw, exclusive=True)
    manifest['comparison'] = dict(suite=lab.read(grid.ROOT/'research/evaluator-comparison-suite.json'),
        sources=extra_sources(), sourcePath=str(source), sourceReportSha256=lab.sha(raw), rows=rows, assets=assets)
    raw = lab.encode(manifest)
    lab.atomic(directory/'experiment.json', raw)
    state = lab.read(directory/'state.json'); state['manifestSha256']=lab.sha(raw)
    lab.atomic(directory/'state.json', lab.encode(state))
    return directory


class ComparisonEngine(grid.GridEngine):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        c = self.manifest['comparison']
        if c['sources']!=extra_sources() or lab.sha((self.directory/'source-report.json').read_bytes())!=c['sourceReportSha256']:
            raise ValueError('Comparison sources changed')
        for file, checksum in c['assets'].items():
            if lab.sha(lab.safe(self.directory, file).read_bytes())!=checksum: raise ValueError('Comparison audio changed')

    def drive(self):
        self.state['status']='running'; self.save()
        config = self.manifest['comparison']; suite = config['suite']
        plan = self.execute('grid-plan', dict(page=str(self.page)))
        source = lab.read(self.directory/'source-report.json')
        if plan['engineSha256']!=source['engineSha256']: raise ValueError('Production engine changed')
        captions = {k:self.text(source['suite']['captions'][k]) for k in ('target-1','target-2','contrast')}
        rows = []
        for old in config['rows']:
            vectors = [self.audio(self.directory/old['file'], start) for start in self.manifest['suite']['windows']]
            row = {**old, 'scores':[{k:emb.cosine(vector, text) for k,text in captions.items()} for vector in vectors]}
            rows.append(row)
        selections = {method:choose(rows,method) for method in suite['methods']}
        # Only now load the newly fixed check descriptions. They cannot affect selection.
        check = {**captions, **{k:self.text(v) for k,v in suite['checkCaptions'].items()}}
        cards = {row['card']['id']:row['card'] for row in selections.values()}
        validation = [self.evaluate(card,suite['checkSeed'],check) for card in cards.values()]
        silence_vector = self.audio(self.directory/rows[0]['file'],silence=True)
        silence = {k:emb.cosine(silence_vector,v) for k,v in check.items()}
        methods = []
        for method, row in selections.items():
            v = next(v for v in validation if v['card']['id']==row['card']['id'])
            methods.append(dict(method=method, selectedId=row['card']['id'], name=row['card']['name'],
                selectionScore=score(row['scores'],method) if method not in ('incumbent','warm') else None,
                newDescriptionMean=grid.objective(v['scores'],('new-1','new-2')),
                newDescriptionWindows=[{k:x[k] for k in ('new-1','new-2')} for x in v['scores']],
                actionSpecificity=v['objective']-grid.objective(v['scores'],('contrast',)), eligible=v['gate']['eligible']))
        ranking = {method:[r['card']['id'] for r in sorted((r for r in rows if r['gate']['eligible']),key=lambda r:(-score(r['scores'],method),r['card']['id']))] for method in ('single-1','single-2','ensemble','contrastive')}
        agreement = []
        names = list(ranking)
        for i,a in enumerate(names):
            for b in names[i+1:]:
                ids=ranking[a]; positions={key:n for n,key in enumerate(ranking[b])}
                pairs=[positions[x]<positions[y] for n,x in enumerate(ids) for y in ids[n+1:]]
                agreement.append(dict(a=a,b=b,concordantFraction=sum(pairs)/len(pairs),pairs=len(pairs)))
        report = dict(version='awen-evaluator-comparison-1', status='post-hoc-diagnostics-only',
            experimentId=self.manifest['id'], suite=suite, sourceReportSha256=config['sourceReportSha256'],
            model=self.manifest['identity'], engineSha256=plan['engineSha256'], methods=methods,
            rows=rows, validation=validation, rankingAgreement=agreement, silenceScores=silence,
            humanLabels=0, alternativeModelsRun=[], deploymentApproved=False)
        lab.atomic(self.directory/'comparison-report.json',lab.encode(report),exclusive=True)
        self.listen(report,plan['scenes'][0])
        self.state['status']='post-hoc-diagnostics-only'; self.save()

    def listen(self, report, scene):
        sections=[]
        for i,row in enumerate(report['validation']):
            methods=', '.join(m['method'] for m in report['methods'] if m['selectedId']==row['card']['id'])
            lab.atomic(self.directory/f'public/evaluator-{i}.wav',(self.directory/row['file']).read_bytes(),exclusive=True)
            sections.append('<section><h2>'+html.escape(methods)+'</h2><p>'+html.escape(row['card']['name'])+'</p><audio controls preload="none" src="evaluator-'+str(i)+'.wav"></audio></section>')
        page='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Awen evaluator comparison</title><style>body{font:17px/1.6 system-ui;max-width:1000px;margin:auto;padding:24px;color:#eeeade;background:#202820}section{border:1px solid #a4b49a;padding:16px;border-radius:8px;margin:16px 0}audio{width:100%}button{font:inherit;padding:10px}</style><h1>Same candidate pool, different objectives</h1><p>Post-hoc CLAP rescoring, not a comparison of different models or human preferences. All selections below use the same new seed. Labels can bias listening.</p><p>'+html.escape(scene['text'])+'</p><button onclick="document.querySelectorAll(\'audio\').forEach(a=>a.pause())">Stop all</button>'+''.join(sections)+'<script>document.querySelectorAll("audio").forEach(a=>{a.volume=.7;a.addEventListener("play",()=>document.querySelectorAll("audio").forEach(b=>{if(a!==b)b.pause()}));});document.addEventListener("keydown",e=>{if(e.key==="Escape")document.querySelectorAll("audio").forEach(a=>a.pause())});</script></html>'
        lab.atomic(self.directory/'public/evaluators.html',page.encode(),exclusive=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('start','resume'))
    parser.add_argument('experiment',nargs='?',type=Path)
    parser.add_argument('--source',type=Path)
    parser.add_argument('--root',type=Path,default=grid.ROOT/'.score-lab/evaluator-comparison')
    parser.add_argument('--max-new-renders',type=int)
    parser.add_argument('--max-new-features',type=int)
    args=parser.parse_args()
    if args.command=='start' and not args.source: parser.error('--source is required')
    if args.command=='resume' and not args.experiment: parser.error('Experiment required')
    if any(v is not None and v<0 for v in (args.max_new_renders,args.max_new_features)): parser.error('Budgets must be nonnegative')
    directory=create(args.root,args.source) if args.command=='start' else args.experiment.resolve()
    print('Experiment:',directory,flush=True)
    with lab.RunLock(directory):
        log=lab.Invocation(directory); engine=None
        try:
            engine=ComparisonEngine(directory,log,args.max_new_renders,args.max_new_features); engine.drive()
            print('Complete:',directory/'public/evaluators.html',flush=True)
        except lab.Paused as error:
            engine.state['status']='paused';engine.save();log.event('paused',reason=str(error));print(error,flush=True)
        except Exception as error:
            if engine: engine.state['status']='failed';engine.save()
            log.event('failed',exception=type(error).__name__);raise
        finally: log.close()


if __name__=='__main__': main()
