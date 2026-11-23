# Adventure arrangement listening pilot

23 November 2026. Implements the bounded comparison in `awen-syq.2.2`, following
the [Scrimshaw / iMUSE review](adventure-game-scoring.md). This is a development
experiment, not a new reader default or an adaptive transition engine.

## What is compared

Four native recordings cross two treatments with two passages from the embedded
Standard Ebooks edition of *The Stainless Steel Rat*:

- Chapter I, paragraph 3: the safe-drop caper previously discussed by the user.
- Chapter II, paragraph 1: the ride to the spaceport and philosophical reflection.

**Baseline** is the production persistent composer with its Classic starter.
**Arranged** is new original material described by a bounded development-only
JSON score: four named four-bar sections, an eight-slot figure per section and
an explicit chord plan. The form is A / answer / B / return. The reflection
relative retains its harmony and a subset of the melodic attacks, with longer
durations and fewer notes. Both end each section with melodic breathing space.
The first and last bars share tones; this is a symbolic compatibility check,
not proof that the loop sounds smooth.

Each recording contains three complete 16-bar cycles at the existing 72 BPM,
followed by a five-second tail: 165 seconds total. Identical palette, seed,
scene-analysis input, sample rate, master/background settings and mixer values
are used within each pair. The Romantic palette fixes the layer instruments
to round bass, bowed bed, felt melody and felt answer in both treatments.
The production Web Audio adapter and shared final limiter render both.

This controls palette changes, but does **not** isolate form alone: the authored
treatment also changes notes, harmony, density and durations. The baseline does
not acquire the new theme merely by sharing its seed. A subsequent ablation
would hold the notes/harmony constant and rearrange only sections. There are no
timed safe-drop sound effects, speech or copied game melodies.

## Level matching and interpretation

Raw renders must have finite samples, usable RMS and peak at or below the
production 0.14 ceiling. For each passage, both PCM recordings are attenuated
to the lower of 0.018 RMS and the quieter raw recording's RMS. Quantized outputs
are checked again; boosting is prohibited. This matches whole-clip measured
energy, not perceived loudness or short-term dynamics. Playback has a shared
volume control and only one recording plays at a time.

The review keeps scene fit, enjoyment and distraction separate, with an optional
recurrence question. Two comparisons and their reversed repeats give four
trials; repetition checks consistency, not correctness. Ties, unsure and skipping
are allowed. Candidate identities remain in the experiment root, outside the
served public folder. An author can still recognise musical differences: this
is candidate-label blinding, not a claim of perfect experimental blinding.

No CLAP score selects a winner. No human ratings have been supplied during
preparation. Automated playback/ratings tests use isolated synthetic answers;
they do not enter the listener packet or constitute preference evidence.

### First listener feedback, 23 November 2026

The user subsequently reported “Passage 1, A. Passage 2, A.” Following the
clarification about the first comparison, these refer to the first presentation
of the caper and reflection passages: A is the authored arrangement in both.
The [conversational feedback record](adventure-listener-feedback.json) preserves
the report, packet identity and treatment mapping separately from browser exports.
This is one listener's overall preference on two passages. Separate scene-fit,
enjoyment and distraction scores, playback duration, device context and answers
to the reversed repeats were not provided and remain unscored. The original
engineering proof retains its zero-rating preparation snapshot.

This supports trying a controlled follow-up, rather than changing defaults or
training a reward. Hold theme/harmony constant and compare form alone next;
the present preference does not identify which musical change helped.

## Run, resume and listen

Python uses the standard library. Node and Playwright are test/development
dependencies; `NODE_PATH` may point to an existing installation. Rendering uses
an isolated headless Edge profile through Playwright by default.

```powershell
python tools/adventure_listening.py start --max-new-renders 1
python tools/adventure_listening.py resume PRINTED_DIRECTORY
python -m http.server 8002 --bind 127.0.0.1 --directory PRINTED_DIRECTORY/public
python tools/recurrence_ratings.py PRINTED_DIRECTORY EXPORTED_RATINGS.json
```

Open `http://127.0.0.1:8002/review.html`. Serve only `public`; the experiment root
contains the identity key. Download a ratings backup to preserve answers outside
browser storage. The existing recurrence-label format/importer is reused and
decodes each objective separately, with no pooled reward or automatic promotion.

Every experiment and invocation has a timestamp/UUID. Source/configuration hashes,
renderer versions, raw/attenuated audio hashes and symbolic traces are archived.
The existing lab's lock, durable job attempts, atomic publication and verified
cache support failed-run recovery. A completed clip is reused; an interrupted
clip restarts as a fresh attempt. This is clip-level recovery, not sample-level
audio rendering continuation. Changed source requires a new experiment.
The arrangement planner's `nextStep` windows separately verify deterministic
symbolic continuation without duplicated or dropped attacks.

Raw recordings and answers stay in ignored `.score-lab/adventure-listening/`;
the [compact engineering proof](adventure-arrangement-proof.json) records the
prepared run without committing a large audio dataset.

## Checks and next decision

```powershell
node --test tests/adventure.test.cjs tests/mvp.test.cjs tests/score-lab.test.cjs
python -m unittest discover -s tests -p test_adventure.py
# Set AWEN_ADVENTURE_PAGE to PRINTED_DIRECTORY/public/review.html:
node tests/adventure.browser.cjs
node tests/audio.browser.cjs
node tests/evolution.browser.cjs
```

Engineering coverage includes grammar/register/time bounds, theme-preserving
sparsification, phrase gaps, common-tone seams, symbolic replay, real process-death
recovery, source/artifact integrity, attenuation-only matching and review backup
and playback controls. Physical FM1 listening and real enjoyment/distraction
ratings remain absent. No MIDI device is opened by these offline renders; the
reader's MIDI code is unchanged. Device-specific articulation and note-off
acceptance must be checked before a future live arrangement integration.

Listen before widening the grammar. If the authored treatment is useful, first
test form alone, then adaptive layering and bounded context-valid chapter bridges
under `awen-syq.2` / `awen-cjl`. Larger datasets, structural genetic search and
reward fitting remain later decisions. The runnable `index.html` is unchanged.
