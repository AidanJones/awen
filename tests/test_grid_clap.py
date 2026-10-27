"""Recovery/identity tests use a TEST ONLY fake encoder, never listener evidence."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
import grid_clap as grid
import score_lab as lab


class FakeBackend:
    calls = 0

    def __init__(self, *args):
        pass

    def feature(self, *args):
        type(self).calls += 1
        return [1.] + [0.]*511


class GridTests(unittest.TestCase):
    def test_objective_ignores_unused_wording(self):
        rows = [{'target-1': .2, 'target-2': .4, 'check-1': 100},
                {'target-1': .4, 'target-2': .6, 'check-1': -100}]
        self.assertAlmostEqual(grid.objective(rows), .4)

    def test_published_feature_recovers_and_corruption_rejected(self):
        root = grid.ROOT/'.score-lab/tests'
        root.mkdir(parents=True, exist_ok=True)
        identity = lambda spec: {'spec': spec, 'packages': {'TEST_ONLY': 'fake'}}
        with tempfile.TemporaryDirectory(dir=root) as tmp, patch.object(grid.emb, 'model_identity', identity):
            directory = grid.create(Path(tmp)/'runs')
            manifest = lab.read(directory/'experiment.json')
            manifest['cache'] = str(Path(tmp)/'cache')
            raw = lab.encode(manifest)
            lab.atomic(directory/'experiment.json', raw)
            state = lab.read(directory/'state.json'); state['manifestSha256']=lab.sha(raw)
            lab.atomic(directory/'state.json', lab.encode(state))
            log = lab.Invocation(directory)
            try:
                first = grid.GridEngine(directory, log)
                first.factory = FakeBackend
                def crash(stage, key):
                    if stage=='after_result_publish': raise KeyboardInterrupt('TEST ONLY crash')
                first.fault_hook = crash
                before = FakeBackend.calls
                with self.assertRaisesRegex(KeyboardInterrupt, 'crash'):
                    first.text('TEST ONLY feature')
                resumed = grid.GridEngine(directory, log)
                resumed.factory = FakeBackend
                self.assertEqual(resumed.text('TEST ONLY feature')[0], 1.)
                self.assertEqual(FakeBackend.calls, before+1)
                job = next(iter(resumed.state['jobs'].values()))
                result = lab.safe(directory, job['result'])
                result.write_bytes(b'changed')
                with self.assertRaisesRegex(ValueError, 'changed'):
                    resumed.text('TEST ONLY feature')
                self.assertEqual(len(job['attempts']), 1)
            finally:
                log.close()

    def test_frozen_small_search_design(self):
        suite = lab.read(grid.ROOT/'research/grid-clap-suite.json')
        self.assertEqual(suite['generations']*suite['childrenPerGeneration'], 12)
        self.assertNotEqual(suite['searchSeed'], suite['checkSeed'])
        self.assertTrue(all(start+10<=suite['seconds'] for start in suite['windows']))
        self.assertEqual(len(suite['captions']), 6)


if __name__=='__main__':
    unittest.main()
