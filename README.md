# Awen

*Every story has a soundtrack.*

A small, local science-fiction reader with an adaptive synthesiser soundtrack. The entire runnable app is **[index.html](index.html)**: inline CSS, JavaScript and three complete reading texts. No React, build, install, CDN, backend, account or API key. Approximately 900 KB, mostly book text; the application code is a few hundred lines.

Active work is tracked in **Beads**: run `bd ready` for available tasks. See the [Beads workflow](.beads/README.md) and [roadmap snapshot](TODO.md). Personal music evolution, a wider-choice gallery and richer starting palettes are the priorities.

## Open it

Download `index.html` and open it in a modern browser. Click **Start soundtrack** to enable audio. Everything needed for reading and synthesis is embedded; the external edition and licence links are optional.

For a consistent storage origin, serve the directory instead:

```sh
python -m http.server 8000 --bind 127.0.0.1
```

Visit `http://localhost:8000`. Static hosting can serve the same HTML unchanged. A downloaded copy works offline; offline relaunch of a hosted URL is not implemented. Browser storage for `file://` pages varies, so localhost is recommended for reliable progress saving. There is no autoplay after a reload.

## Read and listen

- Choose a book from the shelf. Each book remembers its own paragraph.
- Use Previous/Next, Left/Right, or Space. Chapter selection jumps to the first paragraph in that chapter. Long paragraphs scroll naturally.
- **Restart book** returns to paragraph 1 and restarts the composition with the same seed, preserving settings and other books' positions. **Go to paragraph** accepts a whole number from 1 to the book-wide total; it saves the destination while keeping musical time running.
- **Aa / Reading preferences** adjusts text size, spacing and width. Night reading and focus mode reduce visual distraction.
- Start/pause the soundtrack, set its volume, or mix bass notes, chords, melody and pulse independently. Zero volume mutes with a short click-free fade.
- **Check sound** plays a short 440 Hz tone at the selected app volume. **Mute now** or Escape stops music and the check tone. Signal detection distinguishes generated audio from a muted mix; if a signal is detected but you hear nothing, check browser-tab mute, system volume and the selected output device.
- The waveform above Start/Pause is drawn from the actual limited output, including the check tone. It settles to a flat line on pause or mute, stops drawing while the page is hidden, and stays static when reduced motion is requested. It uses native Canvas and Web Audio with no visualisation library.
- **Sound palette** offers Warm ensemble (the default: connected woodwind/string-like motifs, soft bass and occasional plucked accents) or Space synth. These are original synthesis approximations, not recordings or realistic orchestral samples. Both share a short synthesised stereo room.
- **Continuous background** adds soft harmony under the foreground, initially at 30%. Chords follow an authored progression and crossfade at stable pitches, without pitch slides. Set it to zero for more space; the Chords mixer also scales it. All layers and effects use the same final limiter.
- In **Follow the story**, paragraph changes update narrative intent and gently adjust expression without restarting the theme or cutting notes. A scene change must remain stable for a bar and satisfy a minimum three-bar dwell before entering at a bar line. At the fixed 72 BPM this means changes can take several seconds. The Playing label distinguishes the active scene from a pending direction. **Steady ambience** keeps the neutral intent while the same composition continues.
- **Score seed** shows a seed saved separately for each book (initially `rat-001`, `war-001` and `time-001`). Apply a chosen seed or select **New interpretation**. During playback a new seed waits for the next four-bar phrase boundary; when paused it applies immediately. The active/queued status is shown. Unapplied queued changes are not committed across a reload.
- **Follow the story** derives musical targets from local phrase rules. **Steady ambience** uses a fixed neutral target for comparison. Pause for silence.
- **Behind the soundtrack** shows rule evidence, raw/contextual features, musical targets and the live smoothed state. Rules are artistic heuristics, not validated literary interpretation.

Progress, appearance, audio preferences, per-book seeds and score checkpoints stay in `localStorage` under `awen.reader.v1`. Musical state is saved on navigation, pause and periodically while playing. Compatible checkpoints restore the next score-grid position, scene, voicing and motif position; a reload still requires a new user gesture for sound. Incompatible composer/content revisions start a fresh interpretation with the saved seed. Blocked/full storage is reported; reading and audio continue for the session.

## Original musical starting points

Open **Shape your soundtrack → Compare musical starting points**. Alongside your current favourite, the gallery offers four original recipes and the existing Connected ensemble. Duplicate entries are skipped; spare slots show a saved favourite or a small variation. This comparison need not replace your current music: preview, pin or **Explore from here**, and only **Keep favourite** adopts it.

| Starting point | Musical behaviour |
|---|---|
| Spacious frontier | Open suspended harmony, guitar-like answers separated by long spaces, four-bar harmonic changes and a gently swelling background |
| Light caper | Reed-like phrases, rounded bass, soft accents and more rhythmic activity in sustained action |
| Unseen threat | Bowed fragments, darker suspended harmony and slow changes; background and bass carry the spaces |
| Intimate dialogue | Soft piano-like phrases, restrained accompaniment and complete alternate phrases without foreground melody |

These are procedural synthesis sketches, not realistic instrument samples. Recipes have authored note patterns, harmonic rhythm, chord material, envelopes and background voice balances; changing six preference numbers alone would not create these differences. The existing Warm ensemble/Space synth control remains a separate timbral option. All use the existing 72 BPM clock, continuous scene director, mixer and final limiter.

The ideas come from composer accounts of radio/film scoring and research on reading with music, documented in [the starting-point research notes](film_and_audio_drama_starting_points.md). They are original compositions informed by broad principles; no score recordings, extracted melodies, trained model or audio dataset is bundled. The four recipes have been checked on the same first three Rat passages, not validated as beneficial to reading.

A selected recipe is optional `scoreStyle` metadata alongside the six numeric genome traits. Variations retain the first selected parent's recipe while combining numeric preferences; every card identifies its recipe. Recipe identity survives pins, names, export/import and switching books. Old version-1 profiles imply Connected ensemble, and old named-pin keys migrate. The original recipe/seed sequence stays unchanged; new sketches have their own recorded `awen-sketch-1` version.

## Choose chords and dramatic direction

Open **Shape your soundtrack → Explore chords & direction**. Choose a genre context, harmonic intention and tonal centre; leave **Chord family** on suggested alternatives, or choose any of the nine families explicitly. **Build six harmony choices** compares your current direction with source-linked alternatives and the original starting-point harmony. **Chord cycle & research** on each card explains the root movement, change rate, saved version and source context.

Genre/intention choose harmonic material; the selected musical starting point still controls phrasing and instrument colours. The harmonic intention stays fixed after adoption while the story continues to steer texture and activity. **Current passage** supplies a starting suggestion when you build a batch; it does not silently change the harmony at every paragraph.

Preview, name/pin, **Keep favourite**, or **Explore from here** as in the regular gallery. Numeric preference evolution keeps the first selected parent's compiled harmonic direction. Use **Return to starting-point harmony** to remove the override without losing other preferences; **Undo last kept choice** can restore it. While playing, clear/import/undo changes enter at the next four-bar phrase boundary.

Harmony comparisons initially offer a **64-second long harmonic preview**; 16- and 32-second options are also available. Level balancing measures only the selected clip on demand and caches its level values for that duration. Existing ordinary variation previews still start at 16 seconds. Playback uses one shared limited graph and always has mute/stop controls.

Kept directions are stored as an optional versioned `harmony` snapshot alongside the numeric genome: engine/library version, genre, function, family, tonic, chord bank, form and harmonic rhythm. Pins, names, decisions and export/import retain this data. Compatible saved banks replay their stored pitches rather than being resolved again against a newer library. Unsupported engine versions or unrenderable chords fail import with the current profile preserved. Checkpoints carry a harmonic identity, preventing restoration of voicings from another harmonic recipe; legacy authored-score checkpoints remain supported.

## Personal soundtrack evolution

Open **Shape your soundtrack**, choose Whole score / Foreground / Background and Nearby / Wide, then **Explore six variations**. A gallery opens with the starting favourite, up to three pinned favourites and new candidates. Each new candidate changes melody or background presence alongside another trait; at least one explores further from the parent. Seeds select a composition; the preference genome controls its performance; the sound palette remains a separate setting.

**Play preview** replays 16 seconds from the same passage, seed, musical cursor and narrative target. Only one preview plays through the existing limited graph. Play again to stop, use **Mute now**, or Escape to leave. The gallery includes a volume control, approximate **Balance preview levels** option and the reading passage. The first balanced play of a candidate measures only that 16-second clip locally, then caches two level numbers for the open gallery. Louder candidates are attenuated toward a common reference RMS; quiet candidates are never boosted. Switching balancing off plays the original levels. This reduces average-level bias, not all perceived-loudness differences; ordinary reading volume is unchanged. Descriptions such as warmer or less melody report parameter differences, not automated judgements about sound. Very subtle differences or a muted layer may still be hard to distinguish.

**Keep favourite** adopts a previewed candidate across books. You need not hear or rank all six. **Pin** keeps up to three favourites available between rounds and in exported profiles. An inline **Favourite name** field names each pinned genome; names survive reload/export/import. **Recent kept choices** shows the latest five adopted choices and their setting changes. **Explore from here** uses one candidate as a parent; check several **Use as a parent** boxes and choose **Explore selected** to combine bounded traits and mutate them. **None of these · new batch** explores without recording a preference. **Undo this batch** restores up to eight previous batches in the open gallery; this temporary exploration history is discarded when the gallery closes. Pins remain saved even if you cancel exploration.

Keeping, cancelling, Escape or navigating restores the original musical cursor and pauses; press Start to resume reading. **Undo last kept choice** restores the previous adopted genome. A change made during ordinary playback (undo/import) waits for a four-bar phrase boundary. Ordinary reading is never interrupted by requests to rate music.

Six numeric genome traits control melody presence, attack softness, filtering warmth, room, background presence and slow background movement. Within a recipe, tonal rules, tempo, harmony, voice limits and the final output limiter stay fixed. Selection and small mutations need no trained preference model, LLM, dataset or external service. The six candidates are computed on demand as tiny parameter objects; ordinary use does not pre-render an audio library.

The browser stores the active genome, three pins and the latest 80 kept decisions. Accepted gallery decisions include all six candidates, selected winner, parents, mutation settings, book/content/composer versions, paragraph, seed, musical snapshot, target and mix settings. Skipped batches are not treated as dislike labels or retained as a dataset. Existing A/B profile files still import, and saved pins/gallery decisions survive an export/import round trip. Full archived comparison replay, persistent exploration archives and perceptual loudness evaluation remain later work. Profile version 1 accepts older files without names or balancing metadata; absent optional fields receive defaults. Decision history remains capped at 80 and temporary batch undo at eight; the last five decisions shown in the UI are a view, not a separate dataset.

For a repo copy, click **Save profile to file** and choose **profiles/personal.json**. A neutral starter file is included. Browsers without the file-writing API download `awen-personal.json`; move it into `profiles/`. **Browser saved** and **profile-file status** are shown separately. A successful write records the fingerprint of the exact profile snapshot written, so later changes show **Profile file needs updating**, including after reload. Cancelled or failed writes do not advance that checkpoint. The indicator compares current choices with the last successful write/import; it does not watch disk files for deletion or external edits. Browser storage updates automatically; save JSON again after more choices to update the repo copy. **Download JSON copy** is always available if file-picker writes fail. Downloads are reported as requested, rather than verified repo saves. **Import profile** restores a compatible saved file, replaces the active profile and clears the previous write handle so the next save chooses its destination. The app does not automatically read or overwrite repo files, and no server/build step is needed.

The current proof checks six different bounded audio signals, reduced RMS spread and the complete local select/evolve/save loop. At reference volume 35%, a six-candidate native render reduced highest/lowest RMS from about 1.63 to 1.03; this is a small engineering check, not a listening study or universal loudness guarantee. Tests cover lazy measurement/caching, cancellation during measurement, limiter routing, legacy profiles, name persistence, failed/cancelled saves, changes during a pending write, blocked browser storage and download fallback. It does **not** demonstrate learned musical taste, improved reading or better artistic quality. The next gate is a few short listening/reading sessions with these six choices before building larger datasets or running heavier analysis. Hearing all six complete previews takes 96 seconds plus switching; compare only those that interest you.

## The shelf and its sources

Reading text comes from these Standard Ebooks source editions, retrieved 25 October 2026:

| Book | Included reading text | Source |
|---|---|---|
| Harry Harrison, *The Stainless Steel Rat* | 19 chapters, 883 paragraphs | [Edition](https://standardebooks.org/ebooks/harry-harrison/the-stainless-steel-rat) · [Source](https://github.com/standardebooks/harry-harrison_the-stainless-steel-rat) |
| H. G. Wells, *The War of the Worlds* | 27 chapters, 884 paragraphs | [Edition](https://standardebooks.org/ebooks/h-g-wells/the-war-of-the-worlds) · [Source](https://github.com/standardebooks/h-g-wells_the-war-of-the-worlds) |
| H. G. Wells, *The Time Machine* | 12 chapters and epilogue, 308 paragraphs | [Edition](https://standardebooks.org/ebooks/h-g-wells/the-time-machine) · [Source](https://github.com/standardebooks/h-g-wells_the-time-machine) |

The [Stainless Steel Rat collection](https://standardebooks.org/collections/stainless-steel-rat) currently lists one downloadable edition; its other entries are marked `not-pd`. They are not bundled here. Standard Ebooks describes the bundled editions as believed public domain **in the United States**, with contributor work dedicated under [CC0](https://creativecommons.org/publicdomain/zero/1.0/). That does not establish public-domain status elsewhere; Harry Harrison's work in particular may remain copyrighted in your country.

Each book retains its source link, exact source licence text, colophon and source ZIP SHA256 in the embedded data, accessible through **Edition notes**. Inline styling, artwork, front matter and note reference markers are omitted; endnotes are retained in Edition notes. Paragraph boundaries follow the source XHTML, including its longer paragraphs. The decorative covers are CSS illustrations, not Standard Ebooks artwork. Awen is independent of Standard Ebooks. The project has not yet selected a licence for its own application code.

This MVP uses a curated embedded shelf, **not live catalogue search or arbitrary URL/EPUB import**. It avoids browser CORS restrictions and runtime network dependencies. To refresh the shelf, download source ZIPs from the three GitHub repositories and run the optional maintenance script:

```sh
python tools/refresh_books.py rat.zip wells-war.zip wells-time.zip
```

This replaces only the embedded JSON in `index.html`, following the EPUB spine order and excluding chapter headings from paragraphs. It is not a build step required to use or distribute the app.

## Engine-readable scoring research

The [film/theatre harmony research](research/scoring-knowledge.md) records nine source-linked harmonic families, eight dramatic functions and seven genre contexts as a [versioned JSON library](research/scoring-knowledge.json), with a [schema](research/scoring-knowledge.schema.json). Each exact cycle/mapping is labelled as an Awen proposal; source accounts and musical analyses support broader reasoning, not universal chord meanings.

The embedded library compiles to the existing four-voice renderer and is available through the chord/direction gallery above. An explicit experimental `audio.queueHarmonyRecipe(proposeHarmony('frontier', 'suspense'))` applies a selected harmonic candidate at a four-bar phrase boundary; `null` returns to the harmony stored in the selected personal profile. That low-level API remains a session-only override; the public gallery instead saves a compiled harmonic snapshot with the personal profile. Authored starting-point harmony stays available as an explicit return choice. Detailed API/validation commands are in the research document. No runtime fetch or build is required.

## Implementation

The inline script keeps narrative analysis, context aggregation, score mapping, smoothing, the audio adapter and UI functions separate. Versioned lexical rules include phrases, limited negation/intensifiers, capped repetition and punctuation. Context uses the current paragraph and the **last visited** paragraph, with no analysis of unseen neighbours or unchosen chapter content. Opening a different book clears transient context.

The pure `planStep` composer separates musical structure from rendering. It uses a 72 BPM grid, four-bar authored call/answer themes and a longer D-centred harmonic form. Closely related chord voicings retain common tones and minimise movement. Two banks of four quiet background oscillators crossfade over two seconds; frequencies change only on the incoming bank. Foreground notes have softer attacks, sustain and overlapping releases. Normal paragraph navigation never resets the musical cursor or releases existing foreground notes. Stable scene changes affect performance and rhythmic activity at bar lines. Intensity/density affect relative layer balance, brightness controls filtering, pulse affects rhythmic gain and spaciousness controls the shared room; the reported dissonance estimate is not a direct arbitrary-note generator.

`AudioAdapter` retains the output graph across navigation and provides playback, mix, seed/reset and checkpoint methods. Background recovery skips missed scheduling windows instead of replaying a backlog. Pause stops the voices/effects output and retains the next score-grid position for resume; it does not freeze/recreate individual oscillator phases or effect tails. Page exit stops output.

Composer version `awen-score-2` uses specified UTF-16 FNV-1a hashing and `sfc32` streams (with a 12-draw warm-up). Independent streams are keyed by version, seed, book, musical decision domain, phrase/bar index and decision index. Three original motif families and related harmonic forms provide identity; restrained omissions, expression and ornament decisions add variation. UI frames and mixer changes consume no composer randomness. Same seed, versions, initial state and musical-time-stamped intent history produce the same planned note/voicing events; different reading timings can change the performance. Cross-browser bit-identical audio and exact DSP automation replay are not promised.

All sound, including the check tone, goes through a 55 Hz high-pass filter, dynamics compressor, faded master gain and a final bounded waveshaper. The final sample magnitude cannot exceed 0.14 (approximately −17 dBFS); no gain is applied after the limiter. This limits the digital signal, **not physical sound pressure or hardware amplifier output**. Keep device volume comfortable; the app cannot guarantee hearing or speaker safety at arbitrary system-volume settings. Mute also cancels a pending audio start and fades out the held layers, so a check tone cannot accidentally bring the paused score back.

The richer ensemble preset is an artistic option, not a claimed cognitive benefit. See [background-music research notes](background_music_notes.md) for evidence and limits.

**Deliberate departures from the original specification:** plain JavaScript replaces React/TypeScript/Vite; rendering remains native Web Audio with no CDN. Strudel integration is still unimplemented; the persistent composer is independent of the renderer. Character-specific leitmotif discovery/memory, branching stories, a trained classifier, annotation/listening studies, arbitrary imports, service-worker caching and E Ink validation remain future work. The score uses original authored material, deterministic rules and synthesis, with no LLM or generative audio service.

## Verification

```sh
node --test tests/mvp.test.cjs
```

The dependency-free suite checks the books and feature bounds over all 2,075 paragraphs, analysis, smoothing, audio lifecycle, routing/limiting, specified RNG vectors, reproducible score events, independent streams, phrase continuity, scene dwell, compatible/corrupt checkpoints and per-voice constraints. It simulates ten minutes across eight seeds to check register, voice leading and polyphony.

For the optional real-browser audio suite, install Playwright in your test environment (`npm install --no-save playwright`, then `npx playwright install chromium`) and run:

```sh
node tests/audio.browser.cjs
```

Alternatively, set `AWEN_BROWSER_CHANNEL=msedge` to use installed Edge in a separate headless test profile. Playwright is a testing dependency only. The suite renders the production graph in native `OfflineAudioContext`, including an 80-second score, both palettes, background controls, muted layers, maximum levels and overloads. Live checks cover uninterrupted musical position through 20 paragraph changes, scene dwell/bar boundaries, explicit/generated/queued seeds, per-book seeds and checkpoints, all playback/mute controls, waveform/reduced motion, restart/jumps, mobile layout and no autoplay. These verify generated samples and behaviour, not the physical speakers or artistic quality.

The current revision passes 41 dependency-free tests. The isolated Playwright suite checks a final sample ceiling of 0.14, exact silence for zero master/all layers muted, audible output at the default level, and all controls described above. Listening quality and sustained real-device operation remain separate acceptance work.

Manual browser smoke checks: initial silence; user-gesture start; navigation while playing; keyboard navigation; chapter jump; per-book restoration; reload with saved progress and audio off; steady ambience; inspector; appearance and pause. Browser playback state was checked in the Codex in-app Chromium browser. Audible quality, long sessions, Safari/iOS, mobile devices and interruptions on real hardware still need listening/device tests.

Quick demo: choose *The Stainless Steel Rat*, **Steady ambience**, and seed `rat-001`; restart the book and listen for a minute to hear the recurring theme and harmonic form. Then select **Follow the story** and read normally. The first three paragraphs suggest caper, dialogue and chase intentions, but they no longer restart three musical cues. Hold an action passage to let the arrangement evolve. Use another seed to compare an interpretation, then return to `rat-001` and restart for the same initial composition. Lexical estimates can miss irony; these are artistic heuristics, not a comprehension aid.

The [original implementation specification](adaptive_reading_soundtrack_spec.md) and [research paper draft](paper.md) retain the broader research direction; they describe planned features beyond this MVP.

The [continuous-score review](continuous_score_review.md) records the former cue-like implementation and the design behind this revision. Persistent structure, seeds and basic transition rules are now implemented; Strudel integration and listening evaluation remain future work. The [SSX Tricky research note](ssx_tricky_audio_research.md) documents first-hand accounts and public parser/reverse-engineering code, with limits on what is known about EA's original runtime.

Personalisation browser checks: `node tests/evolution.browser.cjs` (same Playwright setup as the audio checks).

Starting-point proof: `node tests/starting-points.browser.cjs` uses the same isolated Playwright setup. It checks recipe choice/evolution, named-profile compatibility, four 16-second sketches over three matched passages, dialogue rests and native signal bounds.

Integrated harmony direction checks: `node tests/harmony-directions.browser.cjs` verifies the public controls, 64/16-second previews, native output cap, versioned pin/profile round trips, exact checkpoint reload, cross-book persistence, reversible clear and incompatible-import handling.
