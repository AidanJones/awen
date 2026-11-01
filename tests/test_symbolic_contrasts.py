"""Regression contrasts and durable recovery, not perceptual validation."""
import copy
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import calibrate_symbolic as calibration
import score_lab as lab


class ContrastTests(unittest.TestCase):
    def setUp(self):
        self.root = calibration.ROOT / '.score-lab/tests'
        self.root.mkdir(parents=True, exist_ok=True)

    def test_resume_recovers_published_job_and_preserves_report(self):
        with tempfile.TemporaryDirectory(dir=self.root) as tmp:
            directory = calibration.create(tmp)
            def crash(stage, key):
                if stage == 'after_result_publish':
                    raise KeyboardInterrupt('TEST ONLY')
            with self.assertRaises(KeyboardInterrupt):
                calibration.run(directory, crash)
            result = calibration.run(directory)
            self.assertEqual((result['passed'], result['total']), (17, 17))
            self.assertFalse(result['promotionAllowed'])
            before = (directory / 'contrasts.json').read_bytes()
            state = lab.read(directory / 'state.json')
            self.assertTrue(all(len(job['attempts']) == 1 for job in state['jobs'].values()))
            calibration.run(directory)
            self.assertEqual(before, (directory / 'contrasts.json').read_bytes())
            self.assertEqual(state['jobs'], lab.read(directory / 'state.json')['jobs'])

    def test_changed_expectations_and_published_results_are_rejected(self):
        with tempfile.TemporaryDirectory(dir=self.root) as tmp:
            directory = calibration.create(tmp)
            calibration.run(directory)
            state = lab.read(directory / 'state.json')
            result = directory / next(iter(state['jobs'].values()))['result']
            result.write_bytes(result.read_bytes() + b' ')
            with self.assertRaises(ValueError):
                calibration.run(directory)
            other = calibration.create(tmp)
            manifest = lab.read(other / 'experiment.json')
            manifest['comparisons'][0]['op'] = 'eq'
            lab.atomic(other / 'experiment.json', lab.encode(manifest))
            with self.assertRaises(ValueError):
                calibration.run(other)

    def test_failed_relation_is_exposed_not_hidden_by_null(self):
        report = {'rows': [{'id': 'x', 'advisoryScores': {'a': None, 'b': 0.2}}]}
        checks = [{'left': 'x/advisoryScores/a', 'op': 'gt', 'right': 'x/advisoryScores/b'}]
        result = calibration.compare(report, checks)
        self.assertEqual(result['passed'], 0)
        self.assertIsNone(result['checks'][0]['observedLeft'])
        bad = copy.deepcopy(checks)
        bad[0]['op'] = 'unknown'
        with self.assertRaises(ValueError):
            calibration.compare(report, bad)


if __name__ == '__main__':
    unittest.main()
