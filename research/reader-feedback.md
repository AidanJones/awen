# Optional reader feedback: enjoyment, fit and reading help

Implemented 6 November 2026 for `awen-3fr.4.1` and `awen-3fr.4.2`. Parent
`awen-3fr.4` remains open for personal ranking, generalisation and evaluation.
This adds a feedback collection/export path and development import. It does not
change the score, default music, MIDI settings or evolution reward.

## In the reader

Open **How is the music working for you?** below the soundtrack controls. While
the reading soundtrack plays, choose **Capture current listening moment**.
The panel then offers three separate five-point agreement scales:

- **I enjoy this music**: personal musical enjoyment.
- **It fits this passage**: perceived narrative fit.
- **It helps me read**: self-reported reading help, not measured comprehension.

Each scale runs from strongly disagree (1) through neutral (3) to strongly agree
(5). Unanswered remains `null`, never zero or a rejection. Independent optional
tags are **Too busy**, **Too plonky**, **Too droney** and **Too tense**. Notes alone
or tags alone can also be saved. At least one answer, tag or note is needed.
An optional listening-setup field can record the FM1 patch, headphones or another
detail in the listener's own words. No hardware patch is queried or inferred.

Feedback is voluntary and the panel stays closed until opened. There are no
per-paragraph prompts. Saving, discarding and downloading leave playback,
preferences and candidate selections intact. Capture is for the reading
soundtrack, not a check tone or gallery preview. Playback must be running, but
the page does not establish that the listener heard it or for how long.

## Freeze the context before answering

Capture copies the current book revision and paragraph identity, composer
snapshot/seed/step, **active** genome, pending genome, harmonic override, scene,
pending scene, smoothed state/target, volume/mix/background, palette and narrative
labels. Navigation or a later queued musical change cannot relabel that captured
moment. The panel names the captured book/paragraph/step/route while the user
answers. Save or discard the existing moment before capturing another.

The step is a scheduler position, which may be ahead of audible output because
notes are scheduled in advance. It is not an audio recording, proof of sample
alignment, or a guarantee of identical replay across browsers. A small
`textHash32` fingerprint supplements the book revision and paragraph ID; it is
not a cryptographic identity. Book text is not duplicated into every record.

Routing is explicit: **browser**, **midi** or **both**. MIDI captures its selected
channel, part mode and velocity cap. A listener-supplied setup note is separate
from that observed browser state. External patch identity, audio, physical volume,
firmware, latency and loudness are not measured. Browser timbral preferences and
FM1 patches must not be treated as interchangeable acoustic observations.

These records are distinct from musical favourites/gallery choices, dictionary
interpretations and controlled listening-pilot responses. Choosing a candidate
does not populate any of these rating axes. The earlier broad “sounds good”
conversation is not converted into a fabricated rating record.

## Storage and backups

The dedicated local key is `awen.reader-feedback.v1`, with schema
`awen-reader-feedback-1` and provenance
`personal-listening-not-independent-study`. An anonymous local notebook/rater ID
is generated once and restored with backups. It is not a verified identity or a
claim of independent annotation. Up to **120 moments** are retained. At capacity,
the reader refuses a new save and preserves all existing records; it does not
silently evict old feedback. Saved records are append-only in this MVP. Notebook
rotation/editing is future profile-workflow work.

**Download feedback backup** writes a JSON download with a unique filename.
The page cannot write directly to the repo. Draft questions/captured moments are
in memory until Save and are discarded on reload. Saved feedback persists when
browser storage works; downloads provide the durable backup.

**Merge a feedback backup** validates the entire file before changing anything.
The limit is 2 MiB. Exact duplicate IDs/answers are deduplicated. Conflicting IDs,
malformed fields, out-of-range ratings/routing, mismatched snapshot identity,
different nonempty notebook/rater IDs and over-capacity merges are rejected.
It never partially merges a bad file. Historical composer/style versions are
preserved as archival data, not silently normalised into today's score engine.

If storage writes fail, answers remain downloadable in memory and the page says
so. If existing stored feedback is unreadable, new answers cannot overwrite it
implicitly: they remain in memory until exported or a valid backup is explicitly
merged. Musical preference/profile storage continues separately.

## Development import

Python's standard-library importer invokes the same pure validator embedded in
the reader through a small Node bridge. There is one schema, not independently
drifting browser/Python validation rules. It opens no browser, MIDI device,
waveform or model, and performs no provider calls.

```powershell
python tools/reader_feedback.py start PATH_TO_DOWNLOADED_FEEDBACK.json
python tools/reader_feedback.py resume PRINTED_IMPORT_DIRECTORY
```

Outputs under `.score-lab/reader-feedback/TIMESTAMP-UUID/` are:

- `input.json`: the unchanged submitted bytes.
- `manifest.json`: input SHA-256 and code/source identities.
- `labels.jsonl`: separate ordinal axes, independent tags/notes, active/pending
  musical context, anonymous rater/book/paragraph/version and output routing.
- `report.json`: answered/unanswered counts and per-axis histograms, route and
  tag counts; no combined preference/quality/reward score.
- `complete.json`: checksummed outputs bound to the manifest.
- `logs/`: uniquely named, fsynced invocation journals.

Runs use a writer lock and atomic publication. If a process stops after labels
publish, resume preserves the same rows and finishes the receipt. Completed
replay checks source, input, manifest and output identities and does not rerun
Node validation. Changed sources require a new import; changed completed
artifacts are rejected. The input is small/bounded; no experiment corpus or
pretrained model is created. Separate imports do not automatically pool people
or deduplicate across folders. Use record/rater IDs explicitly when curating a
future dataset so repeated imports cannot become extra votes.

## Evidence and next steps

The [engineering proof](reader-feedback-proof.json) records five new schema tests,
four Python importer tests, the native MIDI/MVP logic regressions and isolated
Playwright checks. Synthetic browser interactions cover frozen passage/state,
active versus queued genome, independent scales, MIDI context, save/reload,
export/merge/conflict rejection, unreadable-storage preservation and mobile dark
layout. The native audio, evolution and MIDI suites protect playback behaviour.
An actual process-death test stops the importer immediately after JSONL publication
and verifies byte-stable recovery. All generated ratings are marked synthetic
test fixtures and stay in ignored `.score-lab/tests` paths. **No real participant
ratings or model improvement are claimed.**

Before fitting a local preference model, collect useful voluntary feedback,
inspect uncertainty and coverage, reserve books/sessions before tuning, and keep
output mode/patch differences explicit. Evaluate enjoyment, fit and reading help
separately against listener choices. Do not train on unanswered axes, treat tags
as complete disliked-example labels, or turn reading-help impressions into
objective comprehension scores. Runtime evolution remains human selection and
bounded mutation with no model/cloud dependency.

```powershell
node --test tests/mvp.test.cjs tests/midi.test.cjs tests/feedback.test.cjs
python -m unittest discover -s tests -p test_reader_feedback.py -q
# Use an isolated Playwright install; set NODE_PATH if needed.
$env:AWEN_BROWSER_CHANNEL='msedge'
node tests/feedback.browser.cjs
node tests/audio.browser.cjs
node tests/evolution.browser.cjs
node tests/midi.browser.cjs
```
