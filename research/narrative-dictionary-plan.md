# Narrative classification dictionary — backlog `awen-xfp.7`

Requested 1 November 2026. **Specification for future research/implementation,
not a completed classification dictionary or a trained classifier.** Beads
tracks it under the narrative-interpretation epic `awen-xfp`.

## Reconcile what already exists

The runtime has six coarse scene IDs: caper, dialogue, chase, suspense,
discovery and reflective. The [harmonic library](scoring-knowledge.json) has a
separate scene-function vocabulary and aliases. The [classical library](classical-knowledge.json)
adds keyword cues for storm, pursuit, cold, shelter, grief, nature, dialogue and
wonder, with a neutral fallback. These are authored heuristics, not annotated
ground truth. The dictionary should reconcile them rather than add a third
incompatible set of labels.

## Research scope and shape

Review film/theatre scoring and narrative theory alongside music-emotion
research. Existing [source-scoped scoring notes](scoring-knowledge.md) and
[classical references](classical-inspiration.md) are starting material, not a
complete literature-backed ontology. Record exact reviewed sections and whether
a source is primary analysis, composer/practitioner evidence or a broader
theoretical proposal. Do not claim a cited study validates our exact mapping.

Represent independent, possibly coexisting dimensions:

- **Dramatic function:** pursuit/escape, anticipation, confrontation, discovery,
  explanation/dialogue, reflection, aftermath, tenderness or release.
- **Pace and activation:** movement, urgency, waiting, stillness; retain explicit
  uncertainty rather than force every paragraph into one categorical scene.
- **Tone and stakes:** threat, wonder, grief, humour, intimacy and comic danger.
- **Viewpoint and time:** narrator/character emotion, ironic framing, recalled
  action, hypothetical danger and present action. A quoted recollection is not
  necessarily a new chase cue.
- **Environment/programme:** cold, shelter, open landscape, weather or season
  where supported by context. A season alone should not prescribe an emotion.
- **Structure:** new chapter/scene, transition, continuation, resolution and
  ambiguity; larger musical changes still obey the musical boundary policy.

Each versioned entry should contain `id`, definition, synonyms/aliases,
positive and counterexamples, lexical/context/negation cues, co-occurrence rules,
uncertainty/abstention guidance, `sourceIds`, reviewed scope and evidence status.
Definitions and annotations must be separate from the runtime classifier output.

## Link classifications to executable musical choices

Store several alternatives per classification: tension/relaxation trajectory,
harmonic movement, register, rhythmic activity, articulation, texture, motif
development, rests and transition shape. State whether each trait is currently
supported by the engine or only proposed. For example, the current clock is
fixed at 72 BPM: “more urgent rhythm” must not be described as implemented tempo
acceleration. Keep instrument palette, compositional direction and listener
preferences independently selectable.

Every mapping needs a rationale, source scope, bounds, transition policy and
explicit status such as source observation, Awen adaptation or listener evidence.
Include counter-mappings: comic danger may need lightness rather than maximal
threat, and reflection need not be sad or static. Do not impose universal
emotion-to-chord rules or always maximise consonance.

## Acceptance gates

1. Small, source-linked, multi-label dictionary with traceable feature mappings
   and reconciliation of existing IDs.
2. Independently annotated fixtures covering negation, dialogue, irony, mixed
   tone, recalled action and boundaries, with book/chapter holdouts.
3. Separate tests for text classification, faithful musical execution and actual
   listener fit/comfort. Classifier labels must not become their own gold reward.
4. Inspector explanations show detected evidence, uncertainty and chosen musical
   alternatives. Rules or a small local classifier can run without a runtime LLM.
5. Export a compact versioned library only after scope and compatibility checks;
   preserve existing profiles, chapter continuity and explicit user choices.
