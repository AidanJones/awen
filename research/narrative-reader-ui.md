# Narrative research in the reader

Update 3 November 2026: [dictionary v0.3.0 automatic detection](automatic-detection.md)
now supplies multiple rule-estimated labels and scoped evidence to this panel.
The v0.2.0 engineering proof below remains its historical implementation snapshot;
the personal interpretation/audition contract continues alongside automatic cues.

Implemented 2 November 2026, dictionary version 0.2.0. Open **Behind the
soundtrack → Scene & musical direction** in the reader. The single HTML embeds
the dictionary and all UI logic; no network fetch, build step or runtime model
is needed. The authoring helper `python tools/compile_narrative.py --check`
checks that the embedded dictionary matches the canonical research file.

## What the reader offers

The existing six-scene rule estimate and matched phrases are shown separately
from your interpretation. The estimate is explicitly described as an unvalidated
guess. You can accept it as a starting point or select any combination of the
28 dictionary labels, with current/recalled/hypothetical/unknown event context
and an optional note. Accepting a rule estimate retains that provenance; editing
labels records a personal interpretation. No new automatic text detector or
classifier accuracy claim is introduced.

The panel offers unranked musical alternatives with their source-scoped
rationales. Recalled/hypothetical/unknown action does not produce current-action
music proposals. These are passage-level personal controls; unlike the Python
annotation contract, they do not annotate separate clauses with individual
holders, uncertainty judgements and exact evidence spans. That remains an
independent annotation/detector task. The existing phrase evidence is shown
without presenting it as independently verified annotation.

**Compare this direction** enters the existing audition gallery with your
current music as the first candidate and up to five dictionary alternatives.
The clicked alternative comes first after the current candidate. Nothing is
kept automatically: listen, then keep, or cancel/choose the current score.
Previewing pauses reading music and preserves its snapshot; keeping leaves it
paused until Start. This explicit user choice uses the existing gallery workflow,
not an automatic mid-chapter structural switch. Automatic chapter development
still uses its existing phrase-boundary policy.

Your palette and numeric listening preferences are retained. Existing chosen
chords take priority by default; uncheck that option to audition the proposed
harmonic family instead. You can hold a kept recipe, follow expression gently,
or develop between chapters. A kept gallery choice records interpretation and
option provenance in profile history; standard export/import and undo retain it.
If subsequent numeric exploration is kept, its exact dictionary option is not
claimed unless the candidate still carries that identity.

**Keep current music** changes no score. The panel explains that repeated
figures can be useful and that experimental audio judges disagree about loops.
Those judges do not rate or choose music during reading; the link to the
[Audiobox measurements](audiobox-probe.md) is for inspecting development evidence.

## Storage and compatibility

Personal interpretations use a separate `awen.narrative.v1` local-storage key,
bounded to 120 passage records and keyed by book revision/paragraph. They do not
become listening votes, independent study labels or classifier truth. Notes are
plain text, limited to 240 characters. **Download my interpretations** exports a
separate JSON file marked with that provenance. A musical profile includes only
the interpretation attached to a kept choice, not the whole interpretation store.

Navigating restores each passage's interpretation. A changed dictionary version
requires selecting labels again rather than silently reinterpreting an older
record. Storage failures retain an explicit download path. Old profiles still
normalise; invalid optional interpretation metadata is discarded while ordinary
musical history remains available. Palette, seed, book position, chapter control,
limiter and emergency mute retain their previous behaviour.

## Engineering evidence and remaining tasks

The [proof](narrative-ui-proof.json) binds the reader/dictionary/test sources.
Unit checks cover exact embedding, alternatives/scope, compiler-compatible
recipes, retained/replaced harmony and profile provenance. Isolated Playwright
checks actual preview/keep/undo, palette retention, export/reload, per-passage
storage, silent startup and dark mobile layout. The required audio and evolution
browser regressions also passed, including native rendering and output/mute checks.
These are engineering checks, not listener or classifier validation.

Independent annotation, better context detection and held-out classifier tuning
remain under `awen-xfp.1`, `.2` and `.3`. This UI completes the bounded inspector/
personal-choice integration strand of `.5`; it deliberately does not turn a
source-informed dictionary into automatic ground truth. The next critic task is
the style-dependent variation-gate review before multi-critic optimisation.
