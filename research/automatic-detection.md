# Automatic dictionary detection

Implemented 3 November 2026, task `awen-xfp.8`. Dictionary v0.3.0 now drives a
bounded local rule detector for all 28 categories. The reader still runs from
one HTML file, with no model, network request or required build step. This is
an explainable heuristic implementation, not an independently validated classifier.

## Text to labels to music

`detectNarrative` combines each dictionary entry's lexical cues with declared
additional aliases and ambiguity rules in `narrative-dictionary.json`. It keeps
multiple labels, exact matched text spans, supported/rejected/uncertain state,
event scope, a coarse experiencer and the rule responsible. Text offsets are
JavaScript UTF-16 offsets. Unknown experiencers remain unknown; named-character
tracking and general irony understanding are not implemented.

Negation uses a bounded local token window, reset at clause contrasts. Recall
and conditional markers apply to the affected clause; explicit opening memory
frames can extend within a paragraph. Current speech remains separate from a
recalled event inside it. For example, “She asked how he had escaped years ago”
supports current conversation and recalled pursuit. It does not request a chase.
Quotation and temporal scope remain fallible, especially in nested narration,
free indirect speech and long-distance negation.

Weak cues remain uncertain: “wonder whether”, “storm of applause”, searching
for shelter, tears of joy, isolated “excellent” and metaphorical cold do not
automatically establish their corresponding musical label. Comic framing around
supported physical impact has a specific inspectable rule, so the Rat safe-drop
passage can carry action and humour together. These rules are original Awen
adaptations; the cited literature does not validate their exact vocabulary.

Chapter boundaries require parsed document metadata. Continuation needs both
its lexical cue and same-chapter metadata. Blank or unmatched text does not
force all categories into a decision. The detector accepts up to 30,000 characters,
limits occurrences/evidence per category and uses bounded clause windows. These
bounds prevent pathological repeated-word paragraphs from creating unbounded work.

The 28 categories are not 28 new musical engines. Supported current labels map
to the existing six scene states and to dictionary musical-direction options.
Negated, uncertain and non-current action is excluded from automatic action
decisions. The legacy six-scene fallback remains for unmatched text; remembered
action suppresses the legacy action fallback and action-expression contribution.
Current action, threat and revelation can supply bounded expression floors.

Dictionary option priority is an authored routing policy, not calibrated
confidence or a quality score. Comic danger can select a concertino direction;
grief can select an elegy; dialogue, cold, shelter and other cues have their
existing alternatives. Ordinary scene changes retain dwell/bar-boundary rules.
Classical expression is smoothed; recipe changes still require chapter mode,
a changed chapter and the existing four-bar boundary. Fixed recipes and Steady
ambience retain their restrictions. Tempo stays 72 BPM, and automatic detection
does not replace the user's palette or chosen harmony.

The development native renderer and newly generated explorer pages now use the
same dictionary-adjusted targets as the reader. Historical rendered experiments
and frozen explorer pages retain their original sources and outputs.

## Inspect and correct

**Behind the soundtrack → Scene & musical direction** displays all supported
labels, then individual evidence with scope/state. Playback status distinguishes
the actual musical state from current paragraph cues. **Use estimate as a starting
point** copies only current playable labels into the personal interpretation form.
It records `accepted-rule-estimate` provenance; it does not create independent
study annotations. Manual comparison/keep/undo, chosen chords, palette, separate
interpretation downloads and musical profile exports continue to work.

Dictionary-version changes leave older interpretation records available in the
download but ask the user to select labels again instead of silently reapplying
old meanings. Existing musical profiles and reading progress remain compatible.

## Engineering evidence

The [proof](automatic-detection-proof.json) binds the implementation, tests and
matched-book audit. Six focused regression groups cover reachable rules for all
28 labels, metadata-only structure, negation/actuality, ambiguity, exact Unicode
spans, deterministic bounded work, the Rat safe drop and chapter/fixed-policy
continuity. These are authored controls, not independently collected labels.

The isolated Playwright check verifies visible Rat labels, actual playback,
continuous graph/navigation, Steady ambience, accepted-estimate provenance and
reload. It also renders real native evaluator audio with the adjusted target
path and checks its sample ceiling. The full audio and evolution browser suites
passed. None of those checks establishes artistic fit or reading benefit.

The audit compares unchanged book editions against commit `b02e461`, assuming
sequential reading. On the 883 Rat paragraphs, six-state request counts changed:

| State | Earlier rules | Dictionary rules |
|---|---:|---:|
| Caper | 68 | 52 |
| Dialogue | 360 | 388 |
| Chase | 74 | 83 |
| Reflective | 361 | 302 |
| Discovery | 7 | 19 |
| Suspense | 13 | 39 |

Twenty-two different current-cue labels occur under the new rules in Rat.
These counts describe detector output; they are not accuracy, balance targets
or evidence that adding labels improves music. No thresholds were fitted to
independent holdouts. The four-book audit scans the existing 4,351 paragraphs,
creates no new audio and caches one checksum-bound result per book.

```powershell
python tools/compile_narrative.py --check
node --test tests/detection.test.cjs
node tools/audit_detection.cjs NEW_DIRECTORY
node tools/audit_detection.cjs --resume EXISTING_DIRECTORY
```

Audit runs freeze current/baseline/code identities and use atomic per-book
results, unique invocation logs and a writer lock. Resume reuses verified books
and can recover results published before state commit. Changed sources or
corrupt results are rejected; completed replay preserves report bytes.

Independent annotation and empirical tuning remain open in `awen-xfp.1` and
`awen-xfp.2`; broader viewpoint/context work remains in `.3`. More output variety
is not a substitute for those gates. Music-quality, preference and comfort
evaluation remain separate from these text-rule estimates.
