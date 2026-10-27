# Blinded listening-calibration pilot

27 October 2026. This prepares the next calibration deliverable, not a trained ranker or a validated evolution reward. The reader's six-choice gallery remains available; this separate review page collects paired listening labels. No real listener answers are bundled or invented.

## Design

The [scene manifest](calibration-scenes.json) selects six passages from Rat, Riders and Time Machine: comic action, reflection, landscape, emotional aftermath, discussion and recounted unsettling travel. These are developer selection notes, not gold emotional labels. War remains untouched as the existing held-out book. Time Machine is now part of this listening pilot and must not be described as unseen calibration material later.

Each scene has three authored recipe/palette alternatives. The first is the existing Connected ensemble; the other two offer differing musical directions without specifying a correct choice. Recipe and timbre vary together, so this pilot cannot identify a single trait's causal effect. All use the same passage, seed, score cursor, target/context, volume, mix and timing within that scene.

The production engine renders four phrases through its existing limited graph. The public excerpt crops two complete phrases after the first phrase, approximately 26.7 seconds, so the score has begun developing. A preceding source paragraph supplies context where selected; the current passage and optional context are shown on the review page. Audio receives 200 ms edge fades and attenuation-only approximate RMS matching to the quietest alternative in its scene, capped at 0.018 RMS. No quiet alternative is boosted. Peaks remain under the production 0.14 ceiling. Neither equal RMS nor a digital cap establishes equal perceived loudness or physical speaker volume.

The 18 comparisons comprise 12 ordinary incumbent-versus-alternative pairs, three reversed-order repeats and three identical-audio controls (one per book). Incumbent A/B position is balanced across ordinary pairs; trial order is seeded and stable within the packet. Repeats/controls are not labelled on the review page. Identical controls and order reversals are consistency diagnostics, not automatic reasons to discard a listener's opinions.

Six scene selections and several variants of the same passage do not form independent held-out observations. One complete pass involves roughly 16 minutes of audio if every clip is heard in full, plus reading and answering. Short sessions and partial completion are welcome; this pilot need not be finished at once. No statistical reliability threshold is claimed from its size.

## Prepare and resume

Use the same Node/Playwright environment as the [native development evaluator](score-lab-python.md). Python needs only its standard library; CLAP/ML packages are not required.

```sh
python tools/calibration_packet.py start --seed listening-pilot-001 --max-new-renders 3
python tools/calibration_packet.py resume EXPERIMENT_PATH
python tools/calibration_packet.py resume EXPERIMENT_PATH --max-new-renders 0
```

Each start creates a timestamp/UUID directory under `.score-lab/calibration/` (`--root` can change the parent). It prints the exact experiment/log path before work starts. The existing fsynced atomic job journal, native audio artifact hashes and OS writer lock handle interrupted work. Completed clips are verified and reused; a failed local render gets a new attempt and log. Source/manifest changes require a fresh packet. A full packet is published only after all 18 native clips and cropped comparisons pass their gates. There are no provider/model calls.

Windows checkpoint replacement retries known transient sharing/access errors up to six attempts with short backoff, then fails with the complete temporary file retained. Other errors fail immediately. This handles brief reader/scanner locks without bypassing permissions or endlessly retrying a permanent failure.

To rebuild a review packet after a non-rendering tooling/UI change, compatible native audio can be reused explicitly:

```sh
python tools/calibration_packet.py start --seed listening-pilot-001 --reuse-renders-from OLD_EXPERIMENT_PATH --max-new-renders 0
```

Engine/renderer/scene fingerprints, exact render input, source manifest/result hashes and both WAV/trace hashes must match. Verified artifacts are copied into new unique attempts with origin provenance; reuse consumes no fresh-render budget. A missing incompatible render pauses at zero budget. After copying, the destination's completed jobs are self-contained and do not require the source packet to remain present. Public trial assignment is newly blinded for the new packet; old ratings must not be imported into it.

Files are separated:

| Location | Contents |
|---|---|
| `public/review.html` | Standalone offline review interface with embedded public data |
| `public/packet.json`, `public/audio/` | Blinded trials, source passages/edition notes and opaque WAV assets |
| `private-key.json` | Recipe/palette/genome identities, controls, gain measurements and trial mapping |
| `experiment.json`, `state.json`, `jobs/`, `logs/` | Versioned preparation inputs, checkpoints and unique attempts |
| `imports/`, `summaries/` | Explicitly imported raw answers and uniquely archived analysis outputs |

The generated material stays ignored by Git. The public folder includes text attribution and exact edition licence text; it includes no private recipe metadata, model scores or preferred answers. Blinding hides labels/configuration, not the sound of an instrument. A technically curious reviewer can inspect audio identities in the local files, so this is practical pilot blinding rather than a cryptographic guarantee.

## Listen and record answers

Open `public/review.html` with the audio folder beside it, or serve **only `public/`**:

```sh
python -m http.server 8927 --bind 127.0.0.1 --directory EXPERIMENT_PATH/public
```

Use the shared volume control for both alternatives and keep device volume steady during a comparison. Native audio-control volume changes also synchronize both alternatives. Audio has no autoplay, only one clip plays at a time, and Stop/Escape pauses playback. The page records three optional judgements separately:

- Which fits the passage better?
- Which do I enjoy listening to?
- Which is less distracting while reading?

Each allows A, B, about the same, unsure, or unanswered. Confidence and notes are optional. The “I heard both” checkbox is explicit self-report. Playback counters record browser activity and do not prove perception or attention. No comprehension test, hearing measurement or automatic taste label is inferred.

Responses and reading position save in browser storage when available, using a packet-specific key separate from the ordinary reader profile. Export JSON regularly; blocked/file-origin storage can be unreliable. Restore accepts a backup for this exact packet and preserves its anonymous rater ID. There are no accounts or telemetry, and the page never silently writes a repo file. Exported rater IDs are not verified unique people: clearing storage can create a second ID for the same listener, so keep/reuse a backup across sessions.

## Import and summarize

```sh
python tools/calibration_packet.py import-labels EXPERIMENT_PATH --file EXPORTED_LABELS.json
python tools/calibration_packet.py summarize EXPERIMENT_PATH
```

The label envelope has version `awen-calibration-labels-1`, packet ID/checksum, self-reported human rater ID and per-trial responses. Each response records the three choices, confidence, notes, self-reported listening, playback seconds, a revision number and timestamp. Invalid packet IDs/hashes, unknown/duplicate trials, bad values and non-human provenance are refused. Model-generated labels need a separate provenance path; do not present them as human exports.

Each import preserves the original JSON in a fresh timestamp/UUID directory with checksum/provenance. Summaries verify that checksum before reading it. Nothing overwrites previous imports. Summaries deduplicate by rater/trial and choose the highest response revision, so repeated exports are not extra votes. Conflicting content at the same latest revision is flagged and excluded until resolved with a newer revision. Do not edit archived imports to repair labels; update the review page and export a new revision.

Restore the most recent backup when resuming elsewhere: an older backup's lower revisions do not replace newer answers already imported by the organiser.

Missing or explicitly unheard answers remain raw evidence but are excluded from primary preference observations. Unsure, ties and unanswered dimensions stay separate. The summary reports coverage, identity-control ties, reversed-order consistency and canonical candidate-pair labels, with controls excluded from training observations. Candidate identities are joined only in these private analysis outputs. All listening/rater provenance remains self-reported. The tool does not fit a model, pool correlated trials as independent evidence, or claim that the reward is calibrated.

## Tests and next gate

```sh
python -m unittest discover -s tests -p test_calibration_packet.py -v
AWEN_CALIBRATION_PAGE=PATH/public/review.html node tests/calibration.browser.cjs
```

Set `AWEN_CALIBRATION_PAGE` with the shell's environment-variable syntax (PowerShell: `$env:AWEN_CALIBRATION_PAGE='...'`). The browser check uses isolated headless Playwright and clearly TEST-ONLY responses, which are never imported into the real packet. It covers playback exclusivity, no autoplay, three independent answers, unique JSON export, reload/backup, filtering, night selectors, mobile layout and blocked storage. Unit fixtures use synthetic audio and test-only labels; they do not supply musical judgements.

After actual listener feedback exists, inspect ambiguity, controls and missingness before considering a small feature ranker. Fit, taste and distraction must remain separate outcomes. CLAP similarity is still diagnostic-only. Hold out whole works/chapters/seeds for later acceptance, group uncertainty by scene/work/listener as appropriate, and retain the chapter-continuity/signal gates. The [calibration roadmap](clap-probe.md#calibration-roadmap--27-october-2026) and Beads `awen-3fr.6` / `awen-3fr.6.3` track that work.
