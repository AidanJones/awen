"""Notation diagnostics and gate logic, not musical preference validation."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import variation_review as review
import score_lab as lab


class VariationTests(unittest.TestCase):
    def test_controls_distinguish_cell_length_contour_and_harmony_without_quality_reward(self):
        rows={r['id'].split('/')[1]:review.diagnose(r) for r in review.controls()}
        self.assertEqual(rows['ostinato']['diagnostics']['shortestExactGridPeriodSlots'],8)
        self.assertEqual(rows['short-cell']['diagnostics']['shortestExactGridPeriodSlots'],2)
        self.assertEqual(rows['ostinato']['diagnostics']['completeWindowDistinctPitches'],3)
        self.assertEqual(rows['short-cell']['diagnostics']['completeWindowDistinctPitches'],1)
        transpose=rows['transposed-figure']['diagnostics']
        self.assertEqual(transpose['pitchRhythmPhrasePatterns'],2)
        self.assertEqual(transpose['layerRelativeContourPhrasePatterns'],1)
        self.assertEqual(transpose['explicitHarmonicChanges'],1)
        self.assertIsNone(rows['empty']['diagnostics']['shortestExactGridPeriodSlots'])
        self.assertTrue(all(r['qualityScore'] is None and not r['thresholdChanged'] and not r['promotionAllowed'] for r in rows.values()))

    def test_actual_legacy_gate_can_distinguish_duration_jitter_but_reject_ostinato(self):
        cases=[r for r in review.controls() if r['id'] in ('CONTROL/ostinato','CONTROL/duration-jitter')]
        # Synthetic physically-valid signal isolates structural gate logic; no rendered audio claim.
        script="const m=require('./tools/score-lab-metrics.cjs'),fs=require('node:fs');const cases=JSON.parse(fs.readFileSync(0,'utf8'));console.log(JSON.stringify(cases.map(r=>{const trace=Array.from({length:r.steps},(_,n)=>({tick:n+1,chapter:'one',regime:'fixed',state:{density:.4}}));const s=m.traceMetrics(trace,r.events,r.steps);return {id:r.id,structure:s,gate:m.assess({finite:true,peak:.01,rms:.01},s)};})));"
        result=json.loads(subprocess.check_output(['node','-e',script],input=json.dumps(cases),text=True,cwd=review.ROOT))
        by_id={r['id']:r for r in result}
        self.assertFalse(by_id['CONTROL/ostinato']['gate']['eligible'])
        self.assertTrue(by_id['CONTROL/duration-jitter']['gate']['eligible'])
        jitter=review.diagnose(cases[1])['diagnostics']
        self.assertEqual(jitter['millisecondDurationInstrumentPhrasePatterns'],2)
        self.assertEqual(jitter['pitchRhythmPhrasePatterns'],1)

    def test_insufficient_context_and_unknown_harmony_abstain(self):
        row=next(r for r in review.controls() if r['id']=='CONTROL/single-phrase')
        row['chords']=None
        result=review.diagnose(row)
        self.assertEqual(result['diagnostics']['completePhrases'],1)
        self.assertIsNone(result['diagnostics']['explicitHarmonicChanges'])
        self.assertTrue(any('under-observed' in flag for flag in result['flags']))

    def test_published_job_recovers_and_replay_rejects_tampering(self):
        root=review.ROOT/'.score-lab/tests';root.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as tmp:
            directory=Path(tmp)
            manifest=dict(version=review.VERSION,sources=review.sources(),rows=review.controls()[:2],sourceReportSha256='TEST_ONLY',skippedWaveformControls=9)
            raw=lab.encode(manifest);lab.atomic(directory/'experiment.json',raw)
            lab.atomic(directory/'state.json',lab.encode(dict(manifestSha256=lab.sha(raw),status='created',jobs={},renderer=None,judgeIdentity=None)))
            def crash(stage,key):
                if stage=='after_result_publish':raise KeyboardInterrupt('TEST ONLY')
            with self.assertRaises(KeyboardInterrupt):review.run(directory,crash)
            review.run(directory);before=(directory/'report.json').read_bytes();state=lab.read(directory/'state.json')
            review.run(directory);self.assertEqual(before,(directory/'report.json').read_bytes())
            self.assertTrue(all(len(j['attempts'])==1 for j in state['jobs'].values()))
            job=next(iter(state['jobs'].values()));path=directory/job['result'];path.write_bytes(path.read_bytes()+b' ')
            with self.assertRaises(ValueError):review.run(directory)


if __name__=='__main__':unittest.main()
