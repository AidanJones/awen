# Awen: making the continuous score feel like one piece

Review date: 25 October 2026. This document preserves the diagnosis and proposal for the previous MVP. **Implementation update:** `awen-score-2` now supplies persistent phrase/harmonic structure, seeded note planning, scene dwell/bar transitions, shared room effects and per-book checkpoints. See README for exact behaviour and verified limits. Strudel integration, character-specific leitmotifs and listening evaluation remain future work. Exact note/voicing planning is reproducible; cross-browser audio/DSP automation replay is not promised.

## Recommendation

Keep one musical composition running while the story influences its performance. A paragraph should change the direction of the score, not start another miniature composition. Add an explicit seed for reproducibility, but put musical constraints and memory around every random decision.

For *The Stainless Steel Rat*, the first authored palette should be a restrained caper/suspense score: a recognisable original motif, connected harmonic movement, soft overlapping textures and occasional short figures. It should be possible to remove the foreground melody and still hear a coherent piece. “Continuous” need not mean either an unchanging drone or constant notes.

## 1. What the implementation is doing now

Code locations refer to `index.html` as reviewed on this date.

| Observation | Code evidence | Likely audible consequence |
|---|---|---|
| Every different paragraph ID queues a new plan, even when its musical category is unchanged. At the next beat, `composeBeat` releases existing foreground notes and resets `phraseBeat` to zero. | `setPassage`, approximately line 116; `composeBeat`, approximately line 123 | Musical sentences are repeatedly interrupted. Keeping the AudioContext and global tick alive does not preserve phrase continuity. |
| The beginning of a phrase triggers bass, a three-note chord and a melody note together. | `arrange`, approximately lines 77–84 | Page turns repeatedly announce a new downbeat. This exaggerates the short-cue feel. |
| Plucks have a 15 ms attack and approximately 450 ms duration; many other melody notes are only 850 ms. There is no shared reverberant space. | `note`, approximately line 119; `arrange` | Dry, isolated attacks can sound like plonks or bleeps rather than a connected ensemble. Longer notes alone will not fix the musical structure. |
| Background oscillators approach new frequencies over two seconds. | `composeBeat` | This is a pitch glide, not voice leading or a crossfade between stable pitches. It can sound unsettled while the foreground has already changed harmony. |
| The text hash selects one of four motif rotations. | `directPassage`, approximately lines 70–75 | Deterministic variation exists, but there is no user seed, book theme or meaningful motif memory. A punctuation edit can change the rotation. |
| Six narrative dimensions produce six musical targets, but the current renderer's `applyMix` uses brightness; other target fields are not presently connected to corresponding continuous controls. Categorical plans do most of the audible adaptation. | `mapScore`, `applyMix`, `composeBeat` | The inspector suggests more continuous musical control than the renderer delivers. |
| Category thresholds and the opening-quotation rule switch plans without a persistent scene-state policy. | `directPassage` | A threat spoken in dialogue can become “dialogue music”; neighbouring paragraphs can oscillate between interpretations. |

These are implementation findings. The connection to the reported sound is an engineering/artistic diagnosis, not a controlled perceptual result. The original specification already called for motif memory, hysteresis, minimum dwell times and continuity across navigation; those requirements have not yet been fulfilled by the small composer.

## 2. What the research and established practice contribute

### Composition and expression should be separate

**Scirea, Togelius, Eklund and Risi (2017), MetaCompose.** This system separates chord-sequence generation, melody generation, accompaniment and affective performance. Its component evaluations support treating composition as a structured problem rather than substituting arbitrary notes when mood changes. The useful architectural lesson for Awen is to retain a composition and vary its interpretation. We do not need to adopt the evolutionary search, and the paper does not establish benefits for reading novels. [Author manuscript](https://marcoscirea.com/papers/metacompose-journal.pdf), [publication record and DOI](https://researcher.itu.dk/en/publications/affective-evolutionary-music-composition-with-metacompose/).

**Braga, Bernardes, Dannenberg and Correia (2025), Algorithmic Composition Using Narrative Structure and Tension.** The proceedings abstract describes character leitmotifs, harmonic grammars and control at different structural scales. It is a relevant lead for persistent themes and hierarchical planning. This review verified the proceedings abstract, not the full experimental methodology; its reported narrative-listening evaluation should not be treated as evidence that it will improve Awen's reading experience. [Original proceedings entry](https://ijcai.org/proceedings/2025/1116).

### Transitions need musical rules

**Audiokinetic's Wwise documentation** distinguishes transitions at beats, bars and cues, matching positions between segments, fades and outgoing tails. These are production capabilities, not an experiment proving an optimal transition duration. Their relevance is that a transition is an authored musical decision. A gain fade on its own does not make arbitrary changes musically compatible. Awen should normally change orchestration while retaining phrase position, and reserve structural changes for appropriate boundaries. [Source/destination transition rules](https://www.audiokinetic.com/en/library/edge/?id=setting_source_and_destination_properties&source=Help).

**65daysofstatic's account of the No Man's Sky soundtrack** describes authored musical material curated by rules. That is a practitioner example, not a reading study or a recipe for copying its sound. It supports starting with good original musical building blocks rather than expecting unconstrained randomisation to create identity. Awen can use authored note patterns and synthesis instead of recordings. [Artist interview](https://gameinformer.com/b/features/archive/2016/05/30/65daysofstatic-on-creating-no-man-39-s-sky-generative-soundtrack).

### Strudel can express patterns; it does not supply musical judgement

Strudel's scheduler queries patterns over musical time and can replace a pattern while retaining its clock. Its weighted choices and cycle-level modifiers can express constrained variation. `ribbon(offset, cycles)` repeats a selected window of a pattern, including a window of random material: its first argument is a time offset, **not a general application-wide seed API**. We should not equate that feature with complete seeded replay. [Scheduler documentation](https://strudel.cc/technical-manual/repl/), [random modifiers](https://strudel.cc/learn/random-modifiers/), [ribbon documentation](https://strudel.cc/learn/time-modifiers/#ribbon).

`@strudel/web` remains a suitable candidate for the renderer/scheduler. The documented CDN approach supports our single-file/no-build preference. Fully offline packaging and AGPL-3.0 compatibility remain integration considerations. Changing engines will not, by itself, fix phrase resets or weak melodic material. [Official integration guide](https://strudel.cc/technical-manual/project-start/).

### Reading remains a separate evaluation question

Instrumental background music is not an established comprehension aid. Souza and Barbosa's tested instrumental condition did not credibly improve or impair performance; their lyrical condition was more disruptive. That finding does not determine whether pads, strings, sparse motifs or a particular transition policy are best for Awen. We should evaluate continuity, annoyance and immersion separately from comprehension. [Original study](https://doi.org/10.5334/joc.273). See also `background_music_notes.md` for the existing reading-focused review.

## 3. Proposed musical architecture

```text
Current paragraph + already visited context
              ↓
Narrative intent: tension, activity, uncertainty, wonder, confidence
              ↓
Persistent director: current scene, dwell time, pending transition
              ↓
Seeded composer: book theme, harmonic plan, motif memory, musical cursor
              ↓
Pure bar planner → scheduled note/control events → audio renderer
              ↓
Shared effects → existing compressor / final limiter → analyser → speakers
```

The composer should own **musical time**. The reader owns **narrative position**. Reading an extra paragraph must not reset musical time. Advance the composition using a fixed musical grid, not UI frames, timer-call counts or the number of Next clicks.

Use a small authored harmonic vocabulary and a few original motif families initially. Constrain chord voicings to a comfortable register, retain common tones and choose nearby pitches for moving voices. Limit large melodic jumps and repetitions of the same attack. Develop a motif through small rhythmic changes, omission, extension and occasional register changes; do not generate a new theme per paragraph.

For an initial listening experiment, try the following **design defaults, not research-derived optimums**:

| Element | Starting policy |
|---|---|
| Pulse/grid | A stable, unhurried musical grid; trial 64–80 quarter-note BPM, default 72. Audible percussion is optional. |
| Phrases | Four-bar phrases with related answering phrases; allow longer eight-bar developments. |
| Harmony | Hold for two or four bars unless an authored transition requires otherwise. Keep the tonal centre stable. |
| Background | Overlapping, gently evolving voicings with movement in texture; avoid a permanently exposed root tone. |
| Foreground | Short original motifs that recur, with fewer isolated attacks and some connected/overlapping notes. |
| Adaptation | Texture/layer targets may begin changing over 1–3 seconds; rhythmic changes enter at a bar; harmonic changes at a compatible boundary. |
| Scene changes | Require sustained evidence, with a trial 8–12 second minimum dwell. High-confidence changes can use a shorter authored transition. |
| Ambiguous prose | Keep the existing musical direction with small expression changes. A quoted sentence is an orchestration hint, not a scene reset. |
| Space | One quiet shared room/reverb with restrained wet level. Keep all dry and wet paths before the final limiter. |

These policies trade immediate word-level responsiveness for continuity. Display the latest narrative target promptly, while making it clear that a musical transition may be pending. Coalesce rapid reading updates into the most recent target rather than queuing a cue for every paragraph. Do not use future text to anticipate reveals.

## 4. Seed and replay contract

**Yes: add a visible seed, saved per book.** A useful control would show `Score seed: rat-001`, with Apply and New interpretation actions. New interpretation chooses and saves a seed once; it must not re-randomise every paragraph or browser refresh. Keep existing volume and background controls. One additional “musical movement” control is more useful than exposing many synthesis parameters.

The seed should select a coherent interpretation: theme variant, related voicings, motif developments and restrained timing/timbre choices. It should not choose unrestricted notes, unrelated chords or output levels. Identical seed values do not make poor musical choices good.

Define separate deterministic streams for harmony, melody, orchestration and expression. Pin the hash and PRNG algorithms with test vectors; a small documented generator such as `sfc32` is sufficient for these non-security decisions. Do not use `Math.random()` inside the composer. Generate a new user seed once with browser randomness, then persist it.

Illustrative keying, not an implemented API:

```text
bookTheme = derive(userSeed, bookId, composerVersion, "theme")
choice    = derive(userSeed, bookId, composerVersion,
                   layerId, absolutePhraseIndex, decisionIndex)
events, nextState = planBar(composerState, currentIntent, choice)
```

Including a paragraph ID in an independently reset seed for every paragraph would reproduce the present fragmentation. The book theme and musical cursor must survive paragraph changes. Disabling a layer or resizing the waveform must not consume random numbers that change other layers' future composition.

There are three distinct replay promises:

1. **Same seed:** the same thematic interpretation and available musical variations.
2. **Same seed, composer/content versions, starting state and musical-time-stamped reading-event log:** the same symbolic score events. Different reading speeds legitimately lead to different adaptations.
3. **Identical audio samples across browsers:** not promised. Native synthesis/effects and scheduling implementations can differ. Audio regressions should use tolerances; symbolic composition tests should be exact.

Persist the seed, composer version, book/content revision, musical cursor and director/motif state for a resumable session. For diagnostic playback, record navigation events against musical ticks rather than wall-clock timestamps. Do not store user text remotely.

Suggested transport policy: pause freezes the musical cursor; resume continues it; book restart restarts the interpretation with the same seed and a short fade; New interpretation applies at a safe phrase boundary. Back/jump changes narrative intent without automatically replaying accents or resetting the global musical phrase. Restore motifs from encountered history; never infer them from unvisited intervening paragraphs. Document this policy before implementing it.

## 5. Implementation order

1. **Fix phrase continuity first.** Remove the unconditional `phraseBeat = 0` and blanket foreground release on normal paragraph changes. Add explicit musical bars, phrase position, scene hysteresis and a pending transition. Retain emergency mute and latest-target handling.
2. **Author one convincing Rat score.** Build a small coherent progression and one or two original motifs. Connect the background and foreground harmonically, replace frequency glides with voice-led transitions/crossfades, and improve envelopes/overlap. Prove a fixed version is pleasant for several minutes before adding more adaptation.
3. **Add seeded, constrained variation.** Implement the visible seed and replay contract, with independent decision streams and pinned versions. Keep this planner renderer-independent.
4. **Evaluate Strudel behind the adapter.** Start with an isolated `@strudel/web` integration spike. Verify pinned APIs, audio lifecycle, stable cycle position and that every output/effect path can be routed through the existing limiter without a bypass. Avoid an iframe or embedded editor. Migrate only after that output-routing contract is demonstrated.
5. **Tune adaptation using repeatable comparisons.** Replay the same navigation log against fixed authored music, current MVP and the new director, using the same few seeds and approximately matched loudness. Then test normal self-paced reading.

This is a small composition/director redesign, not a request for a model, backend or audio-generation service. The delivered app can remain a single HTML file. A few pure composition helpers and tests will be easier to maintain than continuing to put all musical decisions into `composeBeat`.

## 6. Acceptance checks

- Next/Previous during a phrase does not reset the phrase, retrigger a full chord or indiscriminately cut its notes.
- Rapid navigation replaces the pending intent; it does not stack transitions. A pause or muted output never advances the composer through timer catch-up.
- Same seed + versions + initial state + event log produces identical planned note/control events, regardless of visualiser FPS or UI resize.
- Background, harmony, melody and pulse can be varied/muted independently without changing other streams' random choices.
- New seeds produce constrained variations; every seed still obeys pitch/register, voice-leading, density and maximum-polyphony rules.
- Voice-led transitions minimise avoidable jumps; retained notes and effects tails are compatible with the destination harmony.
- Foreground and background share the same harmonic plan. Dry/effect paths retain the existing 0.14 final sample ceiling, conservative gain, mute and lifecycle tests.
- Offline and real-browser tests cover 10–15 minutes of simulated reading, rapid jumps, pause/resume, reload, restart and seed changes without unbounded voices or memory.
- Listening comparisons ask separately about continuity, plonkiness, monotony, distraction and narrative fit. Automated pass results do not prove pleasantness.

The immediate next step should be a persistent, seedable Rat composition with proper phrase boundaries—not more lexical features, more randomness or a louder continuous layer.
