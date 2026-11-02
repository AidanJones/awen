import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import symbolic_score as score


class ScoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script = "const a=require('./tools/score-lab.cjs').loadRuntime().api;const s=require('./tools/symbolic-score.cjs').exportScore({id:'test',steps:96,genome:a.classicalGenome('flowing','chapters'),timeline:[{step:0,intent:{chapterId:'first',chapterIndex:0}},{step:11,intent:{chapterId:'second',chapterIndex:1,musicCue:{id:'storm'}}}]},a);console.log(JSON.stringify(s));"
        cls.export = json.loads(subprocess.check_output(['node', '-e', script], cwd=score.lab.ROOT, text=True, encoding='utf-8'))

    def test_chapter_segments_and_authored_voices(self):
        result = score.evaluate_score(self.export)
        self.assertEqual([r['startStep'] for r in result['segments']], [0, 32])
        self.assertEqual([r['chapter'] for r in result['segments']], ['first', 'second'])
        self.assertEqual(result['segments'][1]['transpose'], 5)
        self.assertTrue(all(len(s['parts']) == 3 for s in result['segments']))
        self.assertFalse(result['promotionAllowed'])
        self.assertFalse(result['coverage']['scheduledNotes'])

    def test_ambiguous_or_empty_authored_part_abstains(self):
        data = copy.deepcopy(self.export)
        e = next(e for e in data['events'] if e['voice'] == 'dsl.figure')
        data['events'].append(dict(e, midi=e['midi']+4))
        result = score.evaluate_score(data)
        part = next(p for p in result['segments'][0]['parts'] if p['voice'] == 'dsl.figure')
        self.assertFalse(part['monophonic'])
        self.assertIsNone(part['advisoryScores']['melodicEconomy'])
        empty = next(p for p in result['segments'][0]['parts'] if p['voice'] == 'dsl.chord')
        self.assertTrue(all(v is None for v in empty['advisoryScores'].values()))

    def test_missing_voices_context_or_corrupted_clock_rejected(self):
        for mutate in [lambda d:d['events'][0].pop('voice'), lambda d:d['contexts'].pop(),
                       lambda d:d['contexts'][1].update(absoluteStep=500),
                       lambda d:d['events'][0].update(absoluteStep=500)]:
            data = copy.deepcopy(self.export)
            mutate(data)
            with self.assertRaises(ValueError):
                score.evaluate_score(data)

    def test_absolute_phrase_origin_prevents_false_transition(self):
        events = [dict(step=s, midi=m, layer=2, duration=.3) for s, m in [(0,60),(1,84)]]
        result = score.critic.evaluate(events, 2, start_step=31)
        self.assertIsNone(result['advisoryScores']['melodicEconomy'])

    def test_journal_recovers_published_score_and_rejects_tampering(self):
        root = score.lab.ROOT / '.score-lab/tests'
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as tmp:
            path = Path(tmp) / 'input.json'
            score.lab.atomic(path, score.lab.encode([self.export]))
            directory = score.create(tmp, path)
            def crash(stage, key):
                if stage == 'after_result_publish':
                    raise KeyboardInterrupt('TEST ONLY')
            with self.assertRaises(KeyboardInterrupt):
                score.run(directory, crash)
            score.run(directory)
            before = (directory / 'report.json').read_bytes()
            state = score.lab.read(directory / 'state.json')
            score.run(directory)
            self.assertEqual(before, (directory / 'report.json').read_bytes())
            self.assertTrue(all(len(j['attempts']) == 1 for j in state['jobs'].values()))
            job = next(iter(state['jobs'].values()))
            result = directory / job['result']
            result.write_bytes(result.read_bytes()+b' ')
            with self.assertRaises(ValueError):
                score.run(directory)


if __name__ == '__main__':
    unittest.main()
