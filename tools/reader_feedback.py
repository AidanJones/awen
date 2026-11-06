"""Source-bound import of sparse personal reader feedback, with no reward fitting."""
import argparse
import json
from pathlib import Path
import subprocess
import uuid
import score_lab as lab

VERSION='awen-reader-feedback-import-1'
FILES=['index.html','tools/reader_feedback.py','tools/reader-feedback.cjs','tools/score_lab.py']
AXES=['enjoyment','fit','readingHelp']


def sources():
    return {p:lab.sha((lab.ROOT/p).read_bytes()) for p in FILES}


def validate(raw):
    if len(raw)>2097152:raise ValueError('Feedback exceeds 2 MB')
    result=subprocess.run(['node',str(lab.ROOT/'tools/reader-feedback.cjs')],input=raw,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
    if result.returncode:raise ValueError(result.stderr.decode('utf-8').strip())
    return json.loads(result.stdout)


def create(file,root):
    if Path(file).stat().st_size>2097152:raise ValueError('Feedback exceeds 2 MB')
    raw=Path(file).read_bytes();validate(raw)
    directory=Path(root).resolve()/(lab.stamp()+'-'+uuid.uuid4().hex)
    directory.mkdir(parents=True)
    lab.atomic(directory/'input.json',raw,exclusive=True)
    manifest=dict(version=VERSION,inputSha256=lab.sha(raw),sources=sources())
    lab.atomic(directory/'manifest.json',lab.encode(manifest),exclusive=True)
    return directory


def rows_and_report(data):
    rows=[]
    for r in data['records']:
        c=r['context'];output=c['output']
        rows.append(dict(raterId=data['raterId'],recordId=r['id'],at=r['at'],capturedAt=c['capturedAt'],bookId=c['book']['id'],bookRevision=c['book']['revision'],passageId=c['passage']['id'],textHash32=c['passage']['textHash32'],composerVersion=c['composer']['version'],sketchVersion=c['composer']['sketchVersion'],seed=c['composer']['seed'],step=c['composer']['step'],activeGenome=c['genome'],pendingGenome=c.get('pendingGenome'),activeScene=c['activeScene'],pendingScene=c.get('pendingScene'),outputMode=output['mode'],midi=output['midi'],setupNote=r['setupNote'] or None,ratings=r['ratings'],tags=r['tags'],notes=r['notes'],context=c,independentStudyLabel=False,pairedComparison=False))
    axes={axis:dict(answered=sum(r['ratings'][axis] is not None for r in rows),unanswered=sum(r['ratings'][axis] is None for r in rows),histogram={str(i):sum(r['ratings'][axis]==i for r in rows) for i in range(1,6)}) for axis in AXES}
    report=dict(version=VERSION,raterId=data['raterId'],records=len(rows),axes=axes,outputCounts={mode:sum(r['outputMode']==mode for r in rows) for mode in ['browser','midi','both']},tagCounts={tag:sum(tag in r['tags'] for r in rows) for tag in ['busy','plonky','droney','tense']},modelTrained=False,rewardPromoted=False,automaticRuntimeChange=False,limitations=['Sparse voluntary personal feedback, not a controlled independent study.','No listening exposure, comprehension or acoustic hardware measurements.','Unanswered axes remain null; notes/tags do not imply dislikes on other axes.','Versioned contexts remain archival; identical browser or external audio replay is not established.','No cross-listener pooling, overall quality score or training/test split is inferred.'])
    return rows,report


def run(directory,fault_hook=lambda:None):
    directory=Path(directory).resolve()
    with lab.RunLock(directory):
        log=lab.Invocation(directory)
        try:
            manifest=lab.read(directory/'manifest.json')
            if manifest['version']!=VERSION or manifest['sources']!=sources() or lab.sha((directory/'input.json').read_bytes())!=manifest['inputSha256']:raise ValueError('Source or input identity changed')
            if (directory/'complete.json').exists():
                receipt=lab.read(directory/'complete.json')
                if receipt['manifestSha256']!=lab.sha((directory/'manifest.json').read_bytes()):raise ValueError('Manifest changed')
                if set(receipt['outputs'])!={'labels.jsonl','report.json'}:raise ValueError('Incomplete import receipt')
                for file,sha in receipt['outputs'].items():
                    if lab.sha(lab.safe(directory,file).read_bytes())!=sha:raise ValueError('Imported output changed')
                log.event('verified-replay',newValidations=0);return lab.read(directory/'report.json')
            data=validate((directory/'input.json').read_bytes());rows,report=rows_and_report(data)
            output=b''.join((json.dumps(row,ensure_ascii=False,allow_nan=False,sort_keys=True)+'\n').encode('utf-8') for row in rows)
            lab.atomic(directory/'labels.jsonl',output,exclusive=True)
            fault_hook()
            lab.atomic(directory/'report.json',lab.encode(report),exclusive=True)
            lab.atomic(directory/'complete.json',lab.encode(dict(manifestSha256=lab.sha((directory/'manifest.json').read_bytes()),outputs={file:lab.sha((directory/file).read_bytes()) for file in ['labels.jsonl','report.json']})),exclusive=True)
            log.event('imported',records=len(rows),modelTrained=False);return report
        except BaseException as e:
            log.event('failed',exception=type(e).__name__);raise
        finally:log.close()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['start','resume']);p.add_argument('path',type=Path);p.add_argument('--root',type=Path,default=lab.ROOT/'.score-lab/reader-feedback')
    args=p.parse_args();directory=create(args.path,args.root) if args.command=='start' else args.path.resolve()
    print('Import:',directory,flush=True);print(json.dumps(run(directory),indent=2))
