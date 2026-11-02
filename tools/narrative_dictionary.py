"""Validate narrative metadata and propose music from supplied annotations; no text classifier."""
import argparse
from pathlib import Path
import subprocess
import uuid

import score_lab as lab

ROOT = lab.ROOT
LIBRARY = ROOT / 'research/narrative-dictionary.json'
VERSION = 'awen-narrative-mapping-1'
FILES = ['tools/narrative_dictionary.py', 'tools/score_lab.py', 'tools/score-lab.cjs', 'index.html',
         'research/narrative-dictionary.json', 'research/narrative-dictionary-fixtures.json',
         'research/scoring-knowledge.json', 'research/classical-knowledge.json']


def sources():
    return {p: lab.sha((ROOT / p).read_bytes()) for p in FILES}


def validate_library(d):
    if d['schemaVersion'] != 1 or d['id'] != 'awen-narrative-dictionary' or d['version'] != '0.1.0' or d['runtimeIntegrated'] or d['humanPreferenceValidated']:
        raise ValueError('Unsupported dictionary version/claims')
    def unique(items):
        ids = [x['id'] for x in items]
        if not ids or len(ids) != len(set(ids)):
            raise ValueError('Missing or duplicate IDs')
        return set(ids)
    refs, options, labels = unique(d['sources']), unique(d['musicalOptions']), unique(d['entries'])
    classical = lab.read(ROOT / 'research/classical-knowledge.json')
    scoring = lab.read(ROOT / 'research/scoring-knowledge.json')
    presets = {p['id'] for p in classical['presets']}
    harmonies = {p['id'] for p in scoring['harmonicFamilies']}
    for s in d['sources']:
        if not s.get('reviewed') or not s.get('observation') or not s.get('reviewDate'):
            raise ValueError('Missing source scope')
        if not s['url'].startswith('https://') and not (ROOT / s['url']).is_file():
            raise ValueError('Invalid source reference')
    # Verify advertised recipe features against the actual production DSL compiler.
    script = "const a=require('./tools/score-lab.cjs').loadRuntime().api;console.log(JSON.stringify(Object.fromEntries(a.CLASSICAL_LIBRARY.presets.map(p=>[p.id,a.compileScoreDSL(p.program)]))));"
    import json
    programs = json.loads(subprocess.check_output(['node', '-e', script], cwd=ROOT, text=True, encoding='utf-8'))
    for o in d['musicalOptions']:
        target = o['targets']
        if o['evidenceStatus'] != 'awen-proposal' or target['classicalPreset'] not in presets or target['harmonyFamily'] not in harmonies or target['criticProfile'] not in ('calm', 'neutral', 'active'):
            raise ValueError('Invalid musical target')
        if o['transition'] != dict(structural='chapter-boundary', expression='smoothed'):
            raise ValueError('Unsafe transition policy')
        p, features = programs[target['classicalPreset']], o['features']
        for key, field in [('texture','texture'), ('gate','gate'), ('holdBars','hold'), ('phraseShape','shape'), ('figure','figure')]:
            if features[key] != p[field]:
                raise ValueError('Feature claim disagrees with compiled preset')
        if features['tempoBpm'] != 72:
            raise ValueError('Unsupported tempo claim')
    for e in d['entries']:
        if e['dimension'] not in d['dimensions'] or e['evidenceStatus'] != 'awen-proposal' or not e['sourceIds'] or not set(e['sourceIds']) <= refs or not set(e['optionIds']) <= options:
            raise ValueError('Invalid label/source/option reference')
        if not all(e.get(k) for k in ('definition', 'examples', 'cues', 'uncertainty')) or not all(e['examples'].get(k) for k in ('positive', 'counter')) or not all(k in e['cues'] for k in ('lexical','context','negation')):
            raise ValueError('Missing annotation guidance')
    reconciliation = d['reconciliation']
    expected = {'runtimeScenes': set(scoring['sceneAliases']), 'sceneFunctions': set(scoring['sceneFunctions']),
                'classicalCues': {c['id'] for c in classical['cues']}}
    for name, keys in expected.items():
        if set(reconciliation[name]) != keys or any(not set(v) <= labels for v in reconciliation[name].values()):
            raise ValueError('Incomplete legacy vocabulary reconciliation')
    if d['constraints'] != dict(tempoBpm=72, tempoChangeSupported=False,
        structuralChanges='chapter-boundary-at-next-32-step-phrase', expressionChanges='smoothed',
        paletteSelection='preserve-user-choice', repetition='diagnostic-not-universal-penalty', qualityReward='none'):
        raise ValueError('Unsupported engine constraints')
    return d


def propose(d, record):
    entries = {e['id']: e for e in d['entries']}
    choices = {o['id']: o for o in d['musicalOptions']}
    candidates, ignored = {}, []
    text = record['text']
    annotations = record['annotations']
    if not isinstance(text, str) or len(text) > 30000 or not isinstance(annotations, list) or len(annotations) > 100:
        raise ValueError('Bounded text/annotations required')
    for a in annotations:
        if a['id'] not in entries or a['state'] not in ('supported', 'rejected', 'uncertain') or a['eventScope'] not in ('current', 'recalled', 'hypothetical', 'unknown') or a['holder'] not in ('narrator', 'character', 'setting', 'structure', 'unknown'):
            raise ValueError('Unknown annotation label/state/scope/holder')
        evidence = a['evidence']
        if a['id'] == 'chapter-boundary' and a['state'] == 'supported' and evidence['source'] != 'metadata':
            raise ValueError('Supported chapter boundary requires document metadata')
        if evidence['source'] == 'metadata':
            if a['id'] != 'chapter-boundary' or record.get('metadata', {}).get('chapterBoundary') is not True:
                raise ValueError('Chapter boundary needs explicit document metadata')
        else:
            context = text if evidence['source'] == 'text' else record.get('preceding') if evidence['source'] == 'preceding' else None
            start, end = evidence['start'], evidence['end']
            if not isinstance(context, str) or type(start) is not int or type(end) is not int or not 0 <= start < end <= len(context) or context[start:end] != evidence['quote']:
                raise ValueError('Annotation evidence span changed')
        if a['state'] != 'supported':
            ignored.append(dict(id=a['id'], reason=a['state']))
            continue
        e = entries[a['id']]
        # Clause-specific scope: a recalled pursuit does not suppress actual dialogue elsewhere.
        if a['eventScope'] != 'current' and e['dimension'] in ('dramatic', 'activation', 'tone', 'environment'):
            ignored.append(dict(id=a['id'], reason='non-current-or-unknown-event-scope'))
            continue
        for option in e['optionIds']:
            candidate = candidates.setdefault(option, dict(option=choices[option], supportingLabels=[], sourceIds=[]))
            if a['id'] not in candidate['supportingLabels']:
                candidate['supportingLabels'].append(a['id'])
            candidate['sourceIds'] = sorted(set(candidate['sourceIds']) | set(e['sourceIds']))
    explicit = record.get('explicitChoice')
    if explicit is not None and explicit not in choices:
        raise ValueError('Unknown explicit musical choice')
    return dict(id=record['id'], version=VERSION, annotationProvenance=record['provenance'],
                classifierExecuted=False, automaticAdoption=False, preserveCurrent=True,
                dictionaryVersion=d['version'], candidates=[candidates[k] for k in sorted(candidates)],
                ignoredLabels=ignored, explicitChoice=explicit, constraints=d['constraints'],
                warning='Unranked Awen proposals from supplied annotations; no fit, quality or preference reward.')


class Engine(lab.Engine):
    def __init__(self, directory, log):
        self.directory = Path(directory).resolve()
        self.manifest = lab.read(self.directory / 'experiment.json')
        self.state = lab.read(self.directory / 'state.json')
        if self.manifest['version'] != VERSION or self.manifest['sources'] != sources() or self.state['manifestSha256'] != lab.sha((self.directory / 'experiment.json').read_bytes()):
            raise ValueError('Dictionary experiment identity changed')
        self.library = validate_library(lab.read(LIBRARY))
        self.log, self.retry, self.fault_hook = log, set(), lambda *_: None

    def worker(self, command, input_path, output_path, log_path):
        if command != 'narrative-mapping':
            raise ValueError('Unexpected dictionary job')
        result = propose(self.library, lab.read(input_path))
        lab.atomic(log_path, b'Explicit annotations only; no classifier, audio or model inference.\n', exclusive=True)
        lab.atomic(output_path, lab.encode(dict(requestSha256=lab.sha(input_path.read_bytes()), result=result)), exclusive=True)

    def drive(self):
        self.state['status'] = 'running'
        self.save()
        rows = [self.execute('narrative-mapping', r) for r in self.manifest['records']]
        report = dict(version=VERSION, sources=self.manifest['sources'], rows=rows,
                      humanRatings=0, classifierExecuted=False, promotionAllowed=False)
        lab.atomic(self.directory / 'report.json', lab.encode(report))
        self.state['status'] = 'complete'
        self.save()
        return report


def create(root, records):
    library = validate_library(lab.read(LIBRARY))
    if not isinstance(records, list) or not 1 <= len(records) <= 100:
        raise ValueError('Bounded nonempty annotation batch required')
    if len({r['id'] for r in records}) != len(records):
        raise ValueError('Duplicate record IDs')
    for r in records:
        propose(library, r)
    directory = Path(root).resolve() / (lab.stamp() + '-' + uuid.uuid4().hex)
    directory.mkdir(parents=True)
    raw = lab.encode(dict(version=VERSION, sources=sources(), records=records))
    lab.atomic(directory / 'experiment.json', raw, exclusive=True)
    lab.atomic(directory / 'state.json', lab.encode(dict(manifestSha256=lab.sha(raw), status='created', jobs={}, renderer=None, judgeIdentity=None)), exclusive=True)
    return directory


def run(directory, fault_hook=None):
    with lab.RunLock(directory):
        log = lab.Invocation(directory)
        try:
            engine = Engine(directory, log)
            if fault_hook:
                engine.fault_hook = fault_hook
            result = engine.drive()
            log.event('complete', reportSha256=lab.sha((Path(directory) / 'report.json').read_bytes()))
            return result
        except BaseException as e:
            log.event('failed', exception=type(e).__name__)
            raise
        finally:
            log.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['validate', 'start', 'resume'])
    parser.add_argument('experiment', nargs='?', type=Path)
    parser.add_argument('--annotations', type=Path)
    parser.add_argument('--root', type=Path, default=ROOT / '.score-lab/narrative-dictionary')
    args = parser.parse_args()
    if args.command == 'validate':
        d = validate_library(lab.read(LIBRARY))
        print('Validated:', len(d['entries']), 'labels;', len(d['musicalOptions']), 'musical alternatives')
        return
    if args.command == 'resume' and not args.experiment:
        parser.error('Resume requires an experiment directory')
    records = lab.read(args.annotations) if args.annotations else lab.read(ROOT / 'research/narrative-dictionary-fixtures.json')['records']
    directory = create(args.root, records) if args.command == 'start' else args.experiment.resolve()
    print('Experiment:', directory, flush=True)
    run(directory)
    print('Complete:', directory / 'report.json')


if __name__ == '__main__':
    main()
