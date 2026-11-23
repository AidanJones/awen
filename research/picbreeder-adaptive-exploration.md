# Picbreeder and more distinct musical offspring

23 November 2026. The user requests larger future differences when a comparison
sounds too similar, revisiting Picbreeder as the interaction model. This is a
source review and implementation rationale. The [adaptive explorer](adaptive-exploration.md)
now implements the bounded first prototype; listener distinctness remains unmeasured.

## What the primary sources support

The [Secretan et al. system paper](https://www.campbellssite.com/papers/secretan_ecj11.pdf)
describes subjective selection of appealing offspring, using selected individuals
as parents, and branching from published ancestors. It treats exploration as
finding interesting possibilities, rather than optimising toward one prescribed
artifact. Its representation can grow through NEAT, enabling structural changes;
it is not restricted to tiny adjustments in a fixed parameter vector. The
paper also discusses user fatigue and limitations, so image-domain success does
not establish an effective music workflow.

The [project interface and breeding tips](https://picbreeder.net/) encourage
selecting parent(s), evolving, saving and branching. They describe following
useful regularities and discovering transformations between different kinds of
images. For Awen, preserving an interesting musical identity while exploring
different treatments is a useful analogy. Automatic widening after similarity
feedback is **our proposed adaptation**, not an algorithm verified as a feature
of original Picbreeder.

## Previous support and limitation

Awen already has parent selection, pins, deterministic generations, previous
rounds and backups. The [nine-card explorer](nine-direction-exploration.md)
started with authored structural/palette differences, but its descendants changed
two numeric traits and preserved the parent's palette, recipe and harmony. Thus
many further generations could stay within one narrow musical neighbourhood.
The recent controlled form comparison intentionally held the material fixed;
it was a diagnostic, not an appropriate response to a request for much greater
stylistic variety.

## Implemented prototype behaviour

- Keep selection simple: choose a card/parent, or A/B for a focused comparison.
  No explanation is required.
- Add **More different options** as an explicit search action. Preserve it as
  similarity/search feedback, separate from an overall tie or dislike. Equally
  enjoyable but distinct music should not automatically trigger wider mutation.
- Retain the favourite unchanged and branch from it. For the first single-parent
  prototype, nine cards can contain the favourite, two close relatives, three
  medium departures and three broader alternatives. These counts are a proposed
  design to test, not a finding from Picbreeder.
- Broader offspring should alter meaningful musical choices: phrase recipe,
  rhythmic organisation, space/rests, bass/support roles, harmonic treatment or
  instrumentation. Merely increasing volume, onset count or microscopic pitch
  jitter is not useful diversity. Keep signal limits and level matching intact.
- Widen after explicit similarity feedback; let a selected direction become a
  parent for closer refinement again. Preserve other pins, lineage, seed,
  round history, replay and undo. Multiple selected parents should retain their
  identities rather than being averaged into one musical genome.
- Use bounded symbolic differences and duplicate checks to avoid obviously
  identical cards. Those checks cannot guarantee audible distinctness; the
  listener still decides. Do not maximise a novelty or CLAP score as quality.

This search can remain model-free in the browser. It does not require adopting
NEAT wholesale, a neural generator, a large dataset or an LLM during playback.
Wider previews are explicit exploration choices; ordinary reading must retain
the existing within-chapter continuity policy.

## Small next proof

Use one preserved favourite and one passage first. Ask for more different
options, generate a source-bound nine-card branch and verify that the parent
is unchanged, offspring cover multiple authored musical choices, levels remain
bounded, and reload/undo/backups reproduce the round. Then ask only for a card
number, none, or more difference. Persist the action and actual generated
differences, without inventing fit/comfort labels. Avoid repeating tiny form
ablations in response to the user's request for greater contrast.

Implementation is documented under `awen-syq.2.6`; coordinate richer structural mutation
with existing `awen-3fr.3`. The [latest listener observation](form-listener-feedback.json)
is perceived similarity with no passage specified; it is not two fabricated
trial ties. The [seeking fix](review-seeking-proof.json) also matters: the
listener must be able to reach the differing sections before comparisons are
treated as reliable evidence about perceptual difference.
