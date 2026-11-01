# Ordered critic work

1 November 2026. Beads holds live status. This sequence turns the recent
pretrained-model review and score-only prototype into small, reviewable tasks.
Finish and record each experiment before changing the next reward component.

| Order | Beads task | Deliverable / acceptance |
|---|---|---|
| 1 | `awen-3fr.6.2.3.4` | Controlled symbolic contrasts: resolving/unresolved ornaments, transposition, style, phrase boundaries, polyphony, activity, repeated figures and empty scores. Implemented; 14 fixtures and 17 expected relations pass. These are engineering expectations, not listener calibration. |
| 2 | `awen-3fr.6.2.3.5` | Stable voice identities and explicit chapter/epoch harmony. Record bed coverage; abstain where context is missing. Coordinate with existing versioned score representation task `awen-syq.4`. No counterpoint rules inferred from ambiguous layers. |
| 3 | `awen-xfp.7` | Literature-backed multi-label narrative dictionary with definitions, counterexamples, provenance, uncertainty and alternative musical targets. Reuse existing narrative tasks rather than duplicate them. |
| 4 | `awen-3fr.6.2.3.2` | Pinned pretrained evaluator: strict local load and CPU measurement, then a few existing WAVs and controls before all 27. Keep aesthetics distinct from scene fit and reading comfort. Metadata preflight exists; inference remains outstanding. |
| 5 | `awen-3fr.6.2.3.7` | Calibrate style-dependent variation gates against deliberate ostinatos and degenerate loops. Investigate the six rejected M0 storm/spring roots; retain original eligibility and reports. Threshold changes require evidence. |
| 6 | `awen-3fr.6.2.3.6` | Join verified symbolic and acoustic results by identity, inspect control failures, compare objective vectors/Pareto fronts, then at most one small generation if justified. Depends on voice coverage, dictionary, variation-gate review and real evaluator. |
| 7 | Existing `awen-3fr.6`, `awen-3fr.4`, `awen-r42` | Independent listener calibration, separate fit/enjoyment/distraction choices, held-out scenes/seeds and longer reading/device checks before promotion. |

The order is a working sequence, not a claim that model installation technically
depends on the dictionary. Only actual prerequisites are blocking Beads edges.
Richer mutation and RL remain later stages M5/M6 of the
[multi-objective roadmap](multiobjective-roadmap.md).

## First completed slice

`python tools/calibrate_symbolic.py start` freezes authored cases and expected
relations from [symbolic-contrasts.json](symbolic-contrasts.json). Each run has
its own timestamp/UUID directory, source-bound manifest, per-job journal and
unique invocation/attempt logs. Resume with:

```powershell
python tools/calibrate_symbolic.py resume EXPERIMENT_DIRECTORY
python -m unittest discover -s tests -p test_symbolic_contrasts.py -q
```

The [proof](symbolic-contrasts-proof.json) records the actual result. A resumed
completed run preserves the report and creates no new job attempts. Tests
interrupt after result publication and check recovery without duplication;
changed expectations and corrupt results are rejected. Failed expectations
remain visible and the CLI exits nonzero. No waveform or model is needed.

The thresholds have **not** been fitted to independent compositions or people.
Passing these authored contrasts establishes the implementation's intended
behaviour, not reward reliability. There is no overall quality score, runtime
gate change, personal-profile update or automatic promotion.
