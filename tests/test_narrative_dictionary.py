"""Authored mapping controls; not classifier accuracy or listener validation."""
import copy
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import narrative_dictionary as nd


class NarrativeDictionaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.library = nd.validate_library(nd.lab.read(nd.LIBRARY))
        cls.fixtures = nd.lab.read(nd.ROOT / 'research/narrative-dictionary-fixtures.json')

    def test_dictionary_reconciles_existing_vocabularies_and_real_preset_features(self):
        self.assertEqual(len(self.library['entries']), 28)
        self.assertEqual(len(self.library['musicalOptions']), 12)
        self.assertEqual({e['dimension'] for e in self.library['entries']}, set(self.library['dimensions']))
        self.assertEqual(self.library['reconciliation']['runtimeScenes']['chase'], ['pursuit'])
        self.assertEqual(self.library['reconciliation']['classicalCues']['neutral'], [])
        self.assertTrue(self.library['runtimeIntegrated'])
        self.assertEqual(self.library['runtimeScope'], 'manual-interpretation-and-audition-only')
        self.assertFalse(self.library['humanPreferenceValidated'])

    def test_controls_preserve_scope_uncertainty_and_multiple_alternatives(self):
        for record in self.fixtures['records']:
            with self.subTest(record=record['id']):
                before = copy.deepcopy(record)
                result = nd.propose(self.library, record)
                self.assertEqual([c['option']['id'] for c in result['candidates']], record['expected']['optionIds'])
                self.assertEqual(sorted(c['id'] for c in result['ignoredLabels']), record['expected']['ignoredLabelIds'])
                self.assertFalse(result['classifierExecuted'])
                self.assertFalse(result['automaticAdoption'])
                self.assertTrue(result['preserveCurrent'])
                self.assertEqual(result['explicitChoice'], record.get('explicitChoice'))
                self.assertEqual(record, before)

    def test_bad_references_features_and_transition_claims_fail(self):
        mutations = [lambda d:d['entries'][0].update(sourceIds=['MISSING']),
                     lambda d:d['entries'][0].update(optionIds=['MISSING']),
                     lambda d:d['musicalOptions'][0]['features'].update(tempoBpm=180),
                     lambda d:d['musicalOptions'][0]['features'].update(gate=999),
                     lambda d:d['musicalOptions'][0]['transition'].update(structural='immediate'),
                     lambda d:d['reconciliation']['runtimeScenes'].pop('chase')]
        for mutate in mutations:
            d = copy.deepcopy(self.library)
            mutate(d)
            with self.assertRaises(ValueError):
                nd.validate_library(d)

    def test_changed_spans_unknown_labels_and_spurious_chapters_fail(self):
        for mutate in [lambda r:r['annotations'][0].update(id='MISSING'),
                       lambda r:r['annotations'][0]['evidence'].update(quote='WRONG'),
                       lambda r:r.update(explicitChoice='MISSING')]:
            record = copy.deepcopy(self.fixtures['records'][0])
            mutate(record)
            with self.assertRaises(ValueError):
                nd.propose(self.library, record)
        chapter = copy.deepcopy(next(r for r in self.fixtures['records'] if r['id'] == 'chapter-word-is-not-boundary'))
        chapter['annotations'][0]['state'] = 'supported'
        with self.assertRaises(ValueError):
            nd.propose(self.library, chapter)

    def test_proposed_annotation_holdouts_are_grouped_not_accuracy_claims(self):
        plan = self.fixtures['holdoutPlan']
        self.assertFalse(set(plan['developmentBooks']) & set(plan['annotationHoldoutBooks']))
        self.assertFalse(self.fixtures['independentlyAnnotated'])
        self.assertFalse(self.fixtures['classifierAccuracyMeasured'])
        self.assertEqual(plan['status'], 'proposed-not-annotated')

    def test_unique_runs_recover_and_reject_corruption(self):
        root = nd.ROOT / '.score-lab/tests'
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as tmp:
            records = self.fixtures['records'][:2]
            directory = nd.create(tmp, records)
            self.assertNotEqual(directory, nd.create(tmp, records))
            def crash(stage, key):
                if stage == 'after_result_publish':
                    raise KeyboardInterrupt('TEST ONLY')
            with self.assertRaises(KeyboardInterrupt):
                nd.run(directory, crash)
            nd.run(directory)
            before = (directory / 'report.json').read_bytes()
            state = nd.lab.read(directory / 'state.json')
            nd.run(directory)
            self.assertEqual(before, (directory / 'report.json').read_bytes())
            self.assertEqual(state['jobs'], nd.lab.read(directory / 'state.json')['jobs'])
            self.assertTrue(all(len(j['attempts']) == 1 for j in state['jobs'].values()))
            job = next(iter(state['jobs'].values()))
            result = directory / job['result']
            result.write_bytes(result.read_bytes()+b' ')
            with self.assertRaises(ValueError):
                nd.run(directory)


if __name__ == '__main__':
    unittest.main()
