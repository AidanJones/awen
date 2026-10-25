# Awen — Adaptive Reading Soundtrack Implementation Specification

**Status:** MVP build specification  
**Implementation note:** A single-file, dependency-free MVP now lives in `index.html`; see README for implemented features and deliberate stack changes. The requirements below remain the broader design target, not a claim that all features are implemented.
**Target:** Coding agent  
**Product:** Browser-based, paragraph-by-paragraph e-reader with a continuous, adaptive procedural soundtrack  
**Non-negotiable:** No LLM, hosted AI, text-to-music API, or runtime cloud dependency.

**Name:** Awen — Welsh for *poetic inspiration*.  
**Revision:** 25 October 2026; original specification extended against the shared research conversation.  
**Reading guide:** Sections 15–20 incorporate the subsequent branching-narrative and hardware decisions, preserve the research notes, and clarify the roadmap. They extend the original linear-book MVP; where earlier hardware suggestions conflict, section 17 records the final direction. All features remain planned until implemented and tested.

## 1. Product goal
Build a local-first web app that presents a public-domain science-fiction book one paragraph at a time and adapts a continuous, atmospheric synthesiser soundtrack to the reader's current position. Use lightweight deterministic NLP for the first implementation and Strudel for music. The soundtrack should behave like an interactive game score: stable musical identity, gradual layer changes, occasional accents, and no restarting at paragraph boundaries.

**Reference experience:** restrained, spacious sci-fi synthesiser scoring with the adaptive layering of a game soundtrack. Do not reproduce copyrighted melodies, recordings, or distinctive sound designs.

## 2. Scope
### MVP must include
1. A responsive reader with one paragraph visible at a time, previous/next controls, keyboard shortcuts, chapter navigation, progress indicator, and adjustable typography.
2. Bundled, legally verified public-domain text of *The War of the Worlds* by H. G. Wells, with title, author, source, edition, and rights metadata. Start with chapter one for the vertical slice; architect for the whole book.
3. Local persistence of current book/chapter/paragraph, reader settings, soundtrack enablement, and volume.
4. Deterministic text analysis producing paragraph-level narrative features, with inspectable evidence for scores.
5. A continuously running Strudel-driven procedural score using at least four controllable layers: drone, harmonic texture, sparse motif, and pulse/tension.
6. Smooth changes in intensity, density, timbre, harmony, and layer gain as reading position changes; avoid audible resets.
7. An optional developer overlay displaying current paragraph ID, raw and smoothed feature vectors, active musical state, and active layers.
8. Unit tests for parsing, analysis, smoothing, mapping, and persistence; at least one browser-level playback/navigation smoke test.

### Explicitly out of scope for MVP
- LLMs, generative audio, external inference, user accounts, cloud sync, DRM-protected books, arbitrary PDFs, eye tracking, narration/TTS, mobile native apps, monetisation, or an audio recording/export feature.
- Automated leitmotif extraction from arbitrary books. The first version may use hand-authored thematic motif mappings.

## 3. Technical stack
- TypeScript, React, Vite.
- Strudel (`@strudel/*` packages as appropriate to the supported browser integration) for pattern scheduling and synthesis; use the documented programmatic API, not an embedded live-code editor or untrusted `eval`.
- Web Audio API for master gain, transitions, audio unlock, and optional additional effects. Tone.js is optional, not mandatory: avoid introducing a second scheduler unless it solves a demonstrated need.
- IndexedDB (e.g., idb) for reading state and imported content; localStorage acceptable for small settings.
- Web Worker for preprocessing/analysis when necessary.
- Vitest for unit tests and Playwright for end-to-end tests.
- No server required after `npm run build`; static hosting should work. Keep all assets local after first load.

Before coding, verify the current Strudel package APIs and browser audio lifecycle. Isolate Strudel integration behind an adapter so that API changes do not affect narrative or UI logic.

## 4. Architecture
```
Book asset / import
  -> Parser -> Book / Chapter / Paragraph IDs
  -> Analyzer -> Raw narrative features and evidence
  -> Timeline processor -> Smoothed features, scene boundaries
  -> Score director -> Musical targets, motifs, transition policy
  -> Strudel adapter -> Persistent patterns/layers -> Web Audio output
                 ^
                 |
          Reader position events
```

Separate parsing, narrative analysis, score planning, audio rendering, and UI. The reader sends paragraph position events; it must not manipulate synthesiser parameters directly.

### Suggested modules
```
src/
  app/
  components/Reader.tsx
  components/Transport.tsx
  components/DebugOverlay.tsx
  books/types.ts
  books/parseText.ts
  books/sampleBook.ts
  analysis/lexicons.ts
  analysis/extractFeatures.ts
  analysis/smoothTimeline.ts
  analysis/detectBoundaries.ts
  score/types.ts
  score/mapFeatures.ts
  score/director.ts
  score/motifs.ts
  audio/StrudelAdapter.ts
  audio/presets.ts
  persistence/store.ts
  workers/analyze.worker.ts
  tests/
```

## 5. Data contracts
Use strict TypeScript types and validation for imported/persisted content.

```ts
type Paragraph = {
  id: string;             // stable: bookId:chapterIndex:paragraphIndex
  chapterId: string;
  index: number;
  text: string;
};

type NarrativeFeatures = {
  valence: number;        // [-1, 1], negative to positive
  arousal: number;        // [0, 1], calm to energetic
  tension: number;        // [0, 1]
  mystery: number;        // [0, 1]
  wonder: number;         // [0, 1]
  action: number;         // [0, 1]
};

type ParagraphAnalysis = {
  paragraphId: string;
  raw: NarrativeFeatures;
  smoothed: NarrativeFeatures;
  evidence: Array<{ feature: keyof NarrativeFeatures; token: string; weight: number }>;
  sceneBoundaryScore: number;
};

type MusicalTarget = {
  intensity: number;       // [0, 1]
  density: number;         // [0, 1]
  brightness: number;      // [0, 1]
  dissonance: number;      // [0, 1]
  spaciousness: number;    // [0, 1]
  pulseStrength: number;   // [0, 1]
  motifId?: string;
  accent?: 'none' | 'subtle-hit';
};
```

Persist an analysis version alongside cached results so rule changes invalidate stale caches. Clamp all feature values and use safe defaults for empty paragraphs.

## 6. Text ingestion and reading UI
- Ship a curated UTF-8 or JSON version of the source book with explicit chapter/paragraph structure. Confirm edition and public-domain status for the distribution jurisdiction; retain attribution/source metadata and do not copy third-party modern editorial material without permission.
- Ignore headings and blank lines when assigning paragraph navigation; preserve chapter headings separately.
- Never split paragraphs by arbitrary character count. Very long paragraphs must scroll within the reader rather than overflow the viewport.
- Display only one narrative paragraph at a time. The current paragraph is the exact tracking unit.
- Keyboard: Right/Space = next, Left = previous, with sensible exclusions for focused controls. Support touch buttons and screen-reader labels.
- Save progress on every navigation event; restore after reload.
- Reader position changes must be debounced only for audio scheduling, never for UI/progress persistence.
- Default audio OFF until an explicit user gesture starts playback, to comply with browser autoplay policies.

## 7. Deterministic NLP — phase one
Do not require training data for the first vertical slice.

### Feature extraction
- Tokenise and normalise text, retaining sentence boundaries and punctuation.
- Use versioned, auditable lexicons of unigrams, bigrams, and selected trigrams with per-feature weights. Include negation handling within a short window, basic intensifiers, and capped frequency contributions.
- Add structural cues: exclamation marks, sentence length, action verbs, abrupt sentence patterns, question marks, and uncertainty markers.
- Calculate each feature as a weighted combination of lexical and structural signals, normalised to its declared range. Include evidence records for debugging.
- Do not treat lexical novelty alone as tension or as a confirmed scene change.
- Use a small hand-annotated evaluation set from the bundled book to tune rules; store annotations separately from algorithm output.

### Temporal processing
- Compute raw features per paragraph, then a contextual series using a weighted window of preceding/current/following paragraphs for the precomputed timeline. Do not allow future paragraphs to trigger premature accents or reveal plot twists.
- Apply runtime exponential smoothing to the musical targets: `state = state + alpha * (target - state)` at a fixed update interval; choose attack/release rates per parameter rather than a single alpha.
- Use hysteresis and minimum dwell times for discrete musical-state changes.
- Provide a `surprise` or abrupt-change detector based on changes in *current* paragraph features only, with a conservative threshold and cooldown.
- Track motif activation through an explicit, editable keyword/phrase mapping for the sample book. Only activate a motif when its associated concept has been encountered by the reader.

### Phase-two optional classifier
After baseline evaluation, optionally train a **non-generative** TF-IDF word 1–3-gram and character n-gram logistic-regression model for the same narrative features. Train offline in Python, export compact coefficients/vocabulary or ONNX, and run inference locally. Do not add this until it demonstrably improves held-out literary-passage performance over rules. Split evaluation by passage/chapter/book to avoid near-duplicate leakage.

## 8. Musical direction rules
The score is ambient-first, never a literal sonification of individual words. Keep a persistent tonal centre and thematic identity across adjacent paragraphs. Treat the mappings below as tunable artistic heuristics, not universal psychological laws.

| Narrative dimension | Primary musical effect | Guardrail |
|---|---|---|
| High tension | Increased dissonance, subtle modulation, narrower unresolved intervals | Do not automatically increase volume |
| High mystery | Sparse notes, ambiguous voicings, longer tails | Maintain clarity and avoid clutter |
| High wonder | Wider register, open intervals, airy textures | Avoid constant bright crescendos |
| High action/arousal | Increased rhythmic density and pulse | Cap intensity for reading |
| Negative valence | Darker voicings and lower brightness | Do not equate negative with minor mode in every case |
| Calm/low arousal | Thin arrangement, slower changes, more space | Allow near-silence |

### Initial musical palette
- Default: low analogue-style drone; slow, warm pad; sparse sine/bell-like motif; very quiet filtered pulse.
- A single consistent tonal centre for the opening chapter, with limited harmonic vocabulary (e.g., D pedal, open fifths, occasional Phrygian colour). This is an artistic preset, not a strict rule.
- No borrowed film melodies or samples. Use original synthesis patches and patterns.
- At least four layers with independently controllable gain and parameter targets.
- Changes to gain/filter/pan should interpolate smoothly; structural pattern changes should be quantised to musical boundaries where feasible.
- Musical state must survive paragraph changes without recreating the entire audio graph.
- A short accent is optional for high-confidence abrupt events, with a cooldown and a low maximum level.
- Master gain must have an accessible volume control, mute and a hard safety ceiling; avoid unexpectedly loud transients.

### Example feature mapping (starting point only)
```
intensity      = clamp(0.10 + 0.25*arousal + 0.20*action + 0.15*tension)
density        = clamp(0.05 + 0.40*action + 0.20*arousal)
dissonance     = clamp(0.05 + 0.45*tension + 0.15*mystery)
spaciousness   = clamp(0.45 + 0.35*wonder + 0.15*mystery)
pulseStrength  = clamp(0.05 + 0.55*action + 0.20*tension)
brightness     = clamp(0.35 + 0.25*valence + 0.15*wonder - 0.15*tension)
```
`clamp(x)` means bound to `[0,1]`. These parameters control a composer/state machine, not direct one-to-one note generation.

## 9. Strudel integration requirements
- Build `StrudelAdapter` with `initialize()`, `start()`, `stop()`, `setMasterVolume()`, `applyTarget(target, transitionMs)`, and `dispose()`.
- Use stable patterns and independent layers. Avoid regenerating/evaluating arbitrary code from book text.
- Keep a coherent tempo/clock; do not reset phase on paragraph changes.
- If Strudel cannot smoothly interpolate a given synth parameter, implement controlled gain crossfades or swap patterns on the next musical boundary.
- Handle suspended AudioContext, browser tab backgrounding, rapid navigation, and device audio interruptions.
- Provide a silent/mock adapter for automated tests.
- Confirm real browser playback in Chrome and Safari, including iOS Safari if accessible.

## 10. State machine and timing
States are optional high-level orchestrations (`ambient`, `suspense`, `discovery`, `action`, `aftermath`), not hard classifications of paragraphs. Feature vectors remain the primary input.

- Update target on paragraph navigation; interpolate continuously over approximately 4–20 seconds depending on parameter and narrative change.
- Apply minimum dwell times to avoid rapid state flapping.
- Never use lookahead to pre-announce surprise events. Lookahead may prepare assets or smooth benign scene transitions silently.
- If reader moves backward, return to the corresponding score state gracefully, without replaying loud accents by default.
- If reader advances rapidly, cancel superseded transitions and converge to the latest target.
- If idle, maintain a stable low-activity soundscape rather than endlessly increasing intensity.

## 11. Accessibility and UX
- Audio off by default; clear play/pause and volume controls.
- Reduced-motion support; no animated visualiser required.
- Reader settings: font size, line width, theme, line spacing.
- Good contrast, keyboard navigation, focus indicators, and semantic controls.
- Respect system preferences and browser audio restrictions.
- Debug overlay off by default and accessible via a developer toggle.

## 12. Testing and acceptance criteria
### Functional
- Opening the app displays the sample book and first paragraph without network requests to inference services.
- Next/previous navigation updates exact paragraph ID and restores progress after refresh.
- Sound starts only after explicit user interaction.
- Music continues uninterrupted when changing paragraphs; no audible restart, stuck note, or obvious click in ordinary use.
- An action-heavy passage raises pulse/density relative to a calm passage; a mysterious passage changes timbre/spacing without necessarily raising loudness.
- Rapidly moving through 20 paragraphs does not leak voices, crash, or create accumulating transitions.
- Mute/stop releases all audible voices promptly.

### Automated
- Parsing tests preserve paragraph order and stable IDs.
- Analysis tests include positive/negative/negated phrases, empty text, and repeatability.
- Feature output remains in declared numeric ranges.
- Smoothing tests verify convergence and hysteresis.
- Mapping tests verify monotonic effects for key dimensions and bounded gain.
- Persistence round-trip test.
- Playwright smoke test for navigation, persistence, audio start gesture, and mock adapter state changes.

### Subjective evaluation
Create a 15–20 paragraph annotated demonstration spanning calm, wonder, suspense, and action. Add a comparison mode: silence, fixed ambient score, adaptive score. Ask test readers to rate immersion, distraction, continuity, and whether changes feel premature. Record qualitative notes; do not claim adaptive music improves reading until tested.

## 13. Delivery plan
### Milestone 1 — playable vertical slice (highest priority)
- Vite/React app, curated chapter-one text, paragraph navigation, progress persistence.
- Strudel adapter with four atmospheric layers, manual controls for tension/mystery/action/wonder, and smooth transitions.
- Confirm browser audio works before adding NLP.

### Milestone 2 — deterministic narrative automation
- Lexicons, phrase matching, structural cues, feature timeline, smoothing, debug overlay.
- Paragraph changes automatically update the score.
- Hand-annotated fixture and tests.

### Milestone 3 — polish and narrative continuity
- Scene transitions, motif keyword mapping, chapter navigation, accessibility, edge cases, audio lifecycle robustness.
- User study comparison mode.

### Milestone 4 — optional research
- Evaluate TF-IDF n-gram classifier against rules on held-out literary passages.
- Only ship classifier if the measured improvement justifies model complexity.

## 14. Instructions to coding agent
1. Inspect repository and package versions before making assumptions; use current documented Strudel browser APIs.
2. Implement milestone 1 end-to-end first. Do not scaffold an elaborate backend or train a model.
3. Keep domain logic framework-independent and expose a testable audio adapter interface.
4. Prefer simple deterministic behaviour and audible quality over feature count.
5. Add tests alongside each module; run build, unit tests and browser smoke tests.
6. If an integration cannot be verified, document the issue explicitly rather than silently substituting a different music engine.
7. Provide `README.md` with install/run commands, architecture, music controls, known limitations, source/rights attribution, and next milestones.
8. Include a short demo script identifying sample paragraphs where the soundtrack changes meaningfully.

**Definition of done for the initial agent pass:** a user can open the local web app, start the synthesiser with one click, read chapter one paragraph by paragraph, hear a continuous adaptive score driven by deterministic narrative features, and inspect why musical parameters changed. No LLM or external AI service is involved.

## 15. Narrative graphs and choose-your-own-adventure stories

The later discussion explicitly adds a narrative graph from the beginning. Linear paragraph indices remain useful for display, but must not be the sole representation of reading position. A linear book is a graph whose ordinary nodes have one forward edge; a branching story has labelled choices and may contain loops or reconverging paths.

### Minimum graph contract

```ts
type StoryNode = {
  id: string;                 // stable within this story revision
  chapterId?: string;
  paragraphs: Paragraph[];    // initial implementation: one paragraph per node
  nextNodeId?: string;        // linear continuation; absent at a choice or ending
  choices?: Array<{ id: string; label: string; targetNodeId: string }>;
};

type StoryGraph = {
  id: string;
  revision: string;
  startNodeId: string;
  nodes: Record<string, StoryNode>;
};

type ReadingPosition = {
  storyId: string;
  storyRevision: string;
  nodeId: string;
  paragraphId: string;
};

type ReadingSession = {
  position: ReadingPosition;
  history: ReadingPosition[]; // actual traversal, not nodeId minus one
  encounteredMotifIds: string[];
};
```

These are proposed extensions to section 5. Validate duplicate IDs, missing edge targets and start nodes, empty nodes, and malformed choices. Cycles are valid and must not cause unbounded preprocessing. A chapter/paragraph ID is stable within a content revision; persist the revision to detect incompatible edits.

### Reader and score behaviour

- Implement ordinary linear navigation and optional labelled choices using the same position-event interface. Include a small original branching fixture alongside the linear sample; full interactive-fiction import is deferred.
- At a choice, present accessible buttons; do not silently select a branch through the ordinary Next control. At an ending, show an explicit ending state.
- Previous follows the actual visit history. Revisiting a node is a new visit; do not assume graph position can be expressed as a global percentage. Show node/chapter progress for linear books and visited passages or path history for branching stories.
- Persist the selected path, position, settings and encountered motifs locally. Define backtracking as restoring the prior story position and its narrative context; avoid replaying one-shot accents by default.
- Emit the destination position after a choice. The audio renderer receives a musical target rather than interpreting story edges or book text.
- Retain musical identity across branches. For example, investigating a signal may introduce an unresolved motif; escaping may reduce it and increase pulse. These are authored design examples, not automatic semantic guarantees.
- Analyse nodes individually, then aggregate context along the traversed path. Never smooth across unrelated branches by array order. An unchosen branch must not affect audible mood, motifs or accents; asset preparation may remain silent.
- Cache raw features by story revision, node/paragraph ID and analysis version. Path-dependent smoothing and motif memory belong to the reading session, not a globally cached node score.

### Import roadmap

Traditional linked EPUBs can represent simple branching through internal links; complex variables and conditions need a richer story runtime. Investigate EPUB hyperlink conversion, Twine, Spiner and Ink after the core soundtrack works. Spiner's documented Twine-to-EPUB conversion does not support arbitrary scripting. Ink is a candidate for later conditional narrative logic, not a required MVP dependency. Do not claim that importing a linked EPUB preserves every interactive-fiction mechanic.

Add acceptance checks for both branches, a reconverging path, a loop, history-based backtracking, reload/resume, missing targets, and the absence of musical cues from unvisited branches.

## 16. Portable narrative and musical representation

Keep story parsing, feature extraction and score direction independent of React and Strudel. Serialisable, versioned data should connect these stages:

```text
Story graph + current position + traversed context
  -> Narrative features + evidence
  -> Score director + motif memory
  -> Musical target + transition policy
       -> Web: Strudel / Web Audio
       -> Future embedded port: native synthesiser / PCM or I²S
```

Extend the musical target envelope with `schemaVersion`, story/node/paragraph IDs, a monotonically increasing navigation sequence, preset version, optional deterministic seed and transition duration. Newer navigation supersedes pending older targets. Treat all imported musical metadata as bounded data, never executable code. A seeded procedural pattern may be repeatable without forcing playback to restart at each node.

Precompute text features locally at import where useful, while mixing and arranging live at the reader's pace. On constrained future hardware, optionally transfer a book plus precomputed metadata from a computer; that is an alternative deployment mode. The preferred standalone Android target should ultimately perform reading, analysis and synthesis on the same device. Pre-rendered original stems with crossfades remain a fallback experiment for old hardware, not a replacement for the web reference implementation.

Offline-first means caching the application shell, fonts, content, presets and any required samples for subsequent offline launches. Static hosting alone does not guarantee offline reload. Add a service worker/cache strategy before claiming offline installation, handle storage eviction, and verify the full reading/audio flow with networking disabled after initial setup. Avoid runtime CDN/sample dependencies. No reader text needs to leave the device.

## 17. E Ink roadmap and hardware decision record

**Final direction from the conversation:** build the web application first, then evaluate an Android-based E Ink reader with audio for a completely standalone experience. The Meebook M7 became the provisional first prototype candidate, with the BOOX Go 6 (Gen II) an alternative. These are historical research candidates, not verified compatibility or current purchase recommendations. Neither has been tested with Awen. Recheck the exact hardware revision and vendor specifications before procurement; prices and specification tables from the exploratory chat are not requirements.

| Route explored | Reason to retain it | Limitation / decision |
|---|---|---|
| Android E Ink: Meebook M7; BOOX Go 6 (Gen II); earlier BOOX Palma suggestion | Reuse browser application and Strudel, aiming for on-device analysis and audio | Preferred next hardware experiment; verify browser, output path, background playback and battery |
| ESP32 E Ink: LilyGo T5 S3, M5Stack PaperS3/M5Paper, Xteink X4 Pro, Inkplate | Dedicated low-power reader and open firmware exploration | Later native audio port; do not assume modern browser/Strudel execution |
| CrossPoint Reader | Existing open-source E Ink firmware worth investigating for EPUB, links and navigation | Verify precise reading-position hooks and firmware/device support; no Awen integration exists |
| KOReader; Linux E Ink / PineNote | Alternative reader integration and native execution research | Paragraph hooks, audio path and performance need experiments |
| Old jailbroken Kindle with headphone output | Potential reuse of existing hardware with native synthesis or stems | Model was never confirmed; headphone socket does not prove modern Web Audio or real-time synthesis capability |
| E Ink reader plus phone/computer audio | Easier bridge to evaluating reading on E Ink | Optional prototype only; does not meet the user's preferred standalone goal |

The Xteink recommendation was revised after the Bluetooth-audio discussion. Bluetooth hardware or BLE accessory support is not evidence of headphone audio/A2DP support. The chat did not establish working standalone X4 Pro audio. Do not carry the earlier purchase recommendation forward as the final choice.

### Hardware acceptance gate

1. Run the complete web app offline on the candidate device, including import/analysis, reading, path restoration and synthesis.
2. Test sustained four-layer audio during E Ink refreshes, book access, rapid navigation and branch selection; record glitches, CPU/memory use and responsiveness.
3. Test actual supported headphone routes, interruptions, mute/stop, suspend/resume, browser backgrounding and screen sleep. Do not promise locked-screen playback before measurement.
4. Measure battery drain for silence, fixed ambience and adaptive audio under comparable conditions. Record device, OS, browser, volume/output path and session duration.
5. Make the interface suitable for E Ink: high contrast, minimal animations, explicit touch/physical-button navigation, infrequent redraws, readable focus and choice labels.

### Optional embedded research

The chat proposed a C/C++ synthesiser using sine/triangle/saw/noise voices, envelopes, filters and modest delay, with I²S DMA audio independent of display/storage work. Exploratory targets were 4–8 voices, 22.05 or 32 kHz, and 16-bit stereo; these are unmeasured starting budgets. Check DAC, amplifier, power and pin availability per board. A speaker amplifier is not automatically a headphone output. An ESP32 implementation requires a renderer port, audio hardware integration and scheduling work; it is not the next MVP milestone.

## 18. Additional analysis and composition research notes

These notes retain ideas discussed beyond the baseline specification. They are candidates for evaluation, not additional mandatory MVP scope.

- **Representation:** distinguish valence/arousal from tension, mystery, wonder and action. A quiet paragraph can still be ominous. Atmosphere, setting, scale, sadness and nostalgia are possible later annotations; retain the six-feature baseline until evidence supports extensions.
- **Context:** compare paragraph-only analysis, preceding-passage context, scene aggregation and explicit entity/motif memory. Narrative interpretation of irony, retrospect and foreshadowing remains a limitation of lexical methods.
- **Alternative NLP:** sentiment/emotion dictionaries, structural cues, lightweight named-entity recognition, change-point detection and embeddings were explored. Small transformer classifiers were mentioned as non-generative alternatives, but are not selected for the baseline.
- **N-gram research:** evaluate TF-IDF word 1–3-grams, character n-grams, logistic regression and optionally linear SVMs. Literary prose must be evaluated separately from social-media training corpora. Classifier confidence is not a measure of narrative truth.
- **Change detection:** cosine distance between adjacent TF-IDF passage windows may suggest topic shifts. Zero/empty vectors need defined handling. Lexical distance alone must not trigger tension, accents or a new scene.
- **Motifs:** repeated phrases such as the cylinder, the Martians or the heat-ray can support hand-authored motif activation. Keep book-level musical identity separate from local mood. Phrase matching does not establish coreference or hidden narrative significance.
- **Composition:** vertical remixing adds/removes layers; horizontal resequencing selects compatible phrases; leitmotifs retain identity; restrained modulation and timbral changes vary expression. Musical memory should follow encountered material and the actual story path.
- **Restraint:** an exploratory 70% ambient/near-silent, 20% development, 10% emphasis balance was suggested in the chat. It is an artistic starting point, not a research finding or a fixed quota. Silence and near-silence remain legitimate score states.
- **Emotion rules:** mode, tempo, register, dynamics, articulation and timbre were discussed as controllable cues, drawing on Juslin and Lindström and Eerola, Friberg and Bresin. Their studies concern perceived musical expression; applying them to reading soundtracks is a design inference requiring evaluation. Avoid universal major/happy or minor/sad rules.
- **Inspirations:** SSX Tricky supplied the idea of responsive layering; Dune and radio/film scoring supplied atmospheric restraint, space and recurring themes. These are creative references, not evidence about their exact implementations and not permission to reproduce their assets.

## 19. Research landscape and superseded alternatives

The original chat's landscape scan named BookMusic, Aufera, Underscored, Taleody, StoryDrop, Novelody and Moodreads. Preserve these as research leads, not an independently tested feature comparison or proof of novelty.

| Lead from the chat | What the chat proposed investigating | Evidence status for this revision |
|---|---|---|
| [BookMusic](https://github.com/damianogiorgi/BookMusic) | Local LLM writing Strudel patterns; section tracking and continuity | Repository description rechecked; software not installed or benchmarked. Its LLM approach is outside Awen's design |
| [Aufera](https://play.google.com/store/apps/details?id=com.aufera.app) | Scene emotion and reader-paced accompaniment | Chat-reported product claims; not independently validated here |
| [Underscored](https://underscored.app/) | Story arcs, themes, motifs and transitions | Chat-reported claims; not independently validated here |
| Taleody | Adaptive reading ambience | Name and description retained from chat; authoritative source still to establish |
| [StoryDrop](https://johnsear.com/project/storydrop/) | Public-domain books with music in a web experience | Chat-reported lead; not independently validated here |
| Novelody | Chapter soundtracks and progress | Name and description retained from chat; authoritative source still to establish |
| Moodreads | Book-related music and environmental ambience | Name and description retained from chat; authoritative source still to establish |

Early brainstorming included LLM book analysis, generated Strudel code, MusicGen/Stable Audio stems, a Python/FastAPI backend, Pydantic, SQLite and continuous inference. The user's subsequent no-LLM preference superseded that route. None is required for Awen. Tone.js was an alternative audio engine; the settled browser reference uses Strudel with an adapter and Web Audio. EPUB/epub.js import remains a later candidate rather than a dependency for the curated chapter slice. No competitor has been comprehensively benchmarked, so do not claim Awen is the first or uniquely combines these features.

The research also explored preprocessing a whole book versus composing while reading. The retained approach is local feature preprocessing plus live procedural arrangement, with reader-gated motifs and no spoiler-producing lookahead.

## 20. Extended delivery plan, sources and traceability

The original milestones remain in order, with the following additions:

- **Milestone 1 extension:** introduce the graph abstraction and a tiny branching fixture while developing the linear chapter and manually controlled score. Do not build a full story-authoring system.
- **Milestones 2–3 extension:** automate path-aware features, persist traversal/motif context, demonstrate choices and backtracking, and complete verified offline caching.
- **Milestone 4:** evaluate lightweight classifiers, context windows, musical mappings and fatigue. Compare an authored timeline as a diagnostic reference as well as silence/fixed/adaptive conditions.
- **Milestone 5:** test the web reference on a standalone Android E Ink candidate using the acceptance gate in section 17.
- **Later research:** general EPUB/linked-book import, Twine/Spiner/Ink adapters, richer story state, KOReader/CrossPoint integration and embedded synthesis.

### Source register

The [shared research conversation](https://chatgpt.com/share/6ade700d-4de0-83eb-8450-8a17bb002f5b) is the design-history source, reviewed on 25 October 2026 alongside the user-supplied original specification. The consolidation covers concept and landscape research, no-LLM refinement, n-grams and emotion rules, the initial specification, Kindle/ESP32 alternatives, branching stories, the Xteink audio correction, the standalone Android direction and the selected Awen name. Alternative name brainstorming was naming history rather than a product requirement; Awen is the selected name.

Research and technical sources retained or checked for the accompanying paper:

- Juslin and Lindström, [Musical Expression of Emotions: Modelling Listeners' Judgements of Composed and Performed Features](https://doi.org/10.1111/j.1468-2249.2011.00323.x).
- Eerola, Friberg and Bresin, [Emotional expression in music: contribution, linearity, and additivity of primary musical cues](https://pmc.ncbi.nlm.nih.gov/articles/PMC3726864/).
- [Strudel technical manual](https://strudel.cc/technical-manual/repl/).
- [Spiner documentation](https://spiner.readme.io/docs/getting-started) and [Ink](https://www.inklestudios.com/ink/).
- [CrossPoint Reader](https://crosspointreader.com/) and its [release notes](https://github.com/crosspoint-reader/crosspoint-reader/releases). Device support is not evidence of Awen compatibility.

See [paper.md](paper.md) for the academic-style background, proposed methods, evidence limitations and references. Additional literature introduced during documentation is labelled there; it is not represented as research already present in the original chat.
