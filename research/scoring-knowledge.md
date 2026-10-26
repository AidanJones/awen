# Scoring films, theatre and reading: usable harmonic knowledge

Research pass: 26 October 2026. The deliverable is a small design library, not a training dataset or a catalogue of universal emotional meanings. It contains nine harmonic families, eight scene functions, seven genre contexts and nine source records. Exact chord cycles, numeric settings and scene/genre assignments are original Awen proposals. Sources support broader techniques and contextual reasoning, not the effectiveness of these particular cycles.

## What the research adds

**Harmony can work through relationships rather than a single emotional chord.** Frank Lehman's original analysis of *A Beautiful Mind* examines chromatic but triadic material, narrative associations and transformations. He also cautions that film editing, spotting and redirected attention complicate interpretation. For Awen this suggests retaining a harmonic identity and voice-leading policy across a cue, rather than selecting a new chord from a word-level emotion label. [Original article, opening discussion and abstract](https://franklehman.com/wp-content/uploads/2020/02/MTS-Article.pdf).

**Associations are conventional and can be used ironically.** Jason Yin Hei Lee's study traces historical meanings of chromatic mediants. Its introduction discusses a film passage in which an apparent miracle is mocked through major-third-related harmonies. A relationship associated with wonder can therefore serve comic deception in context. Our major-third family is an original four-voice exercise, not that film's transcription. [Original article, introduction 0.1–0.3](https://www.mtosmt.org/issues/mto.25.31.2/mto.25.31.2.lee_jason.html).

**Distant harmony is a candidate, not a compulsory science-fiction sound.** A chapter excerpt from Lehman's *Hollywood Harmony* discusses tritone-related triads in uncanny and cosmic contexts. Only that excerpt was consulted here, not the complete book. The library includes a distant-root alternative and a restrained suspended alternative, so a scene can be tested without imposing the more conspicuous colour. [Chapter excerpt, “Tritonal Transposition”](https://music.arts.uci.edu/abauer/3.1/notes/Frank_Lehman_Hollywood_Harmony_Chapter_3_%282018%29.pdf).

**Genre and scene can disagree usefully.** In the production's own interview, Michael Giacchino describes *Let Him Go* as involving western, thriller and family-drama demands. He discusses inward character experience, sparse instrumentation and avoiding excessive emotional direction. That supports a separate genre context and scene function; it does not identify a mandatory western progression. [Composer interview](https://www.focusfeatures.com/article/interview_let-him-go-composer_michael_giacchino).

**Theatre offers a reason to leave musical space for language.** Chris Houston describes theatrical speech occupying the role a melody might otherwise fill, and script/director-led spotting. This is a practitioner account from a specific production, not a survey of all plays. Awen records lead-rest and silence guidance separately from harmony; silent reading has no actor's voice to mix around, so this is a hypothesis for listening tests rather than direct evidence of reading benefit. [Theatre's composer interview](https://www.marintheatre.org/press-release-details/239/interview-with-sound-designer-composer-and-musical-director-chris-houston-web-exclusive).

**Character viewpoint may matter more than a generic genre.** Adrian Sutton's account of *The Curious Incident of the Dog in the Night-time* describes deriving patterns and electronic material from the protagonist and production concept. This motivates preserving an encountered character's musical identity, not diagnosing a reader or assigning a fixed sound to a group of people. [Composer work note](https://www.adriansutton.com/works/AS0016/).

Berklee's public course outline treats genre through melody, harmony, rhythm, tempo and orchestration together. It was used as an organising reference; course lessons were not accessed. Existing first-hand accounts by Alan Williams and Ennio Morricone supply radio-drama and instrumental-identity context already recorded in the earlier starting-point notes. [Berklee outline](https://online.berklee.edu/courses/music-composition-for-film-and-tv), [Williams interview](https://scifibulletin.com/books/audiobooks/dangerous-visions/dangerous-visions-interview-the-kraken-wakes-alan-williams/), [Morricone interview](https://www.bfi.org.uk/sight-and-sound/interviews/if-you-want-call-yourself-composer-you-follow-every-step-instrumentation-ennio-morricone-interviewed-2006).

## How to represent the knowledge

Separate four layers:

1. **Scene function:** conversation, intrigue, anticipation, pursuit, revelation, reflection, aftermath or tenderness. These describe a dramatic task, not a reliable machine reading of a paragraph.
2. **Genre/context:** western, caper, noir, science fiction, fantasy, chamber drama or neutral. A genre offers alternatives and can be overridden by the scene or a character's viewpoint. Noir here is an exploratory editorial category, not a statistically established minor-sixth convention.
3. **Musical family:** a four-chord bank, form and harmonic rhythm, with performance guidance and references. Several families can serve the same function.
4. **Personal preference:** keep the existing listener genome and A/B/gallery feedback separate from claims about what a scene means. A preferred sound does not establish narrative fit or reading benefit.

The machine-readable [scoring-knowledge.json](scoring-knowledge.json) is the canonical file; [scoring-knowledge.schema.json](scoring-knowledge.schema.json) specifies its initial shape. Each family carries `evidenceStatus: awen-proposal`, source IDs and a statement that the exact progression is our adaptation. Source records distinguish composer accounts, original analysis and a public teaching outline, with reviewed sections noted. Schema and engine validators check structure and references; they do not validate artistic meaning.

## Harmonic candidates

These are examples in D (pitch class 2), not film transcriptions. Symbols use add9 rather than ninth-chord shorthand where no seventh is present. Roots in JSON are semitone offsets from the selected tonic; intervals are relative to each chord's own root. The four entries are chord banks; `form` determines the actual traversal.

| Family | D-centred chord bank | Candidate role |
|---|---|---|
| Open modal space | Dsus2(add6), Gsus2(add6), C(add9), A7sus2 | Spacious reflection, landscape, reserved anticipation |
| Warm added-note continuity | Dm(add9), C(add9), G6, Am7 | Conversation, reflection, tenderness |
| Minor-sixth intrigue | Dm6, Gm6, C6, Am7 | Caper/noir experiments; contextual rather than genre-defining |
| Held-root suspension | D7sus2, Dm7, D7sus4, Dm(add9) | Anticipation without continual bass-root movement |
| Chromatic neighbour tension | Dm(add9), Ebm(add9), Dm(add9), C#dim7 | A more unstable alternative for threat or disorientation |
| Major-third colour | D(add9), Bb(add9), F#(add9), D(add9) | Wonder, revelation or an ironic reading of the same event |
| Tritone-distance contrast | D(add9), Ab(add9), Dsus2(add6), Ab(add9) | Distant tonal areas for testing cosmic/uncanny colour |
| Minor driving cycle | Dm7, C(add9), Gm7, A7 | Pursuit/action with rhythmic direction |
| Gentle release | Dm(add9), G6, D6, D(add9) | One possible softening after strain; suspended/minor alternatives remain available |

Added tones adapt broad harmonic ideas to the engine's four distinct pitch classes. This is a rendering constraint, not a claim that original scores use those voicings. Pitch spelling is explanatory only; the engine uses pitch classes and selects register through voice leading. It anchors melody entries to the selected chord when an experimental recipe is active, avoiding accidental clashes from an unrelated fixed scale.

For example, **anticipation** offers held-root suspension/open modal space in western context, chromatic neighbour/held-root suspension in science fiction, and held-root suspension/warm added notes in chamber drama. All are tentative alternatives. Action need not mean faster tempo; revelation need not be triumphant; aftermath need not become major. Silence is a valid scene-level suggestion even though the harmony compiler does not itself mute audio.

## Engine contract and current integration

The complete JSON is embedded in the single HTML file, so opening the app needs no fetch/build/CDN. `compileHarmonyRecipe(library, options)` validates the library, resolves genre/scene aliases, chooses an explicit alternative, transposes the chord bank, checks four-voice feasibility and returns the current engine format with provenance.

```js
const recipe = compileHarmonyRecipe(scoringKnowledge, {
  genre: 'frontier',    // alias for western
  scene: 'suspense',    // alias for anticipation
  variant: 0,          // use 1 for its alternative
  tonicPc: 2           // D; any pitch class 0–11 is supported
});

// Explicit experimental use with the live adapter:
audio.queueHarmonyRecipe(recipe);
// Or the convenience lookup in the app:
audio.queueHarmonyRecipe(proposeHarmony('unseen', 'discovery', 1));
// Return to the selected authored starting point:
audio.queueHarmonyRecipe(null);
```

While playing, changes enter at a four-bar phrase boundary without resetting musical time. While paused, a selected recipe is ready for the next start. Harmony, harmonic rhythm, form and chord-tone melody anchors are applied; tempo, timbre, lead density, silence and character-motif advice are not silently applied. The compiled object reports these as `applied` and `advisory` data. Normal playback and saved preference genomes do not automatically select these research recipes. This explicit engine API is session-only; experimental harmony is not yet part of profile/checkpoint export or the public gallery UI. Reading positions still save, while authored-score checkpoints are left untouched during a pending/active experimental harmony override.

Maintenance, not a required application build:

```sh
python tools/sync_scoring_knowledge.py          # validate and embed JSON
python tools/sync_scoring_knowledge.py --check  # verify without writing
node --test tests/mvp.test.cjs
node tests/scoring-knowledge.browser.cjs       # optional isolated Playwright
```

The JSON schema checks shape. The dependency-free maintenance validator also checks IDs and cross-references; the engine checks register feasibility on compilation. Tests exercise all 12 tonic transpositions and reject malformed pitches, missing sources and unknown scene/genre selections. No copied themes, source recordings, large annotation corpus or trained model is needed for this library.

## Next listening gate

Audition a few alternatives at comparable levels on the same passage and musical starting state. Record personal enjoyment, narrative fit and reading comfort separately. Test transitions and longer repetition, including returning to the original recipe. Source-labelled suggestions should support selection/evolution, not overrule the listener. Add a normal gallery/persistence workflow only after this small harmony experiment is useful. Timed film/play scene annotation, stronger perceptual loudness work, character motifs and non-four-voice writing remain open strands.
