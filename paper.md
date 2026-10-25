# Awen: An Offline-First E-Reader for Adaptive Procedural Narrative Soundtracks

**Working research paper / system proposal**  
**Date:** 25 October 2026  
**Implementation status:** Design documentation; no implemented system, participant study or measured results are reported.

## Abstract

Reading permits each reader to determine the pace of a narrative, complicating synchronisation with a fixed soundtrack. Awen proposes a browser-based e-reader in which explicit paragraph navigation controls a continuous procedural score. Lightweight lexical and n-gram analysis estimates narrative features, while a separate score director translates those features into restrained changes in synthesis, instrumentation and musical structure. Strudel supplies the planned browser rendering engine. The design excludes large language models and generative audio models and targets local analysis, storage and playback. A graph representation extends the approach to branching stories, where scoring context depends on the reader's actual path. A subsequent hardware stage targets a standalone Android E Ink reader; constrained embedded implementations remain exploratory. This paper develops the motivation, research background, architecture and an evaluation protocol comparing silence, fixed ambient music and adaptive scoring. Benefits to immersion, comprehension and sustained reading remain hypotheses.

**Keywords:** adaptive music; digital reading; procedural composition; natural language processing; n-grams; interactive fiction; offline computing; E Ink.

## 1. Introduction

A fixed recording advances in clock time, whereas a reader may pause, reread, skim or choose another narrative path. A soundtrack organised only around estimated reading speed can therefore become detached from the text being displayed. Awen addresses this coordination problem by presenting one paragraph at a time and treating navigation as an explicit control signal. This identifies the displayed paragraph, not the precise word being read or the reader's psychological state.

The design emerged from a discussion of atmospheric science-fiction scoring, radio adaptations and the responsiveness of game soundtracks. Dune and SSX Tricky were creative reference points for space, restraint and responsive layering. These references motivate an aesthetic; they do not establish the internal design of those soundtracks or justify reproducing their music.

The proposed contribution is an inspectable pipeline connecting local narrative features, path-aware context and continuous procedural composition. Awen is Welsh for *poetic inspiration*. Its immediate target is a web reader using the opening chapter of *The War of the Worlds*. The long-term aim is a self-contained E Ink reading device and support for suitably licensed linear and branching fiction.

This is a system proposal, not a report of a validated intervention. The implementation requirements are maintained in the [companion specification](adaptive_reading_soundtrack_spec.md).

## 2. Background and related work

### 2.1 Reading soundtracks and existing systems

The originating conversation surveyed BookMusic, Aufera, Underscored, Taleody, StoryDrop, Novelody and Moodreads [1]. That scan is a set of leads rather than a systematic review. Several descriptions were based on product claims, and the systems were not independently tested.

BookMusic is a directly relevant technical reference. Its repository describes using a small local LLM to produce Strudel patterns for reading sections, advancing music with reading progress and carrying previous musical code forward for continuity [2]. Awen instead proposes explicit feature extraction and authored composition rules. That is an architectural distinction, not evidence of superior music, lower measured energy use or unique novelty.

The other leads suggest useful comparison dimensions: temporal granularity, whether music is synthesised or selected, handling of character motifs, and dependency on remote services. Their current availability and implementation details require primary-source verification before inclusion in a publication-quality comparative review. Appendix A preserves the original leads without treating them as established findings.

### 2.2 Musical cues and perceived emotion

Juslin and Lindström systematically manipulated composed and performed features and modelled listener judgements of emotional expression [3]. Their study supports investigating multiple musical controls rather than assuming a single tempo or mode determines expression. It does not establish a direct mapping from literary meaning to an optimal reading soundtrack.

Eerola, Friberg and Bresin examined the contribution, linearity and additivity of musical cues [4]. Their work motivates testing a simple, bounded mapping as an interpretable starting point. Awen's proposed weights are artistic hypotheses, not coefficients transferred from that experiment. Cultural context, individual preference and the difference between perceived expression and induced feeling limit generalisation.

Valence and arousal provide useful conceptual axes, but the system also separates tension, mystery, wonder and action. A passage may describe little action while remaining ominous. Musical identity is likewise separated from local mood: a recurring motif can retain its recognisability while its timbre, register or accompaniment changes.

### 2.3 Text analysis without language generation

The original discussion proposed TF-IDF word and character n-grams with logistic regression or a linear SVM, alongside deterministic dictionaries, punctuation and structural features [1]. Such representations provide inspectable inputs but do not resolve irony, narrative distance or retrospective descriptions. A fearful word is not sufficient evidence that an immediate dramatic accent is appropriate.

As an additional literature lead introduced during documentation, Mohammad and Turney describe constructing an emotion lexicon through human annotation [5]. This offers a precedent for lexical associations; it does not supply labels for every narrative dimension or establish accuracy on novels. Awen should begin with versioned rules and a small independently annotated literary evaluation set. Any external lexicon requires licence and domain-suitability checks.

### 2.4 Procedural scheduling and narrative structure

Strudel's technical documentation describes querying patterns over time spans and scheduling resulting events, with Web Audio as the reference environment's default output [6]. This supports the architectural choice to maintain a musical clock while changing targets and layers. Audible continuity still requires implementation and listening tests; it is not guaranteed by selecting an engine.

Branching narratives require a different context model from a single chronological sequence. Spiner documents a Twine-to-EPUB workflow for traditional linked gamebooks while explicitly excluding arbitrary scripting [7]. Ink provides an established narrative language and tooling for branching stories [8]. These systems are future interoperability candidates. The first Awen implementation should use a small native graph fixture rather than attempting complete format compatibility.

### 2.5 Distraction as a competing outcome

An additional study located during documentation, Souza and Barbosa, compared silence, instrumental music and music with lyrics across cognitive tasks [9]. Their results include interference from lyrical music and no credible performance improvement or impairment from the tested instrumental condition. These findings concern the tested materials and tasks; they do not establish the effects of adaptive synthesis during literary reading.

Consequently, enjoyment and perceived immersion must be measured separately from comprehension. Instrumental, quiet or slowly changing music cannot simply be presumed harmless, and subjective preference cannot substitute for objective reading outcomes.

## 3. Research questions

1. **Narrative fit:** Can lightweight, local text features drive musical changes that readers judge appropriate to the displayed passage?
2. **Experience and comprehension:** How does adaptive scoring compare with silence and fixed ambience in immersion, distraction, enjoyment and comprehension?
3. **Continuity:** Do smoothing, state hysteresis and persistent motifs improve perceived coherence relative to immediate paragraph-by-paragraph changes?
4. **Branching:** Can traversed-path context preserve motif continuity without audible information from unvisited alternatives?
5. **Deployment:** Can the same web pipeline operate offline on an audio-capable E Ink reader with acceptable responsiveness, reliability and battery use?

The directional hypothesis is that appropriate adaptive scoring may increase immersion relative to fixed ambience. Whether comprehension remains comparable must be tested with a prespecified analysis and adequate precision; a non-significant difference alone would not establish equivalence.

## 4. Proposed system

### 4.1 Reader and story graph

A story is a directed graph with stable node IDs, paragraph content, optional sequential edges and labelled choices. Linear chapters are a special case. A reading session records story revision, current node and paragraph, traversal history, and encountered motifs. Backtracking follows history rather than an arithmetic paragraph predecessor. Loops and converging branches are valid.

The displayed paragraph provides an explicit location signal. Long paragraphs may scroll, so navigation cannot determine when a particular sentence has been read. This constrains accent timing and is a reason to keep abrupt musical events conservative.

### 4.2 Analysis and path context

For paragraph t, define a bounded feature vector:

```text
e_t = [valence, arousal, tension, mystery, wonder, action]
```

The baseline matches weighted unigrams, bigrams and selected trigrams, applies limited negation and intensifier handling, and incorporates structural cues. Evidence records expose the tokens and weights contributing to each feature. Cached raw results are versioned independently of runtime smoothing.

A later classifier experiment uses TF-IDF word 1–3-grams and character n-grams. Training may occur offline, with compact parameters exported for local inference. Adoption requires improvement on held-out literary passages relative to the rules. Splitting by chapter or book reduces leakage from adjacent or near-duplicate passages.

Context aggregation follows the traversed path. A global array neighbourhood would incorrectly mix unchosen alternatives in branching fiction. The system may prepare assets silently in advance, but audible features, motif activation and event accents must not disclose future or unvisited content.

### 4.3 Musical direction and inertia

The director derives musical targets through an initial bounded mapping:

```text
target_t = clamp(W * contextual_features_t + b)
state_next = state + alpha * (target_t - state)
```

The first expression defines tunable target parameters; the second represents runtime smoothing at a fixed update interval. Separate attack and release rates, state hysteresis and minimum dwell times prevent unstable transitions. Approximate transitions of 4–20 seconds are initial design settings requiring listening evaluation. Rapid navigation cancels superseded targets.

The initial arrangement contains drone, harmonic texture, sparse motif and pulse/tension layers. Mystery may influence spacing and ambiguity; action may increase pulse and density; wonder may open register and texture. Tension need not raise loudness. All mappings are constrained by a persistent tonal identity, dynamic limits and the option of near-silence.

Motifs are initially authored and activated by explicit phrase mappings. Their presence indicates an encountered concept, not automatic understanding of hidden relationships. Backtracking restores story context while avoiding repeated one-shot accents by default.

### 4.4 Rendering, portability and offline operation

React/TypeScript supplies the planned reader; Strudel is isolated behind an adapter responsible for playback and target application. Domain logic exchanges bounded musical data rather than generating executable code from prose. IndexedDB stores books, analysis and reading sessions; a worker may handle expensive preprocessing.

Offline-first operation requires the application, fonts, presets, content and any samples to remain available locally, including after restart. A static build alone does not satisfy that requirement. Offline launch, storage eviction and audio lifecycle behaviour need explicit verification. Playback begins through a user gesture and must handle suspension, interruptions and mute/stop reliably.

The serialisable musical representation also permits a later native renderer. This is a portability boundary, not a claim that Strudel can run unchanged on a microcontroller.

## 5. E Ink deployment and design history

The hardware discussion moved from an old Kindle with a headphone socket to ESP32-based readers, then to Android E Ink when standalone audio became the preferred goal [1]. The final provisional candidate was the Meebook M7, with BOOX Go 6 (Gen II) as an alternative. These names preserve the discussion's direction; neither is validated for Awen, and this paper does not reproduce transient prices or treat historical specifications as current procurement advice.

CrossPoint is an open-source firmware ecosystem worth investigating [10]. It may reduce reader implementation work, but firmware support does not demonstrate Awen integration, paragraph-position hooks or audio capability. KOReader and PineNote were also explored. Older Kindle browser capabilities and the user's exact Kindle model were not established.

For a future ESP32 port, the chat proposed a C/C++ synthesis backend, DMA-buffered I²S output and independent display/audio scheduling. Suggested budgets of 4–8 voices and 22.05/32 kHz audio were engineering starting points, not benchmark results. A reader paired with phone audio is a useful experiment but falls short of standalone operation. Bluetooth accessory support alone must not be mistaken for a verified headphone output path.

The next hardware study should record device/OS/browser versions, audio route, sustained playback during display refresh, latency, glitches, memory, and battery drain. Minimal animation and explicit controls are appropriate interface goals for the E Ink prototype.

## 6. Proposed evaluation

### 6.1 Engineering and classifier evaluation

First verify parsing, stable identifiers, bounded features, persistence, branch traversal and cache invalidation. Use deterministic fixtures covering empty text, negation, ambiguous passages, rapid navigation, loops and branch reconvergence. Measure audio continuity in real browsers rather than inferring it from mocked adapter calls.

Create a hand-annotated literary corpus with passage-level feature judgements and annotation guidance. Report agreement and disagreements before tuning rules. Choose evaluation metrics to match the eventual labels: for categorical annotations, per-label precision/recall and macro-F1; for continuous ratings, error and association measures with uncertainty. Report genre and book composition. Freeze held-out data before comparing optional classifiers.

### 6.2 Reader study

Use a counterbalanced within-participant comparison of silence, fixed ambience and adaptive scoring. Assign comparable but different passages to reduce memorisation; rotate passage-condition pairings across participants. Match the fixed and adaptive conditions in palette and approximate loudness so differences are not explained solely by sound selection or level. Allow comfortable volume adjustment and record it.

Prespecify primary outcomes and a sample-size justification. Collect immersion/enjoyment ratings, perceived distraction and premature-cue reports, comprehension questions, and reading duration. Include interviews about continuity, fatigue, unwanted interpretation and preference for silence. Do not describe custom rating questions as validated scales.

Report effect sizes and confidence intervals, account for participants and passages, and document exclusions and missing data. For a claim that comprehension is preserved, define a justified non-inferiority or equivalence margin in advance. Consider hearing differences, reading habits, genre familiarity, musical preference and language proficiency when designing recruitment and analysis.

### 6.3 Diagnostic studies

Compare automated scoring with a hand-authored timeline to separate text-analysis failures from composition failures. Ablate smoothing, motif memory and path-aware context individually. A branching fixture should include two different routes to a shared scene and an unvisited motif-bearing branch. Audible output must follow the selected route without leaking the unused branch.

Longer reading sessions are needed to assess fatigue beyond a short demonstration. E Ink trials should separately compare reading without audio, fixed ambience and adaptive synthesis under controlled display and output conditions.

## 7. Limitations and responsible interpretation

Lexical features provide a limited proxy for narrative meaning. Literary style, irony, negation scope, historical vocabulary and figurative language may produce misleading features. Paragraph presentation may itself change the reading experience, so any benefit cannot automatically be attributed to soundtrack adaptation alone. Path history provides narrative context but does not identify the reader's actual emotion.

Musical conventions vary across listeners and cultures. A coherent score may still distract, constrain imaginative interpretation or become fatiguing. No benefit is established by the architecture or cited musical-expression studies. The literature scan is selective rather than exhaustive, and competitor claims need verification.

Book editions, lexicons, sound assets and dependencies require attribution and licence review before distribution. The documents do not select a project licence or bundle third-party media. Reader studies should obtain appropriate consent and any required institutional review, with data collection minimised and separated from the ordinary offline reading experience.

## 8. Expected contribution and current status

If implemented and evaluated, Awen could provide a reproducible reference for local narrative-feature analysis, inspectable musical direction and path-aware procedural scoring. The research value would lie in measured trade-offs between continuity, narrative fit, distraction and deployment cost, rather than an unsupported claim that adaptive music necessarily improves reading. At present, the contribution is the documented design and evaluation plan; results remain to be obtained.

## References

1. **Project design discussion.** *Research adaptive reading soundtrack*. Shared ChatGPT conversation, consulted 25 October 2026. [Design-history source](https://chatgpt.com/share/6ade700d-4de0-83eb-8450-8a17bb002f5b). This is not peer-reviewed evidence.
2. **Giorgi, D.** *BookMusic*. [Project repository and README](https://github.com/damianogiorgi/BookMusic). Consulted 25 October 2026; description reviewed, implementation not benchmarked.
3. **Juslin, P. N., & Lindström, E.** (2010 volume; first published online 2011). Musical Expression of Emotions: Modelling Listeners' Judgements of Composed and Performed Features. *Music Analysis, 29*, 334–364. [DOI](https://doi.org/10.1111/j.1468-2249.2011.00323.x).
4. **Eerola, T., Friberg, A., & Bresin, R.** (2013). Emotional expression in music: contribution, linearity, and additivity of primary musical cues. *Frontiers in Psychology, 4*, 487. [DOI](https://doi.org/10.3389/fpsyg.2013.00487); [full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC3726864/).
5. **Mohammad, S., & Turney, P.** (2010). Emotions Evoked by Common Words and Phrases: Using Mechanical Turk to Create an Emotion Lexicon. *Proceedings of the NAACL HLT 2010 Workshop on Computational Approaches to Analysis and Generation of Emotion in Text*, 26–34. [ACL Anthology](https://aclanthology.org/W10-0204/). Additional source introduced during documentation.
6. **Strudel contributors.** *Technical manual: REPL*. [Official documentation](https://strudel.cc/technical-manual/repl/). Consulted 25 October 2026.
7. **Spiner.** *Getting Started with Spiner*. [Project documentation](https://spiner.readme.io/docs/getting-started). Consulted 25 October 2026.
8. **inkle.** *ink: A narrative scripting language for games*. [Official project page](https://www.inklestudios.com/ink/). Consulted 25 October 2026.
9. **Souza, A. S., & Barbosa, L. C. L.** (2023). Should We Turn off the Music? Music with Lyrics Interferes with Cognitive Tasks. *Journal of Cognition, 6*(1), 24. [DOI](https://doi.org/10.5334/joc.273); [PubMed record](https://pubmed.ncbi.nlm.nih.gov/37152835/). Additional source introduced during documentation.
10. **CrossPoint contributors.** *CrossPoint Reader*. [Project website](https://crosspointreader.com/); [release notes](https://github.com/crosspoint-reader/crosspoint-reader/releases). Consulted 25 October 2026; no Awen hardware compatibility implied.

## Appendix A. Research leads retained from the chat

| Lead | Topic recorded in the discussion | Follow-up needed |
|---|---|---|
| Aufera | Scene emotion, pace-aware listening and book imports | Verify primary product descriptions and test workflow |
| Underscored | Story arcs, character instruments, motifs and transitions | Verify current product and published evidence |
| Taleody | Adaptive reading ambience | Establish authoritative source and implementation details |
| StoryDrop | Public-domain books with music in a web experience | Inspect original project and distinguish selection from synthesis |
| Novelody | Chapter soundtracks and progress tracking | Establish authoritative source and granularity |
| Moodreads | Book-specific music and ambience | Establish authoritative source and current availability |

None of these entries is a verified comparative result. Their source descriptions and available links are retained in section 19 of the specification.

## Appendix B. Decisions and superseded approaches

The initial discussion considered LLM book interpretation, generated Strudel code, AI-generated stems and a backend. Later user preferences superseded that direction: no LLM or generative AI, local processing and Strudel-based procedural composition. Tone.js, embeddings, named-entity models and small non-generative transformers were explored but are not baseline requirements. Deterministic phrase features come first; supervised n-grams require measured justification.

The chat also proposed lexical cosine-distance change detection, recurring phrase motifs, scene-level context, horizontal resequencing and an illustrative 70/20/10 balance of near-silence, development and emphasis. These remain research ideas, not validated laws or fixed quotas. The graph abstraction and portable musical-state boundary were retained as architectural decisions; full Twine/Ink import and constrained native synthesis were deferred.

For a submission-ready paper, complete a systematic related-work search, verify the remaining product leads, select evaluation instruments and preregister the study. Add implementation details, measured results and a reproducibility package only when those artefacts exist.
