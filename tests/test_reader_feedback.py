"""Synthetic feedback fixtures test plumbing only, never real listener evidence."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import reader_feedback as feedback
import score_lab as lab


class ReaderFeedbackTests(unittest.TestCase):
    def setUp(self):
        root=lab.ROOT/'.score-lab/tests';root.mkdir(parents=True,exist_ok=True)
        self.tmp=tempfile.TemporaryDirectory(prefix='TEST_ONLY_FEEDBACK_',dir=root);self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.data=json.loads(subprocess.check_output(['node','-e',"console.log(JSON.stringify(require('./tests/feedback-fixture.cjs').fixture()))"],cwd=lab.ROOT))
        second=copy.deepcopy(self.data['records'][0]);second['id']='TEST_SECOND';second['ratings']={'enjoyment':None,'fit':4,'readingHelp':1};second['context']['output']={'mode':'midi','midi':{'channel':1,'parts':'harmony','limit':56}};second['setupNote']='SYNTHETIC FM1 PATCH';self.data['records'].append(second)
        self.file=self.root/'fixture.json';self.file.write_bytes(lab.encode(self.data))

    def test_shared_schema_and_separate_null_labels_contexts(self):
        directory=feedback.create(self.file,self.root/'runs');report=feedback.run(directory)
        self.assertEqual(report['axes']['enjoyment']['answered'],1)
        self.assertEqual(report['axes']['readingHelp']['unanswered'],1)
        self.assertEqual(report['outputCounts'],dict(browser=1,midi=1,both=0))
        self.assertFalse(report['modelTrained']);self.assertFalse(report['rewardPromoted'])
        rows=[json.loads(line) for line in (directory/'labels.jsonl').read_text().splitlines()]
        self.assertEqual(rows[0]['ratings'],dict(enjoyment=5,fit=2,readingHelp=None))
        self.assertEqual(rows[1]['setupNote'],'SYNTHETIC FM1 PATCH')
        self.assertFalse(rows[0]['pairedComparison'])
        before=(directory/'report.json').read_bytes()
        with patch.object(feedback,'validate',side_effect=AssertionError('No validation on completed replay')):feedback.run(directory)
        self.assertEqual(before,(directory/'report.json').read_bytes())
        self.assertEqual(len(list((directory/'logs').glob('*.jsonl'))),2)

    def test_actual_process_death_after_labels_publish_resumes_same_rows(self):
        directory=feedback.create(self.file,self.root/'runs')
        script="import os,sys;sys.path.insert(0,'tools');import reader_feedback as f;f.run(sys.argv[1],fault_hook=lambda:os._exit(72))"
        child=subprocess.run([sys.executable,'-c',script,str(directory)],cwd=lab.ROOT)
        self.assertEqual(child.returncode,72);self.assertFalse((directory/'complete.json').exists())
        before=(directory/'labels.jsonl').read_bytes();feedback.run(directory)
        self.assertEqual(before,(directory/'labels.jsonl').read_bytes())

    def test_rejects_bad_input_changed_sources_and_corrupt_output(self):
        invalid=copy.deepcopy(self.data);invalid['records'][0]['ratings']['fit']=0
        with self.assertRaises(ValueError):feedback.validate(lab.encode(invalid))
        directory=feedback.create(self.file,self.root/'runs')
        with patch.object(feedback,'sources',return_value={}):
            with self.assertRaisesRegex(ValueError,'identity'):feedback.run(directory)
        feedback.run(directory);(directory/'labels.jsonl').write_text('corrupt')
        with self.assertRaisesRegex(ValueError,'output changed'):feedback.run(directory)

    def test_unique_import_roots_do_not_pool_raters_or_mutate_source(self):
        before=self.file.read_bytes();a=feedback.create(self.file,self.root/'runs');b=feedback.create(self.file,self.root/'runs')
        self.assertNotEqual(a,b);feedback.run(a);feedback.run(b);self.assertEqual(before,self.file.read_bytes())
        self.assertEqual(lab.read(a/'report.json')['raterId'],'SYNTHETIC_TEST_ONLY')


if __name__=='__main__':unittest.main()
