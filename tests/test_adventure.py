"""Engineering fixtures only: no actual listener labels."""
import array
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
import adventure_listening as review
import recurrence_ratings as ratings
import score_lab as lab


def fake_worker(self, command, input_path, output_path, log_path):
    payload=lab.read(input_path)
    if command=='plan':
        result=[dict(id=k,palette='romantic',genome={},text='TEST ONLY',context='',
            chapter=dict(id=k,title=k),book=dict(id='rat',title='Test',author='Test',revision='test',url='https://example.com',license='test')) for k in ['caper','reflection']]
    else:
        value=800 if payload['treatment']=='baseline' else 1400
        wav,_,_=review.attenuate(array.array('h',[value,-value]*120),1)
        trace=lab.encode(payload)
        lab.atomic(output_path.parent/'audio.wav',wav,exclusive=True)
        lab.atomic(output_path.parent/'trace.json',trace,exclusive=True)
        result=dict(file='audio.wav',sha256=lab.sha(wav),traceFile='trace.json',traceSha256=lab.sha(trace),seconds=165,cap=.14,renderer=dict(testOnly=True))
    lab.atomic(output_path,lab.encode(dict(requestSha256=lab.sha(input_path.read_bytes()),result=result)),exclusive=True)


class AdventureTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.directory=review.create(self.tmp.name)

    def prepare(self):
        with patch.object(review.Engine,'worker',fake_worker): return review.run(self.directory)

    def test_pair_matching_blinding_and_zero_labels(self):
        report=self.prepare();packet=lab.read(self.directory/'packet.json');key=lab.read(self.directory/'private-key.json')
        self.assertEqual(report['humanRatings'],0);self.assertEqual(report['clips'],4)
        self.assertEqual(len(packet['trials']),4)
        self.assertEqual(sum(v['repeatOf'] is not None for v in key.values()),2)
        self.assertTrue(all(m['gain']<=1 for m in report['measures']))
        self.assertTrue(all(abs(m['matchedRms']-m['targetRms'])<2/32767 for m in report['measures']))
        self.assertNotIn('genome',packet['scenes'][0]);self.assertNotIn('baseline',json.dumps(packet))
        html=(self.directory/'public/review.html').read_text(encoding='utf8')
        self.assertIn('Which arrangement works',html);self.assertNotIn('__CALIBRATION_DATA__',html)
        self.assertNotIn('86 seconds',html)

    def test_chunk_resume_and_corruption(self):
        with patch.object(review.Engine,'worker',fake_worker):
            with self.assertRaises(lab.Paused): review.run(self.directory,1)
        self.prepare();before=(self.directory/'report.json').read_bytes()
        with patch.object(review.Engine,'worker',side_effect=AssertionError('No rerender')): review.run(self.directory,0)
        self.assertEqual(before,(self.directory/'report.json').read_bytes())
        next((self.directory/'jobs').rglob('audio.wav')).write_bytes(b'CORRUPT')
        with self.assertRaisesRegex(ValueError,'artifact hash'): review.run(self.directory,0)
        self.assertEqual(len(list((self.directory/'logs').glob('*.jsonl'))),4)

    def test_process_death_rehydrates_result(self):
        script="import sys,os;sys.path[:0]=['tools','tests'];import adventure_listening as r;from test_adventure import fake_worker;r.Engine.worker=fake_worker;r.run(sys.argv[1],fault_hook=lambda stage,key:os._exit(71) if stage=='after_result_publish' and key.startswith('render') else None)"
        child=subprocess.run([sys.executable,'-c',script,str(self.directory)],cwd=lab.ROOT)
        self.assertEqual(child.returncode,71);self.prepare()
        self.assertTrue(all(len(j['attempts'])==1 for j in lab.read(self.directory/'state.json')['jobs'].values()))

    def test_failed_worker_retains_attempt_and_recovers(self):
        failed=False
        def flaky(engine, command, input_path, output_path, log_path):
            nonlocal failed
            if command=='render' and not failed:
                failed=True
                raise RuntimeError('SYNTHETIC worker failure')
            return fake_worker(engine,command,input_path,output_path,log_path)
        with patch.object(review.Engine,'worker',flaky):
            with self.assertRaisesRegex(RuntimeError,'SYNTHETIC'):review.run(self.directory)
        self.prepare()
        attempts=[j['attempts'] for j in lab.read(self.directory/'state.json')['jobs'].values()]
        retried=next(a for a in attempts if len(a)==2)
        self.assertEqual([a['status'] for a in retried],['failed','complete'])

    def test_changed_sources_require_new_run(self):
        with patch.object(review,'sources',return_value={'changed':'source'}):
            with self.assertRaisesRegex(ValueError,'source identity'):review.run(self.directory)

    def test_existing_ratings_import_works_without_pooling_objectives(self):
        self.prepare();packet=lab.read(self.directory/'packet.json')
        row=dict(trialId=packet['trials'][0]['id'],revision=1,fit='A',enjoyment='B',lessDistracting='tie',recurrence=None,heardBoth=True,confidence='low',notes='SYNTHETIC TEST ONLY',playedSeconds=dict(A=1,B=1))
        data=dict(version='awen-recurrence-labels-1',packetId=packet['id'],packetSha256=lab.sha((self.directory/'packet.json').read_bytes()),rater=dict(id='TEST_ONLY',kind='human'),responses=[row])
        result=ratings.summarize(self.directory,data)
        self.assertNotEqual(result['rows'][0]['answers']['fit'],result['rows'][0]['answers']['enjoyment'])
        self.assertFalse(result['promotionAllowed'])
        bad=copy.deepcopy(data);bad['packetSha256']='wrong'
        with self.assertRaises(ValueError):ratings.validate(self.directory,bad)

    def test_attenuation_never_boosts(self):
        with self.assertRaises(ValueError):review.attenuate(array.array('h',[1000]),1.01)


if __name__=='__main__':unittest.main()
