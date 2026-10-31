"""Pure-engineering tests; scores here are synthetic and are not benchmark evidence."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import compare_muq as compare
import muq_backend as backend


class MuQComparisonTests(unittest.TestCase):
    def test_artifacts_reject_tampering(self):
        parent=compare.ROOT/'.score-lab/tests';parent.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as temporary:
            root=Path(temporary);data=b'TEST ONLY model artifact';(root/'file').write_bytes(data)
            spec={'files':{'file':{'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}}}
            backend.verify_files(root,spec)
            (root/'file').write_bytes(b'x'*len(data))
            with self.assertRaisesRegex(ValueError,'checksum'):backend.verify_files(root,spec)
            (root/'file').write_bytes(b'x')
            with self.assertRaisesRegex(ValueError,'size'):backend.verify_files(root,spec)

    def test_diagnostics_keep_silence_wording_and_level_separate(self):
        rows=[{'id':'g2-2-8kqe3d','scores':[{'target-1':.8,'target-2':.2}]*2,'targetMean':.5,'unusedMean':.4,'specificity':.1},
              {'id':'other','scores':[{'target-1':.4,'target-2':.6}]*2,'targetMean':.5,'unusedMean':.3,'specificity':-.1}]
        silence={'target-1':.7,'target-2':.7,'check-1':.35,'check-2':.35}
        quiet=[{'target-1':.6,'target-2':.2}]*2
        d=compare.diagnostics(rows,silence,quiet)
        self.assertEqual(d['wordingRankFlipPairs'],1);self.assertEqual(d['windowRankFlipPairs'],0)
        self.assertEqual(d['silenceAboveUnusedMean'],['other']);self.assertEqual(len(d['silenceAboveTargetMean']),2)
        self.assertAlmostEqual(d['halfAmplitudeTargetDelta'],-.1);self.assertEqual(d['positiveSpecificity'],1)

    def test_suite_is_small_and_identical_windows(self):
        suite=compare.lab.read(compare.ROOT/'research/muq-comparison-suite.json')
        self.assertEqual(len(suite['cards']),5);self.assertEqual(suite['windows'],[2,18])
        self.assertIn('bed',suite['cards'])


if __name__=='__main__':unittest.main()
