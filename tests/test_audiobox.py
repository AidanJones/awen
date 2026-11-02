"""Evaluator plumbing/control tests. Fake predictions are not real-model evidence."""
import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import audiobox_backend as backend
import audiobox_lab as probe
import score_lab as lab

AXES = ['CE','CU','PC','PQ']
FAKE_IDENTITY = dict(spec={'axes': AXES}, testOnly=True)


class FakePCM:
    def __getitem__(self, key):
        return self


class FakeBackend:
    loads = 0
    def __init__(self, spec, root):
        type(self).loads += 1
        self.identity, self.load_seconds = FAKE_IDENTITY, 0
    def read_pcm(self, file):
        return FakePCM(), 24000
    def official_equivalence(self, pcm, rate):
        return {'TEST_ONLY': True}
    def score_pcm(self, pcm, rate):
        axes = dict.fromkeys(AXES, 4.)
        return dict(axes=axes, windows=[dict(weight=1., axes=axes)], inferenceSeconds=0.)


class AudioboxTests(unittest.TestCase):
    def test_weighting_uses_valid_duration_and_retains_raw_axes(self):
        rows = [dict(weight=1., axes=dict.fromkeys(AXES, 8.)), dict(weight=.2, axes=dict.fromkeys(AXES, 2.))]
        self.assertAlmostEqual(backend.weighted_axes(rows, AXES)['CE'], 7.)
        self.assertGreater(backend.weighted_axes(rows, AXES)['PQ'], 1.)
        for bad in [[], [dict(weight=0, axes=dict.fromkeys(AXES,1))], [dict(weight=1,axes={'CE':float('nan')})]]:
            with self.assertRaises(ValueError):
                backend.weighted_axes(bad, AXES)

    def test_artifact_size_and_content_are_both_verified(self):
        root = lab.ROOT/'.score-lab/tests'
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as tmp:
            file = Path(tmp)/'model'
            file.write_bytes(b'abcd')
            spec = {'files': {'model': dict(bytes=4, sha256=lab.sha(b'abcd'))}}
            backend.verify_files(tmp, spec)
            file.write_bytes(b'abce')
            with self.assertRaises(ValueError): backend.verify_files(tmp,spec)
            file.write_bytes(b'ab')
            with self.assertRaises(ValueError): backend.verify_files(tmp,spec)

    def fixture(self, tmp):
        directory = Path(tmp)/'experiment'
        directory.mkdir()
        rows = []
        for n in range(2):
            file = Path(tmp)/str(n)
            file.write_bytes(('FAKE AUDIO '+str(n)).encode())
            rows.append(dict(id='TEST_ONLY_'+str(n), file=str(file), sha256=lab.sha(file.read_bytes())))
        manifest = dict(version=probe.VERSION, sources=probe.sources(), identity=FAKE_IDENTITY,
                        modelRoot='TEST_ONLY', rows=rows, sourceReportSha256='TEST_ONLY')
        raw = lab.encode(manifest)
        lab.atomic(directory/'experiment.json',raw)
        lab.atomic(directory/'state.json',lab.encode(dict(manifestSha256=lab.sha(raw),status='created',jobs={},renderer=None,judgeIdentity=None)))
        return directory

    def test_budgets_recovery_replay_and_corrupt_wav(self):
        root = lab.ROOT/'.score-lab/tests'
        root.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as tmp, patch.object(probe,'identity',return_value=FAKE_IDENTITY):
            directory = self.fixture(tmp)
            FakeBackend.loads = 0
            result = probe.run(directory,0,FakeBackend)
            self.assertEqual(result['status'],'paused')
            self.assertEqual(FakeBackend.loads,0)
            self.assertEqual(len(probe.run(directory,1,FakeBackend)['rows']),1)
            def crash(stage,key):
                if stage=='after_result_publish':raise KeyboardInterrupt('TEST ONLY')
            with self.assertRaises(KeyboardInterrupt):probe.run(directory,1,FakeBackend,crash)
            loads = FakeBackend.loads
            report = probe.run(directory,0,FakeBackend)
            self.assertEqual(report['status'],'complete')
            self.assertEqual(FakeBackend.loads,loads)
            self.assertTrue(all(r['selectable'] is False for r in report['rows']))
            before = (directory/'report.json').read_bytes()
            state = lab.read(directory/'state.json')
            probe.run(directory,0,FakeBackend)
            self.assertEqual(before,(directory/'report.json').read_bytes())
            self.assertTrue(all(len(j['attempts'])==1 for j in state['jobs'].values()))
            Path(report['rows'][0]['file']).write_bytes(b'corrupt')
            with self.assertRaises(ValueError):probe.run(directory,0,FakeBackend)

    def test_failed_local_inference_retries_in_unique_attempt(self):
        root = lab.ROOT/'.score-lab/tests'
        root.mkdir(parents=True,exist_ok=True)
        class Failed(FakeBackend):
            def score_pcm(self,*_):raise RuntimeError('TEST ONLY local failure')
        with tempfile.TemporaryDirectory(dir=root) as tmp, patch.object(probe,'identity',return_value=FAKE_IDENTITY):
            directory = self.fixture(tmp)
            with self.assertRaises(RuntimeError):probe.run(directory,1,Failed)
            report = probe.run(directory,1,FakeBackend)
            self.assertEqual(len(report['rows']),1)
            job = next(j for j in lab.read(directory/'state.json')['jobs'].values() if j['status']=='complete')
            self.assertEqual(len(job['attempts']),2)
            self.assertNotEqual(job['attempts'][0]['directory'],job['attempts'][1]['directory'])


if __name__ == '__main__':unittest.main()
