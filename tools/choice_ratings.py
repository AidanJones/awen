"""Archive overall A/B choices without inventing separate musical ratings."""
import argparse
from datetime import datetime
from pathlib import Path
import uuid
import score_lab as lab


def summarize(directory, data):
    directory=Path(directory)
    packet=lab.read(directory/'packet.json'); report=lab.read(directory/'report.json')
    if lab.sha((directory/'packet.json').read_bytes())!=report['packetSha256']:
        raise ValueError('Packet hash changed')
    if (data.get('version')!='awen-choice-labels-1' or data.get('packetId')!=packet['id']
        or data.get('packetSha256')!=report['packetSha256']):
        raise ValueError('Choices belong to another packet')
    rater=data.get('rater',{})
    if rater.get('kind')!='human' or not isinstance(rater.get('id'),str) or not 1<=len(rater['id'])<=128:
        raise ValueError('Invalid anonymous rater')
    key=lab.read(directory/'private-key.json')
    if lab.sha((directory/'private-key.json').read_bytes())!=report['privateKeySha256']:
        raise ValueError('Identity key changed')
    trials={t['id']:t for t in packet['trials']}; responses=data.get('responses')
    if not isinstance(responses,list) or len(responses)>len(trials): raise ValueError('Invalid responses')
    rows=[]; seen=set()
    for r in responses:
        if not isinstance(r,dict): raise ValueError('Invalid response')
        ident=r.get('trialId');choice=r.get('choice')
        if ident not in trials or ident in seen or choice not in ['A','B','tie','neither']:
            raise ValueError('Unknown, duplicate or invalid choice')
        try:
            at=datetime.fromisoformat(r['at'].replace('Z','+00:00'))
            if at.tzinfo is None:raise ValueError('Missing timezone')
        except (KeyError,TypeError,AttributeError,ValueError): raise ValueError('Invalid answer timestamp') from None
        seen.add(ident)
        rows.append(dict(trialId=ident,scene=trials[ident]['scene'],choice=choice,
            overallPreference=key[ident][choice] if choice in ['A','B'] else choice,
            fit=None,enjoyment=None,lessDistracting=None))
    return dict(version='awen-choice-summary-1',packetId=packet['id'],rater=rater,rows=rows,
        promotionAllowed=False,rewardModelTrained=False,
        note='Overall choices only. No separate fit, enjoyment, distraction, listening duration or confidence inferred.')


def ingest(directory, file):
    file=Path(file)
    if file.stat().st_size>1048576: raise ValueError('Choices exceed 1 MB')
    raw=file.read_bytes(); summary=summarize(directory,lab.read(file))
    target=Path(directory)/'ratings'/(lab.stamp()+'-'+uuid.uuid4().hex)
    lab.atomic(target/'choices.json',raw,exclusive=True)
    lab.atomic(target/'summary.json',lab.encode(summary),exclusive=True)
    return target


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('experiment',type=Path);parser.add_argument('choices',type=Path)
    args=parser.parse_args();print(ingest(args.experiment,args.choices))
