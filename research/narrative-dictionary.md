# Narrative labels and musical alternatives

Research and implementation: 2 November 2026. The canonical
[dictionary](narrative-dictionary.json), version 0.3.0, contains 28 proposed
labels in seven dimensions and 12 musical alternatives. It reconciles the
existing runtime scenes, harmonic scene functions and classical cues.
It supplies a [local automatic rule detector](automatic-detection.md), a Python
annotation-to-music mapper and a [manual reader panel](narrative-reader-ui.md).
It is not a trained or independently validated model or a validated music reward.
Version 0.1.0's original mapping proof remains historical; v0.2.0 added manual
reader integration and v0.3.0 adds inspectable automatic detection.

## What the sources support

| Source and reviewed scope | Observation / Awen use |
|---|---|
| Eerola, Friberg and Bresin (2013), [original experiment](https://pmc.ncbi.nlm.nih.gov/articles/PMC3726864/), abstract, cue definitions and Discussion | Tested changes in musical cues affect perceived emotional character. Their operational activity/tempo measure uses non-simultaneous onsets. Awen separates musical features and tests activity at its unchanged 72 BPM; exact narrative labels and target ranges are our proposals. |
| Zentner, Grandjean and Scherer (2008), [original study abstract](https://pubmed.ncbi.nlm.nih.gov/18729581/), abstract only | Perceived and felt musical response differ and depend on preference. Narrative tone, musical expression, enjoyment and reader distraction therefore remain separate evaluation records. We do not implement or claim to validate the GEMS scale. |
| Niederhoff, [Perspective—Point of View](https://www-archiv.fdm.uni-hamburg.de/lhn/node/26.html), definition and opening Explication | Narrative representation depends on narrator/character position and values. Awen records the experiencer and event scope. This is theoretical motivation, not an NLP method for detecting irony. |
| Speer, Zacks and Reynolds (2007), [original experiment abstract](https://pubmed.ncbi.nlm.nih.gov/17576286/), abstract only | Situation/goal changes can mark narrative event boundaries. Awen annotates these separately from paragraphs. Restricting large musical changes to chapter/phrase boundaries is our conservative policy, not a result of that study. |
| Lee (2025), [original analysis](https://www.mtosmt.org/issues/mto.25.31.2/mto.25.31.2.lee_jason.html), abstract and introduction 0.1–0.3 | Harmonic conventions can serve wonder or comic mockery in context. Awen offers alternative treatments instead of assigning a compulsory chord to an emotion. |
| Houston, [first-hand theatre interview](https://www.marintheatre.org/press-release-details/239/interview-with-sound-designer-composer-and-musical-director-chris-houston-web-exclusive), script/underscoring questions | Speech can occupy the melodic foreground. Leaving musical space during reading is a candidate adaptation, not direct evidence of reading benefit. |

The seventh source record links the existing [classical review](classical-inspiration.md)
and its work-specific references. Environmental suggestions draw on that scoped
catalogue; no new score transcription was undertaken. Every definition, example,
lexical signal and exact mapping is marked `awen-proposal`. `sourceIds` identify
conceptual motivation, not validation of the individual label.

## The seven dimensions

| Dimension | Labels |
|---|---|
| Dramatic function | pursuit, anticipation, confrontation, revelation, conversation, reflection, aftermath, intrigue |
| Activation | high-activation, low-activation |
| Tone | threat, wonder, grief, humour, tenderness, release |
| Viewpoint | ironic-framing, character-interior |
| Event time | recalled-action, hypothetical-action, current-action |
| Environment | cold-exposure, shelter, open-landscape, severe-weather |
| Structure | chapter-boundary, situation-change, continuation |

Labels may coexist: a scene can be active, dangerous and comic; reflection need
not be sad; a landscape can contain grief. Each entry includes a definition,
positive/counterexample, illustrative aliases, contextual/negation guidance,
uncertainty guidance, source references and musical option references.
Aliases remain annotation aids. Version 0.3.0 also uses them with explicit
additional cues, negation/scope handling and ambiguity guards in a local detector;
literal keyword presence is not treated as independent ground truth.

Reconciliation is explicit: runtime `chase` maps to `pursuit`, `dialogue` to
`conversation`, `discovery` to `revelation`, and so on. Classical `storm` offers
both severe weather and confrontation interpretations; this crosswalk does not
automatically assert both. Neutral means no new label rather than forced calm.

## Musical alternatives and constraints

The 12 options reference existing classical presets and harmonic families, with
separate calm/neutral/active critic profiles. For example, pursuit can suggest
driving motion or lighter concertino motion; revelation can suggest open modal
figuration or a more conspicuous third-related colour. These are unranked
experiments, not preferred answers or prescribed emotion-to-chord rules.

The validator checks texture, articulation gate, harmonic hold, phrase shape and
figure against the actual production DSL compiler. Those feature records describe
the preset **before** a harmony override. Register remains compiler bounded;
tension is a contextual harmonic hypothesis, not a validated scalar. Current
features and proposed tension/rest extensions have separate status.

Tempo remains 72 BPM. More movement means different note activity/articulation,
not tempo acceleration. Structural proposals retain chapter-only commitment at
the next 32-step phrase; expression changes must be smoothed. User palette choice,
continuity, repeated figures and the output limiter retain their existing policy.
The Python mapper itself schedules or plays nothing. The reader panel offers
explicit auditions through the existing gallery, with no automatic adoption.

## Supplied annotations, not classifier predictions

`tools/narrative_dictionary.py` validates the library and maps explicit records.
A record supplies `id`, `text`, `provenance` and `annotations`. Each annotation has
a label ID, `state` (`supported`, `rejected`, `uncertain`), `eventScope` (`current`,
`recalled`, `hypothetical`, `unknown`), `holder` and an exact evidence span.
Text spans use Python Unicode character offsets and must match the quoted text;
browser integration must convert UTF-16 offsets explicitly. Optional preceding
context is separately identified. Chapter-boundary support requires document
metadata, not a text match on the word “chapter”. See the
[15 example records](narrative-dictionary-fixtures.json) for the format.

Only supported current-event annotations generate music proposals. Recalled,
hypothetical and unknown event annotations remain visible but do not trigger
action music in this initial conservative policy. Scope is clause-specific: a
remembered chase does not suppress present dialogue elsewhere in the record.
A future intentional flashback-scoring mode could treat recalled action
differently; this version does not infer that decision.

Candidates retain supporting labels and source IDs. Shared alternatives are
deduplicated, never averaged into a quality score. Uncertain/rejected evidence
is retained with its exclusion reason. Empty evidence retains current music.
An explicit personal option is preserved independently of annotation agreement;
no candidate is automatically selected or adopted.

```powershell
python tools/narrative_dictionary.py validate
python tools/narrative_dictionary.py start
# Or supply a JSON array of records:
python tools/narrative_dictionary.py start --annotations RECORDS_JSON
python tools/narrative_dictionary.py resume PRINTED_EXPERIMENT_DIRECTORY
python -m unittest discover -s tests -p test_narrative_dictionary.py -q
```

Runs have timestamp/UUID directories, immutable source/input identities, journalled
jobs, unique invocation/attempt logs, atomic publication and a writer lock.
Published jobs recover after interruption. Source drift or corruption is rejected.
The [proof](narrative-dictionary-proof.json) records 15 matching authored controls,
an audited replay forbidding waveform opens, unchanged report bytes and zero new
attempts. These verify mapping and provenance behaviour; there is no classifier
accuracy, model inference, listening evaluation or independent annotation result.

## Holdouts and integration still to do

The fixture file records a **proposed, unannotated** whole-work split: Rat/Riders
for annotation development and Time/War for annotation holdout. Freeze revisions,
chapter IDs, context policy and independent labels before evaluating a detector.
Keep disagreement and uncertain labels. Hide model predictions and music choices
from annotators. These books have appeared elsewhere in Awen research, so this
is not an untouched end-to-end research holdout; a final benchmark needs newly
reserved material. No labels for those real passages are fabricated here.

The reader UI is implemented under `awen-xfp.5`; its personal storage contract
is documented [separately](narrative-reader-ui.md). Local automatic rules are
implemented under `.8`; independent annotation and empirical accuracy validation
remain separate work.

Existing tasks cover the remainder: `awen-xfp.1` independent annotation,
`awen-xfp.2` detector evaluation/tuning and `awen-xfp.3` viewpoint/context.
The completed manual inspector offers alternatives plus “keep current” while
preserving explicit user direction. Scene interpretation and actual musical
execution need separate tests. A future ML reward must be evaluated against
independent labels/listeners, not the predictions it is being trained to imitate.
