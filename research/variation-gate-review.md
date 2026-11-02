# Variation gate: distinguish the evidence before changing the rule

Read-only engineering review, 2 November 2026, task `awen-3fr.6.2.3.7.1`.
The parent variation-policy task remains open for independent listening and
threshold calibration. This review changes no gate, runtime default, archived
eligibility or learned reward.

## What the existing rule measures

`tools/score-lab-metrics.cjs` requires at least two distinct complete four-bar
event sequences. Its signature includes onset slot, layer, MIDI pitch, duration
rounded to milliseconds and instrument. It excludes the continuous bed and
acoustic rendering. This is exact symbolic difference, not a validated measure
of perceived monotony. A clip with only one complete phrase cannot meet a
two-pattern criterion, regardless of its intended form.

`tools/variation_review.py` separates descriptive facets: complete-phrase
coverage, duration/instrument-sensitive signatures, pitch/onset signatures,
layer-relative contours, the shortest exactly repeated grid cell, distinct
pitches, onset slots and explicit chord-set changes. It does not combine them
into a quality score or impose a new repetition penalty. Layer-relative contours
do not establish independent voices. Instrument/duration differences can matter
musically; reporting them separately does not declare them irrelevant.

## Verified archived observations

The original completed symbolic archive supplies 18 scheduled traces and their
explicit harmonic plans. The importer checks its manifest/state and all job
input/result checksums. It does not reconstruct old harmony using today's
changed reader or reinterpret the old renderer. Nine waveform-only silence/
level/loop controls remain excluded: they have no corresponding transformed
symbolic score. These traces cover their full saved schedule, not necessarily
the exact cropped audio interval.

All six original storm/spring rejections have:

- Two complete four-bar phrases with the same exact note pattern.
- Seven distinct scheduled pitches in that complete-phrase window.
- A shortest exact grid period of 32 slots: the four-bar pattern repeats.
- Seven explicit chord-set changes in the full saved harmonic plan.

Storm uses 64 distinct onset slots in the complete-phrase window; spring uses
30. The historical gate's rejection reason is solely “insufficient symbolic
variation”. These observations explain why literal phrase uniqueness cannot
distinguish all intended musical treatments. They do not establish that listeners
prefer any rejected score, nor that every repeated four-bar phrase should pass.

## Authored notation controls

| Control | Descriptive result / what it tests |
|---|---|
| Three-pitch ostinato | Repeated eight-slot cell; one four-bar pattern. Repetition can be intentional, but no preference is assumed. |
| Single-pitch short cell | Repeated two-slot cell; also one four-bar pattern. The scalar phrase count treats this and the ostinato alike. |
| Ostinato with 2 ms duration difference | Two duration-sensitive phrase signatures but one pitch/onset pattern. A unit test runs the actual legacy gate with an explicitly synthetic valid signal: this variant passes while the unchanged ostinato fails. No audibility or rendered-audio claim is made. |
| Transposed figure with changed harmony | Two absolute pitch patterns, one relative contour and one chord-set change. Reused contour need not imply unchanged harmony. |
| Single phrase | Between-phrase variation is under-observed; the diagnostic flags limited coverage. |
| Sparse line | Two differing patterns with few notes. A higher uniqueness count alone does not establish an engaging score. |
| Empty score | No positive quality conclusion; there is no overall score to reward silence. |

These are seven developer-authored notation controls. The short-cell example is
not a symbolic transcription of the previous two-second waveform-loop control.
No new audio or listening dataset was created. The earlier
[Audiobox probe](audiobox-probe.md), where production quality preferred loops,
is separate acoustic evidence for keeping evaluator axes distinct.

## Reproduce and recover

```powershell
python tools/variation_review.py start --source COMPLETED_SYMBOLIC_ARCHIVE
python tools/variation_review.py resume PRINTED_EXPERIMENT_DIRECTORY
python -m unittest discover -s tests -p test_variation_review.py -q
```

The [proof](variation-review-proof.json) binds 18 archived traces, seven controls
and 25 journalled jobs. Runs use timestamp/UUID directories, immutable inputs/
sources, unique invocation/attempt logs, atomic state and a writer lock. Published
results recover after interruption. The audited completed replay rejects any
waveform open, preserves the report and adds no attempts. Tests also cover
actual legacy gate behaviour, unknown harmony, limited context, recovery and
corrupt-result rejection. Archived source identities remain recorded separately
from current analysis code.

## Next acceptance gate

Collect separate listener judgements for useful recurring material, unwanted
repetition and reading distraction across styles and longer excerpts, including
ties. Freeze comparisons and reserve seeds/styles before evaluating a new
policy. Evaluate harmonic movement and texture alongside recurrence; treat
physical output, invalid audio and continuity requirements separately from
style-dependent variation evidence. No numeric threshold has been selected from
these authored controls. The parent task remains open; multi-critic optimisation
must not silently treat this engineering audit as preference validation.
