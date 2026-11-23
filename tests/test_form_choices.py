"""Synthetic engineering choices only; never real user preferences."""
import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'tools'),str(Path(__file__).resolve().parent)]
import adventure_listening as review
import choice_ratings as ratings
import score_lab as lab
from test_adventure import fake_worker


class ChoiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.directory=review.create(self.tmp.name,'form')
        with patch.object(review.Engine,'worker',fake_worker):review.run(self.directory)
        self.packet=lab.read(self.directory/'packet.json')

    def data(self):
        return dict(version='awen-choice-labels-1',packetId=self.packet['id'],
            packetSha256=lab.sha((self.directory/'packet.json').read_bytes()),
            rater=dict(id='SYNTHETIC_TEST_ONLY',kind='human'),responses=[dict(
                trialId=self.packet['trials'][0]['id'],choice='A',at='2026-11-23T18:00:00Z')])

    def test_two_passages_simple_template_no_forced_repeats_or_description(self):
        self.assertEqual([t['scene'] for t in self.packet['trials']],['caper','reflection'])
        self.assertEqual(len(self.packet['trials']),2)
        html=(self.directory/'public/review.html').read_text(encoding='utf8')
        self.assertIn('Choose A',html);self.assertIn('Neither',html)
        self.assertNotIn('<textarea',html);self.assertNotIn('<select',html)
        self.assertNotIn('alternating',html);self.assertNotIn('grouped',html)
        self.assertNotIn('__CALIBRATION_DATA__',html)
        self.assertEqual(lab.read(self.directory/'report.json')['humanRatings'],0)

    def test_decode_choices_without_inventing_axes(self):
        data=self.data();result=ratings.summarize(self.directory,data)
        key=lab.read(self.directory/'private-key.json')
        self.assertEqual(result['rows'][0]['overallPreference'],key[data['responses'][0]['trialId']]['A'])
        self.assertTrue(all(result['rows'][0][k] is None for k in ['fit','enjoyment','lessDistracting']))
        self.assertFalse(result['promotionAllowed'])
        for choice in ['tie','neither']:
            data['responses'][0]['choice']=choice
            self.assertEqual(ratings.summarize(self.directory,data)['rows'][0]['overallPreference'],choice)
        data['responses']=[];self.assertEqual(ratings.summarize(self.directory,data)['rows'],[])

    def test_invalid_choices_and_cross_packet_import_rejected(self):
        for mutate in [lambda d:d.update(packetSha256='wrong'),lambda d:d['responses'].append(d['responses'][0]),lambda d:d['responses'][0].update(choice='C'),lambda d:d['responses'][0].update(at='bad')]:
            data=self.data();mutate(data)
            with self.assertRaises(ValueError):ratings.summarize(self.directory,data)

    def test_archival_import_is_unique(self):
        source=self.directory/'TEST_ONLY.json';lab.atomic(source,lab.encode(self.data()))
        a=ratings.ingest(self.directory,source);b=ratings.ingest(self.directory,source)
        self.assertNotEqual(a,b);self.assertEqual((a/'choices.json').read_bytes(),source.read_bytes())

    def test_cached_resume_reuses_completed_clips(self):
        before=(self.directory/'report.json').read_bytes()
        with patch.object(review.Engine,'worker',side_effect=AssertionError('No rerender')):review.run(self.directory,0)
        self.assertEqual(before,(self.directory/'report.json').read_bytes())


if __name__=='__main__':unittest.main()
