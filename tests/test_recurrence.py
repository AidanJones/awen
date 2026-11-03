"""Engineering tests only: all rating fixtures are synthetic, never listener evidence."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import recurrence_listening as review
import recurrence_ratings as ratings
import score_lab as lab


def fake_worker(self,command,input_path,output_path,log_path):
    payload=lab.read(input_path)
    if command=='plan':
        result=[dict(id=k,palette=p,text='TEST ONLY',context='',chapter=dict(id='one',title='One'),book=dict(id=k,title=k,author='Test',revision='test',url='https://example.com',license='test')) for k,p in [('rat','baroque'),('riders','romantic')]]
    else:
        wav=lab.encode(payload);trace=b'[]'
        lab.atomic(output_path.parent/'audio.wav',wav,exclusive=True);lab.atomic(output_path.parent/'trace.json',trace,exclusive=True)
        result=dict(file='audio.wav',sha256=lab.sha(wav),traceFile='trace.json',traceSha256=lab.sha(trace),seconds=86,renderer=dict(testOnly=True))
    lab.atomic(output_path,lab.encode(dict(requestSha256=lab.sha(input_path.read_bytes()),result=result)),exclusive=True)


class RecurrenceTests(unittest.TestCase):
    def setUp(self):
        root=lab.ROOT/'.score-lab/tests';root.mkdir(parents=True,exist_ok=True)
        self.tmp=tempfile.TemporaryDirectory(dir=root);self.addCleanup(self.tmp.cleanup)
        self.directory=review.create(Path(self.tmp.name))

    def prepare(self):
        with patch.object(review.Engine,'worker',fake_worker):review.run(self.directory)

    def test_blinding_pairs_reservations_and_zero_ratings(self):
        self.prepare();packet=lab.read(self.directory/'packet.json');key=lab.read(self.directory/'private-key.json')
        self.assertEqual(len(packet['trials']),14)
        self.assertEqual(len(key),14)
        self.assertEqual(sum(v['repeatOf'] is not None for v in key.values()),2)
        for scene in packet['scenes']:
            pairs={frozenset([r['A'],r['B']]) for r in key.values() if r['scene']==scene['id']}
            self.assertEqual(len(pairs),6)
            self.assertNotIn('palette',scene)
        html=(self.directory/'public/review.html').read_text(encoding='utf8')
        self.assertNotIn('private-key',html);self.assertNotIn('"treatment"',html)
        self.assertFalse(lab.read(self.directory/'report.json')['reserved']['rendered'])
        self.assertEqual(lab.read(self.directory/'report.json')['humanRatings'],0)

    def test_chunk_resume_replay_and_tamper_rejection(self):
        with patch.object(review.Engine,'worker',fake_worker):
            with self.assertRaises(lab.Paused):review.run(self.directory,2)
        self.prepare()
        before=(self.directory/'report.json').read_bytes()
        attempts=sum(len(j['attempts']) for j in lab.read(self.directory/'state.json')['jobs'].values())
        with patch.object(review.Engine,'worker',side_effect=AssertionError('No recompute')):review.run(self.directory,0)
        self.assertEqual(before,(self.directory/'report.json').read_bytes())
        self.assertEqual(attempts,sum(len(j['attempts']) for j in lab.read(self.directory/'state.json')['jobs'].values()))
        wav=next((self.directory/'jobs').rglob('audio.wav'));wav.write_bytes(b'CORRUPT')
        with self.assertRaisesRegex(ValueError,'artifact hash'):review.run(self.directory,0)

    def test_actual_process_death_recovers_published_result(self):
        script="import sys,os;sys.path.insert(0,'tools');sys.path.insert(0,'tests');import recurrence_listening as r;from test_recurrence import fake_worker;r.Engine.worker=fake_worker;r.run(sys.argv[1],fault_hook=lambda stage,key:os._exit(71) if stage=='after_result_publish' and key.startswith('render') else None)"
        child=subprocess.run([sys.executable,'-c',script,str(self.directory)],cwd=lab.ROOT)
        self.assertEqual(child.returncode,71)
        self.prepare()
        jobs=lab.read(self.directory/'state.json')['jobs'].values()
        self.assertTrue(all(len(j['attempts'])==1 for j in jobs))

    def test_individual_axes_ties_repeats_and_backup_validation(self):
        self.prepare();packet=lab.read(self.directory/'packet.json');key=lab.read(self.directory/'private-key.json')
        repeat=next(k for k,v in key.items() if v['repeatOf']);original=key[repeat]['repeatOf']
        rows=[]
        for ident in [original,repeat]:
            choice='A' if ident==original else 'B'
            rows.append(dict(trialId=ident,revision=1,recurrence=choice,fit='tie',enjoyment='unsure',lessDistracting=None,heardBoth=True,confidence='low',notes='SYNTHETIC TEST ONLY',playedSeconds=dict(A=2,B=3)))
        data=dict(version='awen-recurrence-labels-1',packetId=packet['id'],packetSha256=lab.sha((self.directory/'packet.json').read_bytes()),rater=dict(id='TEST_ONLY',kind='human'),responses=rows)
        result=ratings.summarize(self.directory,data)
        self.assertEqual(result['repeatComparisons'][0]['agreement'],dict(recurrence=True,fit=True,enjoyment=None,lessDistracting=None))
        for mutate in [lambda d:d.update(packetSha256='wrong'),lambda d:d['responses'].append(d['responses'][0]),lambda d:d['responses'][0].update(recurrence='bad'),lambda d:d['responses'][0].pop('fit'),lambda d:d['responses'][0]['playedSeconds'].update(A=999)]:
            invalid=copy.deepcopy(data);mutate(invalid)
            with self.assertRaises(ValueError):ratings.validate(self.directory,invalid)

    def test_authored_score_has_expected_recurrence_without_quality_claim(self):
        script="const {score}=require('./tools/recurrence-worker.cjs'); console.log(JSON.stringify(['cell','ostinato','varied','sustained'].map(t=>score(t))))"
        scores=json.loads(subprocess.check_output(['node','-e',script],cwd=lab.ROOT,text=True))
        self.assertEqual([len(s['notes']) for s in scores],[96,96,96,12])
        def phrase(s,n):return [(e['step']%32,e['midi'],e['duration']) for e in s['notes'] if n*32<=e['step']<(n+1)*32]
        self.assertEqual(phrase(scores[1],0),phrase(scores[1],1))
        self.assertNotEqual(phrase(scores[2],0),phrase(scores[2],1))
        self.assertTrue(all(s['harmony']==scores[0]['harmony'] for s in scores))


if __name__=='__main__':unittest.main()
