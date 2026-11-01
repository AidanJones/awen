"""Theory-derived score diagnostics, not learned or human quality labels."""
import copy
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import symbolic_critic as critic
import score_lab as lab


def note(step,midi,layer=2,duration=.4):return dict(step=step,midi=midi,layer=layer,duration=duration)


class SymbolicTests(unittest.TestCase):
    def test_resolution_is_conditional_on_explicit_chords(self):
        events=[note(0,60),note(1,62),note(2,64)];chords=[[0,4,7]]*8
        r=critic.evaluate(events,8,chords);self.assertEqual(r['metrics']['nonChordMelodyNotes'],1);self.assertEqual(r['advisoryScores']['ornamentResolution'],1)
        bad=critic.evaluate([note(0,60),note(1,66),note(2,71)],8,chords);self.assertEqual(bad['advisoryScores']['ornamentResolution'],0)
        unknown=critic.evaluate(events,8);self.assertIsNone(unknown['advisoryScores']['ornamentResolution']);self.assertFalse(unknown['coverage']['waveformRead'])

    def test_style_changes_leap_advice_and_phrase_boundaries_break_lines(self):
        events=[note(0,60),note(1,72)]
        self.assertEqual(critic.evaluate(events,8,style='lyric')['advisoryScores']['melodicEconomy'],0)
        self.assertEqual(critic.evaluate(events,8,style='figured')['advisoryScores']['melodicEconomy'],1)
        self.assertIsNone(critic.evaluate([note(31,60),note(32,84)],64)['advisoryScores']['melodicEconomy'])

    def test_chord_attacks_are_clustered_and_polyphonic_melody_abstains(self):
        r=critic.evaluate([note(0,48,0),note(0,60,1),note(0,64,1),note(0,67,2)],8)
        self.assertEqual(r['metrics']['notesPerSecond'],4*r['metrics']['attacksPerSecond'])
        poly=critic.evaluate([note(0,60),note(0,64),note(1,62)],8,[[0,4,7]]*8)
        self.assertFalse(poly['coverage']['monophonicMelody']);self.assertIsNone(poly['advisoryScores']['melodicEconomy']);self.assertIsNone(poly['advisoryScores']['ornamentResolution'])

    def test_repetition_is_reported_without_a_universal_penalty(self):
        events=[note(bar*8+slot,midi) for bar in range(4) for slot,midi in [(0,60),(2,64),(4,67)]]
        r=critic.evaluate(events,32);self.assertEqual(r['metrics']['uniqueContourBars'],1);self.assertEqual(r['metrics']['adjacentContourRepeatFraction'],1)
        self.assertNotIn('quality',r['advisoryScores']);self.assertFalse(r['humanPreferenceValidated'])
        empty=critic.evaluate([],8);self.assertTrue(all(v is None for v in empty['advisoryScores'].values()))

    def test_bounds_and_nonfinite_notes_are_rejected(self):
        for e in [note(-1,60),note(9,60),note(1,128),note(1,60,duration=float('nan')),note(1,60,layer=True)]:
            with self.assertRaises(ValueError):critic.evaluate([e],8)
        with self.assertRaises(ValueError):critic.evaluate([note(0,60)],8,[[0,99,7]]*8)

    def test_published_symbolic_result_recovers_and_replay_checks_hash(self):
        root=critic.ROOT/'.score-lab/tests';root.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as tmp:
            directory=Path(tmp);row=dict(id='TEST_ONLY',events=[note(0,60),note(1,62),note(2,64)],steps=8,chords=[[0,4,7]]*8,style='lyric',profile='neutral',traceSha256='TEST_ONLY',originalGate={'eligible':True})
            manifest=dict(version=critic.VERSION,sources=critic.sources(),rows=[row],sourceReportSha256='TEST_ONLY',skippedControls=0,controlReason='TEST_ONLY',profileInterpretation='TEST_ONLY')
            raw=lab.encode(manifest);lab.atomic(directory/'experiment.json',raw);lab.atomic(directory/'state.json',lab.encode(dict(manifestSha256=lab.sha(raw),jobs={},status='created',renderer=None,judgeIdentity=None)))
            log=lab.Invocation(directory)
            try:
                engine=critic.Engine(directory,log)
                def crash(stage,key):
                    if stage=='after_result_publish':raise KeyboardInterrupt('TEST ONLY')
                engine.fault_hook=crash
                with self.assertRaises(KeyboardInterrupt):engine.drive()
                engine=critic.Engine(directory,log);a=engine.drive();b=engine.drive();self.assertEqual(a,b)
                state=lab.read(directory/'state.json');job=next(iter(state['jobs'].values()));self.assertEqual(len(job['attempts']),1)
                result=directory/job['result'];result.write_bytes(result.read_bytes()+b' ')
                with self.assertRaises(ValueError):critic.Engine(directory,log).drive()
            finally:log.close()


if __name__=='__main__':unittest.main()
