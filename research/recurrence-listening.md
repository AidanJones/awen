# Blinded recurrence listening pilot

Prepared 3 November 2026 for `awen-3fr.6.2.3.7.2` and preparation child
`awen-3fr.6.2.3.7.2.1`. This is listening-material preparation, not completed
preference calibration. No real ratings, learned reward or threshold change
are reported. The [earlier audit](variation-gate-review.md) motivates the test.

## What is being compared

Eight original, explicitly authored arrangements use the existing native
`AudioAdapter.note`, continuous harmony, palette routing, effects and final
output limiter. These are controlled experimental scores, not saved reader
compositions or transcriptions of Bach. Each contains six four-bar phrases at
the reader's fixed 72 BPM: 80 seconds of scheduled material plus a six-second
release tail, with a final two-second fade. There is no waveform cutting or
concatenation to manufacture loops. No model is needed to prepare or play them.

| Treatment (private key only) | Controlled musical difference |
|---|---|
| Short cell | One pitch every two eighth-note slots |
| Four-bar ostinato | The same sixteen-note figure in each four-bar phrase |
| Phrase variation | Same onset grid, duration, level and pitch vocabulary base, with motif rotations and occasional octave displacement between phrases |
| Sustained texture | Twelve longer notes over the eighty-second score |

Within each scene all four share a seed-derived transposition, four-voice
constant harmony, palette, background level, graph and rendering settings.
The first three have 96 foreground notes each; the sustained treatment has
12 and intentionally differs in note length and density. This is a texture
comparison, not an isolated test of recurrence alone. Static harmony deliberately
isolates some melodic differences; it cannot establish how moving harmony
changes tolerance for repetition. More expressive orchestration remains future
work.

The two blocks are the safe-drop passage plus its next two paragraphs from
*The Stainless Steel Rat* with the baroque palette, and three opening paragraphs
from *Riders of the Purple Sage* with the romantic palette. Both include preceding
context, edition revision, attribution and licence notes. Scene and timbre are
confounded across blocks; this is not a factorial genre study. These are familiar
development texts, not untouched book holdouts.

## Blinding and ratings

Each block has all six unordered pairs. A/B positions and trial order use a
frozen seeded shuffle, with two reversed repeat trials: **14 comparisons**.
The anonymous audio paths contain content hashes, not treatment names. The
identity key, manifest, jobs, logs and future rating imports stay outside the
served `public` folder. This is presentation blinding, not secure concealment
against a participant inspecting files or recognising a clip.

The independent questions are:

1. Which recurring pattern suits this passage?
2. Which accompaniment fits the passage better?
3. Which do you enjoy listening to more?
4. Which is less distracting while reading?

Every question allows A, B, tie, unsure or unanswered. Optional notes, confidence,
a heard-both declaration and playback counters remain separate. Counters record
playback, not attention or comprehension; short listening is not silently counted
as full exposure. An unselected or unheard clip is not a negative preference.
The repeated trials provide individual consistency diagnostics, without defining
a correct answer. Disagreement between axes or people must remain visible.

There is no autoplay. Only one clip plays at a time, Escape stops playback, and
navigation/reload stops audio. Files have attenuation-only RMS balancing towards
0.018 after the shared 0.14 output ceiling; gains and original signal measurements
are preserved in private job results. The player can only attenuate these files.
These digital checks do not establish comfortable physical speaker levels.

Responses save to a packet-specific local browser record. Export JSON regularly
and restore only a backup matching the exact packet identity/hash. Sessions may
be split: fourteen full pair listens would take about forty minutes before
reading/rating overhead. Do not require completing everything in one sitting.
Browser storage, the downloaded JSON and a repository file are distinct: the
page cannot write to the repo automatically.

## Frozen reservation and subsequent evaluation

The manifest reserves two new musical seed strings and cello/pastoral palettes
before any ratings. They are not rendered by this pilot. Seed variation here
only selects a bounded common transposition; those reservations are limited
tests of generalisation, not diverse new compositions or independent genres.
The existing chapters have been seen during development. A future evaluation
must additionally freeze genuinely new chapter selections before tuning.

Use actual listener labels to test whether a proposed variation measure agrees
with recurrence suitability **without losing enjoyment or reading comfort**.
Report ties, abstentions, incomplete exposure and per-listener disagreements.
Pre-register any threshold or reward combination before using the reservations.
Do not fit and report performance on the same fourteen trials. This packet is
too small to establish a general reward, population preference or reading benefit.
The current variation gate and physical/continuity requirements remain unchanged.

## Create, resume, serve and import

Python uses the standard library. Node/Playwright are development dependencies
only; use an isolated test profile and an installed browser channel. `NODE_PATH`
can point to an existing test dependency directory; `AWEN_BROWSER_CHANNEL`
defaults to `msedge`.

```powershell
python tools/recurrence_listening.py start --max-new-renders 2
python tools/recurrence_listening.py resume PRINTED_DIRECTORY --max-new-renders 2
python tools/recurrence_listening.py resume PRINTED_DIRECTORY
python -m http.server 8001 --bind 127.0.0.1 --directory PRINTED_DIRECTORY/public
python tools/recurrence_ratings.py PRINTED_DIRECTORY EXPORTED_RATINGS.json
```

Open `http://127.0.0.1:8001/review.html`. Serve only `public`, not the repository
or experiment root. Imports preserve the raw export and an individual decoded
summary in a fresh timestamp/UUID `ratings` directory; they do not update runtime
preferences or train a model. The summary keeps all four axes and reversal
agreement separately, with no pooled reward. Existing feedback/CLAP interfaces
and runtime evolution are unchanged.

Runs use timestamp/UUID roots, immutable source hashes and inputs, writer locks,
unique invocation/attempt logs, atomic result publication and artifact checksums.
Render budgets allow planned stops. A result published immediately before a
process dies is recovered without rendering it again. A failed unpublished
attempt is retried in a new directory. Completed replay uses no browser and
rejects changed artifacts or sources. Start a new run after changing source;
never edit a frozen experiment to make it resume under a different renderer.

## Engineering verification

See the [proof snapshot](recurrence-listening-proof.json). Tests exercise authored
score relationships, pair coverage, public blinding, reservation, chunked resume,
actual process death after publication, zero-budget replay and checksum rejection.
Synthetic ratings test ties, reversal decoding, missing axes and malformed
imports. They are not participant evidence. Isolated Playwright checks cover
exclusive playback, silent reload, all four rating axes, export/restore, wrong
packet rejection and mobile dark layout. Automated signal checks cannot establish
artistic quality, fatigue or the suitability of a repeated figure.

```powershell
python -m unittest discover -s tests -p test_recurrence.py -q
$env:AWEN_RECURRENCE_PAGE='PRINTED_DIRECTORY/public/review.html'
node tests/recurrence.browser.cjs
node --test tests/mvp.test.cjs
node tests/audio.browser.cjs
node tests/evolution.browser.cjs
```

The preparation child can close after verification. The parent calibration task
stays open until independent listening supplies evidence; no ratings are invented
to clear that gate.
