# Learned feedback for multi-objective score evolution

Design update: 1 November 2026. **Proposed experiment, not an executed reward
comparison.** No new model, training run or preferred runtime score is claimed.
Models remain development-only; the browser keeps the bounded native renderer.

## What holds the current feedback back

The [grid pilot](grid-clap-evolution.md) increased CLAP association without
improving action-versus-reflection specificity. Silence beat musical candidates
under a check description, and wording/windows changed conclusions. In the
[five-clip comparison](muq-comparison.md), silence exceeded 2/5 CLAP target means
and 5/5 MuQ target means. These are local diagnostics, not general model accuracy.

CLAP retrieval similarity does not supply separate enjoyment, continuity or
reading-comfort judgements. Literary paragraphs are not music captions; irony,
perspective and dramatic function need more than literal noun overlap. Current
short windows also cannot establish a coherent chapter arc. Increasing search
pressure can exploit those weaknesses. Numeric evolution changes six traits
while retaining recipe/palette; it cannot invent a new chord grammar. The new
classical families widen selectable starting material but have not been evaluated
by the earlier embedding experiments.

## Candidate ML signals checked against primary sources

- [TuneJury](https://github.com/yonghyunk1m/TuneJury): a learned pairwise music
  preference reward using frozen audio/text representations. Its full model is
  a candidate alternative to raw cosine, not an established scene-fit judge for
  prose. The [checkpoint guide](https://github.com/yonghyunk1m/TuneJury/blob/main/checkpoints/README.md)
  separately describes an audio-only head. Those heads require their specified
  encoders; our cached general-CLAP or MuQ vectors cannot be substituted merely
  because dimensionality matches. Exact head/encoder revisions, dependencies,
  preprocessing, weight licences and hashes need preflight before inference.
- [Audiobox Aesthetics](https://github.com/facebookresearch/audiobox-aesthetics):
  released predictor with content enjoyment, content usefulness, production
  complexity and production quality outputs. Enjoyment/quality offer independent
  candidate audio-only signals. Complexity is a diagnostic, **not** an annoyance
  score: automatically rewarding less complexity could favour a static drone
  or silence. Usefulness is not literary scene fit. No Awen inference has run.
- [Audio-language judge probes](https://arxiv.org/abs/2610.13247) motivate testing
  actual audio dependence, swapped audio, pair order and rubric wording. An
  audio-capable judge could provide separate fit/coherence/estimated-distraction
  labels during development, but those are model opinions, not listener comfort.

These are source-informed candidates rather than a recommendation to install
every model. Start with one audio-only learned evaluator, keeping CLAP as an
existing baseline; then test the learned text/audio preference alternative if
the first controls are useful. Do not train a fresh joint encoder first.

## Reward vector and search policy

| Axis | Candidate signal | Interpretation |
|---|---|---|
| Scene support | Independent dramatic-function briefs; compare CLAP margins with a learned text/audio preference reward | Fit hypothesis, requiring scene-shuffle and wording controls |
| Musical enjoyment | Audio-only learned preference/aesthetic model | Generic musical appeal proxy, not personal taste |
| Low distraction | Initially an explicitly named audio-judge estimate; later a small ranker over frozen audio features and actual separate distraction judgements | Estimated intrusiveness until calibrated with a reader |
| Continuity/development | Existing chapter/reset/slew/onset constraints, plus longer-clip model judgements where supported | Hard constraints plus a separately reported coherence estimate |

Keep finite samples, output bounds, an audible reference level and chapter-only
large automatic changes as hard gates. A model score cannot compensate for a
failed gate. Retain the objective vector and uncertainty rather than averaging
unrelated cosine/MOS values. Use Pareto selection: preserve candidates where no
other candidate is at least as good on every calibrated objective and better
on one. Show trade-offs to the listener rather than declare one universal winner.
Any later weighted scalar must use declared calibration and fixed weights.

A multi-objective genetic search is the first implementation target. The
renderer is a small black-box parameterised generator and already supports
seeded mutations and native renders. RL adds complexity without repairing a
bad reward. Consider it later only if sequential chapter decisions need a
trained policy and the objectives pass controls. Structural recipe/cycle
mutations need their own parser, continuity and lineage checks before expanding
the numeric search.

## Bounded next probe

1. Preflight one released audio-only learned evaluator in an isolated environment.
   Pin artifacts and confirm actual CPU/hardware needs before installing large
   encoders. Reuse existing audio when compatible; no reference corpus collection.
2. Freeze three contrasting passages and four diverse existing directions each
   (12 candidate clips). Use matched seed, reference level and windows. Add
   silence, static/busy repetition, level and scene-shuffle controls; controls
   are diagnostic and never adopted as musical winners.
3. Score the same WAVs with CLAP and the new evaluator, retaining every axis,
   window and raw result. Check whether quality scores distinguish clearly
   degraded variants and whether scene scores change with the passage. Do not
   call those engineered contrasts human preference labels.
4. Only after useful controls, run a tiny Pareto search and replay finalists on
   a fresh seed and unused brief wording. Inspect which dimension actually
   improves and whether candidates exploit near-silence, brightness or repetition.
5. Collect a few separate enjoyment/fit/distraction choices to test transfer and
   personalise a small ranker. The initial learned signals can run without
   these labels; claims of personal comfort or accuracy cannot. Split by scene
   or work, report uncertainty and keep actual listening provenance.

Use the existing [resumable bridge](score-lab-python.md): unique experiment and
attempt logs, pinned source/model identities, atomic checkpoints, verified
caches and explicit ambiguous-call recovery. Emit no synthetic listener votes.
The [judge contract](score-lab-judge.md) already separates the three audio-judge
dimensions, but connecting a real model and Pareto evolution remain open work.
