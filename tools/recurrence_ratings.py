"""Validate and preserve individual pilot ratings, without deriving a reward."""
import argparse
import math
from pathlib import Path
import uuid
import score_lab as lab

AXES=['recurrence','fit','enjoyment','lessDistracting']
CHOICES=[None,'A','B','tie','unsure']


def validate(directory,data):
    directory=Path(directory).resolve()
    packet=lab.read(directory/'packet.json');report=lab.read(directory/'report.json')
    if lab.sha((directory/'packet.json').read_bytes())!=report['packetSha256']:
        raise ValueError('Packet hash changed')
    if data.get('version')!='awen-recurrence-labels-1' or data.get('packetId')!=packet['id'] or data.get('packetSha256')!=report['packetSha256']:
        raise ValueError('Ratings belong to another packet')
    rater=data.get('rater',{})
    if rater.get('kind')!='human' or not isinstance(rater.get('id'),str) or not 1<=len(rater['id'])<=128:
        raise ValueError('Expected an anonymous human rater identity')
    trials={t['id']:t for t in packet['trials']};rows=data.get('responses')
    if not isinstance(rows,list) or len(rows)>len(trials):raise ValueError('Invalid responses')
    seen=set()
    for r in rows:
        ident=r.get('trialId')
        if ident not in trials or ident in seen:raise ValueError('Unknown or duplicate trial')
        seen.add(ident)
        if not all(k in r and r[k] in CHOICES for k in AXES) or type(r.get('heardBoth')) is not bool or type(r.get('revision')) is not int or r['revision']<1:
            raise ValueError('Invalid rating fields')
        if not isinstance(r.get('notes'),str) or len(r['notes'])>1000 or r.get('confidence') not in [None,'low','medium','high']:
            raise ValueError('Invalid notes/confidence')
        for slot in ['A','B']:
            value=r.get('playedSeconds',{}).get(slot)
            if type(value) not in [int,float] or not math.isfinite(value) or not 0<=value<=trials[ident][slot]['seconds']:
                raise ValueError('Invalid playback counter')
    return packet


def summarize(directory,data):
    packet=validate(directory,data);key=lab.read(Path(directory)/'private-key.json')
    if lab.sha((Path(directory)/'private-key.json').read_bytes())!=lab.read(Path(directory)/'report.json')['privateKeySha256']:
        raise ValueError('Private key hash changed')
    responses={r['trialId']:r for r in data['responses']};mapped=[];repeats=[]
    for r in data['responses']:
        mapping=key[r['trialId']]
        answers={axis:mapping[r[axis]] if r[axis] in ['A','B'] else r[axis] for axis in AXES}
        mapped.append(dict(trialId=r['trialId'],scene=mapping['scene'],answers=answers,heardBoth=r['heardBoth'],playedSeconds=r['playedSeconds']))
        original=responses.get(mapping['repeatOf'])
        if original:
            old=key[original['trialId']]
            agreement={}
            for axis in AXES:
                a=answers[axis];b=old[original[axis]] if original[axis] in ['A','B'] else original[axis]
                agreement[axis]=None if a in [None,'unsure'] or b in [None,'unsure'] else a==b
            repeats.append(dict(trialId=r['trialId'],original=mapping['repeatOf'],agreement=agreement))
    return dict(version='awen-recurrence-summary-1',rater=data['rater'],packetId=packet['id'],
                rows=mapped,repeatComparisons=repeats,thresholdChanged=False,promotionAllowed=False,
                note='Descriptive individual answers, including incomplete listening; no pooled preference score or validated reward.')


def ingest(directory,file):
    file=Path(file)
    if file.stat().st_size>1048576:raise ValueError('Ratings exceed 1 MB')
    raw=file.read_bytes();data=lab.read(file);summary=summarize(directory,data)
    target=Path(directory)/'ratings'/(lab.stamp()+'-'+uuid.uuid4().hex)
    lab.atomic(target/'ratings.json',raw,exclusive=True)
    lab.atomic(target/'summary.json',lab.encode(summary),exclusive=True)
    return target


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('experiment',type=Path);p.add_argument('ratings',type=Path)
    a=p.parse_args();print(ingest(a.experiment,a.ratings))
