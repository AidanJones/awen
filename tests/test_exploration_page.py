import importlib.util
import json
import re
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('exploration_page', Path(__file__).resolve().parents[1] / 'tools/exploration_page.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ExplorationTests(unittest.TestCase):
    def test_optional_reader_bundle_and_explicit_handoff_link(self):
        root=module.ROOT/'.score-lab/tests';root.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as tmp:
            file=module.build(Path(tmp)/'bundle',include_reader=True)
            html=file.read_text(encoding='utf-8')
            data=json.loads(re.search(r'id="exploration-data"[^>]*>(.*?)</script>',html,re.S)[1])
            self.assertEqual(data['readerUrl'],'index.html?explorer=explore.html')
            self.assertEqual((file.parent/'index.html').read_text(encoding='utf-8'),(module.ROOT/'index.html').read_text(encoding='utf-8'))
            self.assertTrue(json.loads((file.parent/'manifest.json').read_text())['readerIncluded'])
            for invalid in ['javascript:alert(1)','//example.com/explore','data:text/html,hi']:
                with self.assertRaises(ValueError):module.build(Path(tmp)/'bad',reader_url=invalid)

    def test_standalone_and_no_overwrite(self):
        root = module.ROOT / '.score-lab/tests'
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as tmp:
            target = Path(tmp) / 'new'
            file = module.build(target, 'http://127.0.0.1:50473/review.html')
            html = file.read_text(encoding='utf-8')
            data = json.loads(re.search(r'id="exploration-data"[^>]*>(.*?)</script>', html, re.S)[1])
            self.assertEqual(len(data['scenes']), 6)
            self.assertEqual(len({s['book']['id'] for s in data['scenes']}), 3)
            self.assertNotIn('__PRODUCTION_RUNTIME__', html)
            self.assertNotIn('<script src=', html)
            self.assertIn('class AudioAdapter', html)
            self.assertIn('OUTPUT_CEILING=.14', html)
            self.assertNotIn('awen-calibration-labels-1', html)
            with self.assertRaises(FileExistsError):
                module.build(target)


if __name__ == '__main__':
    unittest.main()
