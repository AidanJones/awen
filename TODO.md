# Awen: open work and exploration

Updated 27 October 2026.

**Tracking:** Beads is authoritative for current status; run `bd ready` / `bd list`. This roadmap records the work and research strands, including the latest development-loop direction in section 8. Some older items combine shipped features with remaining evaluation; consult their Beads issue before starting work. See [.beads/README.md](.beads/README.md) for the workflow and epic index.

This is the consolidated backlog, not a commitment to implement every research idea. The immediate direction is pleasant, continuous music that a listener can shape. **LLMs are welcome during development; the finished browser/device score must run without an LLM.** Python may support development-time ML, analysis and provider integration. Keep the runnable app self-contained in single-file HTML with inline JavaScript/CSS, no React/build step and minimal dependencies wherever practical.

## Already available

- [x] Four complete curated books, including The Stainless Steel Rat and the western Riders of the Purple Sage; paragraph/chapter navigation, restart and paragraph jump.
- [x] Continuous native Web Audio composer, recurring themes, connected harmony, seeded planning, per-book checkpoints and scene dwell/bar transitions.
- [x] Adjustable background and layers, palettes, waveform, explicit start/pause, emergency mute and shared output limiter.
- [x] Six-candidate preference gallery with foreground/background scopes, nearby/wide exploration, multiple parents, pins/names, keep/cancel/undo and a capped decision history.
- [x] Original musical starting points, six sound palettes including western guitar/whistle and strings/brass, and a source-linked harmonic-direction gallery with saved choices.
- [x] Readable themed dropdowns in night mode.
- [x] Browser profile persistence plus explicit JSON save/import; neutral repo starter in `profiles/personal.json`. Browser choices do not automatically update that file.
- [x] Initial reading/music, continuous-score, SSX Tricky and film/audio-drama research notes. Written-source review is complete for this pass; scene listening and score analysis remain open.
- [x] Development-only score-lab prototype (`awen-88h`): bounded seeded search, real native audio rendering, objective gates, blinded audio-judge exchange, optional adapter loop and held-out reporting. Eight clips passed engineering checks; no LLM judgements or musical winner yet.

## 1. Personal evolution: highest priority

### EVO-01 — A gallery with a wider choice

- [x] Replace or supplement the two-option comparison with an initial gallery of **six candidates**, including the current favourite. Six is a starting design choice to test, not a research result.
- [x] Use clearly labelled cards with Play/Stop, Keep favourite, Pin and Explore from here. Play only one candidate at a time through the existing limited output graph.
- [x] Offer a few optional plain descriptions such as warmer, more space or more movement. Generate descriptions from actual parameter differences; do not imply the system heard or understood the music.
- [x] Allow one favourite or several selected parents; offer None of these and New batch without forcing a ranking of every candidate.
- [x] Preserve pinned favourites between rounds. Let the listener replay the parent and undo a generation.
- [x] Keep previewing optional and separate from ordinary reading. Restore the reading position and original score cursor when leaving the gallery.
- [x] Automated keyboard, touch-layout and playing/selected-state checks; the time burden and actual listening usability remain part of reader evaluation.

Acceptance: a listener can hear a meaningfully wider range, choose one or more promising directions and generate a new round without losing favourites or their reading place.

### EVO-02 — Explore nearby or explore widely

- [ ] Add a mutation-strength control: small refinements versus broader exploration.
- [ ] Start each batch with the unchanged parent, a few nearby variants and at least one more distant but musically constrained option.
- [ ] Prevent duplicate/nearly identical candidates; vary audible characteristics rather than only changing seed labels.
- [ ] Define compatible recombination for multiple selected parents. Preserve authored harmonic/phrase constraints and output limits.
- [ ] Separate a composition seed from a personal preference genome and a palette identifier. Record all three.
- [ ] Keep the existing foreground/background scope; consider locking any trait the listener already likes.

Acceptance: repeated selection can refine a favourite, while broad exploration can escape an unhelpful starting point.

### EVO-03 — Richer musical traits

- [ ] Evaluate traits for melodic rest frequency/length, motif spacing, harmonic change rate, register, orchestration and scene persistence.
- [ ] Improve foreground/background interaction so more continuous music can still breathe without returning to an unchanging drone.
- [ ] Define perceptually useful bounds and test extremes/combinations. Preserve coherent harmony, scheduling, polyphony and output limiting.
- [ ] Audit the current six traits for audible range and interactions, including whether activity increases/decreases are equally useful.

Acceptance: different genomes produce clearly different musical behaviours, while every candidate remains a plausible reading accompaniment.

### EVO-04 — Taste, narrative fit and reading comfort

- [ ] Distinguish I enjoy this, It fits this passage and It helps me read. Do not treat them as the same judgement.
- [ ] Add optional quick feedback: too busy, too plonky, too droney, too tense. Keep these separate from candidate selection.
- [ ] Transfer general taste across books; investigate scene-specific preferences without memorising unrelated tunes per paragraph.
- [ ] Let feedback be sparse and voluntary; avoid prompting after every paragraph.
- [ ] Evaluate optional lightweight local preference ranking only after collecting useful choices. Human selection and bounded mutation remain sufficient for the first version.

### EVO-05 — Fair and reproducible comparisons

- [ ] Keep passage, seed, musical starting state, narrative target and non-evolved settings consistent across candidates.
- [ ] Compare similar phrase-length excerpts; test whether sequential playback or switching at a shared musical position is easier to judge.
- [ ] Check loudness bias between variants. The output cap bounds samples but does not establish equal perceived loudness.
- [ ] Record full generation lineage: parents, all candidates, selected/rejected/skipped items, mutation settings, versions and preview context. Current history stores A/B decisions and only the latest 80.
- [ ] Add reliable replay of an archived comparison, with clear handling of incompatible composer/content/genome versions. Symbolic replay does not promise identical DSP samples across browsers.

## 2. Better starting music

### MUSIC-01 — Original starting palettes

- [x] Prototype spacious frontier/western, restrained caper/intrigue, retro science fiction/unseen threat and intimate dialogue.
- [x] Give each its own authored musical identity, phrase behaviour and suitable timbres. Six preference values alone do not create a new genre.
- [x] Native rendering checks of four sketches on the same three Rat passages; listener comparison remains open.
- [x] Let the listener choose or evolve from multiple starting palettes; keep this separate from a book's narrative interpretation.

### MUSIC-02 — Film and audio-drama reference study

- [ ] Obtain accessible reference scenes and score materials; begin with Morricone/Leone westerns and Alan Williams's The Kraken Wakes.
- [ ] Inspect the deposited Kraken score and composer chapter if accessible. They were located but their full contents were not reviewed.
- [ ] Annotate roughly 12–20 excerpts, including dialogue, reflection, anticipation, action, aftermath and moments with no music.
- [ ] Record cue entry/exit, speech density, orchestration, register, motif recurrence, onset density, harmonic rhythm and transition shape with verified edition/timecodes.
- [ ] Study the scene mix as well as standalone score tracks; distinguish music from environmental sound.
- [ ] Translate broad principles into original material and adjustable rules. Film timing must be adapted to self-paced reading.
- [ ] Explore historical cue sheets as explicit scene-to-music references; inspect individual items before any reuse.
- [ ] Pilot a few aligned radio/film scripts, silent-film cue sheets and exact recordings before considering training (`awen-7x1.2.2`). Record actual music cues, timing, edition/rights provenance, dialogue/effects contamination and missing/uncertain labels. Unaligned orchestral recordings or script text alone do not supply narrative-scoring supervision; see [reference-source research](research/audio-text-evaluation.md).

See [film and audio-drama notes](film_and_audio_drama_starting_points.md) for sources, access limits and proposed starting behaviours.

### MUSIC-03 — Continuity, motifs and dramatic range

- [ ] Listen through longer sessions for repetition, disjointed transitions, plonks and fatigue.
- [ ] Add more original call/answer material and restrained development over longer spans.
- [ ] Explore character/location leitmotifs activated only by encountered content, with reliable identity tracking and no spoilers.
- [ ] Test deliberate thinning, rests and recovery after action; continuous scoring need not mean constant notes.
- [ ] Compare greater subdivision/activity with gentle tempo changes. Current tempo is fixed at 72 BPM, including chase scenes; tempo variation is optional and lower priority.
- [ ] If tempo varies, change the musical clock coherently at suitable boundaries and test continuity, replay and intensity. Avoid letting every paragraph alter tempo.
- [ ] Make chapter boundaries explicit in automatic score direction (`awen-7x1.3.2`): allow gradual expression/activity changes within a chapter, reserving larger automatic changes in palette, tonal regime, seed or motif identity for suitable musical boundaries after a chapter change. Keep explicit user choices, restart and seeking separate. A new runtime director is not implemented yet.

## 3. Profiles and repo storage

### DATA-01 — Personal profile workflow

- [ ] Make unsaved file changes clear: distinguish browser-saved choices from the last explicitly written JSON copy.
- [ ] Add named favourites, generation archives and readable summaries of how a profile changed.
- [ ] Define migration and retention policies before expanding history beyond 80 decisions.
- [ ] Test export/import round trips across browser/device and composer upgrades, including unavailable file APIs and cancelled writes.
- [ ] Consider a separate compact active profile and append-only experiment log for manageable Git diffs.

### DATA-02 — Several listeners, later

- [ ] Start with named local profiles and separate JSON files, with an explicit active listener. No accounts/backend are needed for that experiment.
- [ ] Prevent choices and taste settings from leaking between profiles; decide whether reading progress belongs to a listener or device.
- [ ] Only design sharing, conflict resolution or remote sync if needed. Preserve a simple one-person offline workflow.

## 4. Narrative interpretation without a large model

- [ ] Build a small independently annotated literary set covering dialogue, irony, negation, recalled action, suspense and calm.
- [ ] Evaluate and tune scene rules, thresholds, smoothing and persistence against that set and listening feedback.
- [ ] Separate the emotional language of dialogue from the scene's broader intent; improve context beyond just the last visited paragraph where useful.
- [ ] Test local word/character n-gram linear classifiers only if they improve held-out book/chapter performance over rules.
- [ ] Keep annotation labels, model/rule output and listener taste separate; retain explanations in the inspector.
- [ ] Evaluate offline LLM feedback during development (`awen-xfp.6`), including bounded proposals and actual audio-capable judging through score-lab. A text-only critic cannot establish heard musical quality. Preserve local listener-driven evolution and a finished runtime with no model calls; see section 8 for the concrete evaluation backlog.

## 5. Audio engine and interactive-score research

- [ ] Follow up SSX Tricky's public parser/reverse-engineering leads for transition/arrangement ideas. Original runtime rules, stems and authoring system remain unverified.
- [ ] Compare vertical layer changes and compatible phrase resequencing with the current persistent composer.
- [ ] Evaluate Strudel only for a concrete benefit such as pattern authoring or scheduling; assess single-file/CDN/offline packaging, seeded replay and licence compatibility before adoption. Native Web Audio is the current implementation.
- [ ] Keep a versioned symbolic score representation so composition is independent of a future renderer.

See [SSX research](ssx_tricky_audio_research.md) and [continuous-score review](continuous_score_review.md). The latter includes historical problems already fixed; do not treat its original diagnosis as a current bug list.

## 6. Listening evaluation and engineering acceptance

- [ ] Run reading comparisons: silence, fixed accompaniment, current adaptive score and personally evolved score.
- [ ] Measure preference/immersion, distraction, fatigue, reading time and comprehension separately. Do not assume preferred music improves comprehension.
- [ ] Include multi-session listening: a good short preview may become repetitive after 30 minutes.
- [ ] Test real headphones/speakers and comfortable levels; keep the sample limiter and emergency mute for all new preview paths. A digital ceiling cannot control hardware volume.
- [ ] Test Safari/iOS, Android, interruptions, background throttling and long-session CPU/battery behaviour.
- [ ] Extend existing unit/Playwright suites for gallery state, candidate lineage, cancellation, migration, replay, peak limits and no simultaneous preview outputs.

See [reading/music evidence](background_music_notes.md). Automated tests establish behaviour and generated sample bounds, not artistic success or physical listening safety.

## 7. Reader and longer-term deployment

- [ ] Arbitrary EPUB/local book import and a broader curated shelf; preserve chapter order, paragraph IDs, edition attribution and content revisions. Live Standard Ebooks loading is not implemented.
- [ ] Reliable hosted offline relaunch/book storage if needed; the downloaded HTML currently works offline.
- [ ] Native branching-story graph fixture first, then investigate Ink/Twine/EPUB interoperability; preserve actual visited-path context and avoid unchosen-branch spoilers.
- [ ] Standalone Android E Ink experiment: verify browser performance, usable audio output, background playback, controls and battery on actual hardware before committing to a device.
- [ ] Embedded/ESP32 native synthesis remains exploratory; benchmark voice/memory/power budgets and audio output rather than assuming browser code ports unchanged.
- [ ] Reconcile the original specification and paper with the shipped single-file/native-audio implementation and preference-evolution direction; choose an application code licence before distribution needs one.

See [original specification](adaptive_reading_soundtrack_spec.md) and [paper draft](paper.md) for the broader design history. React and mandatory Strudel passages there are superseded by the current implementation and user preferences.

## 8. Development search, ML tools and audio judging

See [score-lab design and commands](research/score-lab.md), [audio-judge rubric](research/score-lab-judge.md) and [measured engineering proof](research/score-lab-proof.json). This is bounded development search, not evidence that an AutoML model has learned musical quality.

### Implemented foundation — `awen-88h` (closed)

- [x] Small reproducible batches through the production browser synthesiser, with fixed passages, seeds, timing, volume and mix; no reference-audio corpus or large processing run.
- [x] Versioned JSON/WAV manifests, source/audio hashes, per-clip event/state traces and approximate RMS balancing by attenuation only.
- [x] Experimental rejection gates for invalid/over-level/silent audio, inside-chapter resets or regime jumps, excessive expression slew, constant symbolic patterns and excessive onset density. These do not establish pleasantness or reading benefit.
- [x] Separate judge dimensions for narrative fit, musical coherence and likely intrusiveness, with ties/abstention, timestamped audio evidence, both pair orders and identical/missing-audio controls.
- [x] Optional local adapter hook and bounded multi-round search (at most four candidates/three rounds), stopping without supported improvement. Output is a reviewable preset proposal; app defaults and personal profiles are never automatically changed.
- [x] Separate held-out book report; current proof has eight native clips, 51 unit tests and audio/profile Playwright checks, with zero LLM calls and no selected musical winner.

### Judge, metrics and promotion — `awen-3fr.6` (open)

- [ ] Connect an actual audio-capable provider adapter with pinned model/deployment, prompt/settings provenance, duration checks, bounded retries and an explicit cost ceiling. Attach the real WAV bytes; do not substitute a score description, MIDI labels or speech transcription.
- [ ] Calibrate against a few listener judgements before scaling. Keep **I enjoy this**, **it fits this passage** and **it helps me read** separate. Model-estimated unobtrusiveness is not measured comfort or comprehension.
- [ ] Validate the judge itself: swapped order, identical audio, absent audio, replaced audio, changed question wording, uncertainty and disagreement. Hashes and listening attestations alone do not prove audio perception.
- [ ] Audit reward hacking and loudness bias. Do not maximise volume, text–music embedding similarity, entropy or novelty as a single musical-quality metric. If using CLAP/other embeddings, first test their relationship to this accompaniment task and listener choices.
- [ ] Calibrate continuity/variation limits: preserve identity and some recurrence while avoiding an unchanging drone, relentless novelty, plonks and fatigue. Larger automatic changes belong at chapter boundaries; smooth within-chapter development remains desirable.
- [ ] Expand only after the small gate is useful: additional scene functions, ambiguous dialogue, fresh seeds, unseen chapters/books, slower/faster reading and longer sessions. Keep labels independent of the current classifier. The current few opening passages are not a representative benchmark.
- [ ] Compare against the shipped baseline and retain failures/abstentions. Use held-out cases once for acceptance; retire them from holdout status if their results guide tuning. Require no meaningful regressions across the separate objectives rather than hiding them in one average.
- [ ] Promote accepted development results only as small versioned rules, parameters, musical recipes or an appropriate tiny local model, with listener acceptance and runtime regression checks. Do not bundle a development LLM, provider credentials or Python/server requirement into the reader.

### Python integration — `awen-3fr.6.1` (implemented; provider calibration remains open)

- [x] Implement a standard-library Python orchestration bridge with the shared native renderer/metrics and a Python audio-provider adapter contract. See [commands and recovery](research/score-lab-python.md); the finished reader remains self-contained and LLM-free.
- [x] Create unique experiment directories and fresh invocation/attempt logs, atomic checkpoints, an OS writer lock, verified per-clip/provider-response caches and new attempts for failed local work.
- [x] Resume interrupted work without rerendering completed clips or silently repeating ambiguous provider calls. Preserve raw responses and hashes; support response reconciliation, explicit retries, persistent request budgets and strict source/model identity checks. Exercise real process-death recovery separately from the native audio smoke test.
- [x] Preserve seeds, bounded candidates/parent lineage, judge controls and shared proposal/held-out formats across Python/JavaScript. Verify JSON key-order interoperability rather than maintaining a second synthesiser.
- [ ] Connect/calibrate a real provider and evaluate optional ML dependencies under the parent `awen-3fr.6`; the bridge itself does not download models or invent judge results.

### Audio–text embeddings — `awen-3fr.6.2` (open)

- [x] Implement the first CLAP slice (`awen-3fr.6.2.1`): optional pinned CPU backend, ten-second native audio windows, independently drafted briefs, unsuitable/shuffled/paraphrase/silence controls, content-addressed feature cache, unique logs and resumable feature jobs. See [measured results](research/clap-probe.md).
- [x] Reject extreme text-encoder collapse. The initial music-only checkpoint failed an independent API sanity check; the pinned general/music/speech replacement passed it. The four-window result is not a reliable evolution reward (2/4 intended scene preferences, two wording reversals and two silence wins), so no preset is adopted.
- [x] Verify a real 14-feature run paused after two features, resumed without recomputation, and a fresh experiment reused all vectors with zero new inference/model loading. Keep model weights and optional dependencies out of the reader/repo.
- [ ] Compare pretrained LAION CLAP, music-specific MuQ-MuLan and CLaMP 3 on a tiny scene-brief/audio set before training a new joint encoder. Check actual checkpoint licences, revisions, preprocessing and hardware requirements.
- [ ] Keep embedding association distinct from narrative fit, musical coherence, personal taste and reading comfort. Use independent briefs and negative/shuffled pairs, not the current classifier's labels as ground truth.
- [ ] Cache by audio/text/checkpoint/preprocessing hashes; measure timed windows and hold out whole works/genres. Only use embeddings for shortlisting or a small ranking layer after listener agreement is useful. An audio-capable LLM can judge finalists during development; neither becomes a required runtime dependency.
- [x] Build the replayable blinded calibration packet (`awen-3fr.6.3`): six scenes across Rat/Riders/Time, three same-scene alternatives each, 12 primary comparisons plus three reversed-order and three identical-audio controls. The separate offline review page records fit, enjoyment and distraction with ties/uncertainty, backup/export and self-reported listening. Native renders/packet preparation resume with unique logs; label imports retain revisions, deduplicate exports and flag conflicts. See [pilot guide](research/listening-calibration.md) and [engineering proof](research/listening-calibration-proof.json).
- [ ] Collect the first actual listener labels in short optional sessions, then inspect coverage, ambiguous answers and controls. The prepared pilot has zero real ratings and establishes neither reward reliability nor reading benefit. War stays excluded; Time Machine is now calibration material rather than a future unseen book.
- [ ] Compare raw CLAP, a fixed paraphrase ensemble and a small regularised ranker against the incumbent/simple-feature baselines. Keep the encoder frozen first; verify that CLAP actually adds useful held-out information before expanding data or comparing larger models.
- [ ] Add anti-gaming controls for near-silence, drones, repeated/busy attacks, noise, loudness changes and discontinuities. A fit score cannot compensate for failed signal or continuity constraints. Freeze choices before held-out book/chapter/seed evaluation, report scene-grouped uncertainty, and trial listener shortlisting before automatic reward-based selection.

See [audio–text and script/cue-sheet research](research/audio-text-evaluation.md). The first CLAP checkpoint experiment is complete; cross-model comparisons and reference-corpus work remain backlog items. No reference corpus or model training has been performed.

The [27 October calibration roadmap](research/clap-probe.md#calibration-roadmap--27-october-2026) records the order of work and promotion gates. A reliable combined reward may be possible; raw CLAP is not presumed sufficient, and dropping it is an acceptable outcome.

### Related open strands

- [x] Nine-direction personal exploration (`awen-w3k`): broad 3×3 starting grid, production-engine previews, up to three retained parents, bounded seeded refinement, previous rounds, backups and reader-profile downloads. Separate from blinded A/B labels. See [guide and limits](research/nine-direction-exploration.md).
- [x] Different instrument articulation and kinetic options (`awen-ejv`): procedural plucked strings, sustained winds/bows, brass filter movement and wooden accents; driving strings/clockwork caper in the grid, more action rhythm without a tempo reset. Native pitch/envelope/output checks; [details and remaining listening questions](research/instrument-articulation.md).
- [x] Bounded CLAP-guided grid search (`awen-0qr`): nine current directions plus two six-child generations. Average cosine improved on a fresh seed and unused wording, but individual reversals, silence failures and unchanged action specificity prevent treating it as a reliable reward. Unique logs, real pause/resume/zero-budget replay and listening comparison; defaults unchanged. [Results and proof](research/grid-clap-evolution.md).
- [x] Academic working paper and first evaluator comparison (`awen-2yo`): compiled LaTeX draft with explicit measured/proposed boundaries; six objectives/baselines, five fresh-seed selections, cached audio/features, resumed run and labelled listening page. New checks reverse the prior winner versus unchanged strings. [Paper](research/paper/main.tex), [ledger/results](research/experiment-ledger.md), [proof](research/evaluator-comparison-proof.json).
- [x] Benchmark one alternate encoder (`awen-3fr.6.2.2`): pinned MuQ-MuLan versus original CLAP on five identical clips, two windows and controls. MuQ improves one silence diagnostic but worsens target silence and window stability; no reliable replacement reward established. Isolated environment, strict state/artifact/source validation, 22 features and resumed/cached execution. [Results](research/muq-comparison.md), [proof](research/muq-comparison-proof.json), paper updated in place.
- [ ] Obtain actual listener labels before fitting personal rankers or claiming validated reward superiority. A learned-preference reward or audio-language judge remains a separate controlled experiment; never substitute general CLAP vectors into a head trained on another encoder.
- [ ] Listen across these starting directions in longer reading sessions; use actual preferences to choose which richer compositional traits should evolve next. Automated waveform differences do not prove meaningful musical diversity.
- [ ] Richer musical traits and meaningful bounds — `awen-3fr.3` / EVO-03.
- [ ] Reliable replay of archived comparisons and complete generation lineage — `awen-3fr.5` / EVO-05.
- [ ] Explicit chapter-aware runtime direction and varied traversal fixtures — `awen-7x1.3.2` / MUSIC-03.
- [ ] Sparse feedback UI separating taste, fit and reading comfort — `awen-3fr.4` / EVO-04.
- [ ] Real listener/device and longer-session acceptance — `awen-r42` / section 6.

## Suggested next slice

Classical-repertoire strand (31 October): see
[reviewed sources and staged experiments](research/classical-inspiration.md) and
[implemented Bach-inspired DSL](research/bach-dsl.md).

- [x] Integrate a bounded figured-line DSL with reader playback, profiles, pins,
  phrase-boundary changes, gallery/grid evolution and the development renderer.
- [ ] Prototype section-specific Vivaldi storm/cold/indoor-repose contrasts after
  inspecting score/sonnet alignment; retain programme evidence separately from
  proposed reading uses.
- [ ] Inspect a specified Chopin Op. 28 No. 4 edition and prototype slow harmonic
  movement/voice leading as a distinct starting family.
- [ ] Review primary scores and work-specific analysis for Beethoven, Satie and
  Debussy; add bounded meter, texture and development features only as needed.
- [ ] Compare structural families with the familiar score in small listener
  sessions before enlarging the corpus or using fit metrics for selection.
- [ ] Add structural DSL mutation and fully tracked lineage only after parser,
  continuity and listening constraints are established. Current evolution
  preserves DSL source and varies numeric genome traits.

1. Use the resumable Python bridge to connect and calibrate a real provider against the strict judge exchange.
2. Calibrate the judge and metric thresholds on a few matched comparisons, with listener judgements kept separate.
3. Add chapter context and continuity fixtures before changing automatic runtime direction.
4. Explore richer musical traits and archived replay; widen search only after held-out checks and a few real reading sessions support the direction.

Engineering and development experiments can proceed independently; personal taste, reading comfort, fatigue and actual-device listening require listener evidence. Keep those gates explicit rather than inventing labels on the listener's behalf.
