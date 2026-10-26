# Film and audio-drama starting points for Awen

Research notes, 25 October 2026; implementation update, 26 October 2026. Four original starting-point recipes are now available in the app. They remain artistic design hypotheses, not findings from a listening experiment. Sources below were searched/read as web text; no film, soundtrack or radio episode was auditioned or automatically analysed in this pass. Some repository downloads were inaccessible; their catalogue records are identified accordingly.

## Why this is useful

A small set of authored musical starting points could give preference evolution better parents than repeated small mutations of one ensemble. Separate three things: palette (instrument colours), scoring behaviour (when and how music develops), and listener preference (how much activity, warmth, space, etc.). A listener may like a western palette with restrained dialogue scoring or a science-fiction palette with greater rhythmic motion. Genre alone should not determine emotion.

Study scenes with dialogue/narration and transitions, not only soundtrack albums. A standalone theme does not expose the relationship between music and the words. Film/audio drama have fixed timing and silent reading does not: sustained phrases, optional rests and bar/phrase-aligned changes need to tolerate an unknown reading duration. None of the sources below establishes improved reading comprehension from cinematic underscoring.

## References located

### Ennio Morricone / Sergio Leone westerns

Primary interview: [Morricone interviewed in 2006, Sight and Sound/BFI](https://www.bfi.org.uk/sight-and-sound/interviews/if-you-want-call-yourself-composer-you-follow-every-step-instrumentation-ennio-morricone-interviewed-2006).

Morricone describes deriving tone from the director and script, sometimes before seeing scenes. For *Once Upon a Time in the West*, he recorded music before filming. He credits Leone with the water-drop opening; this is a useful reminder to distinguish music from other sound design. The interview also describes distinct musical strands sharing elements in *The Mission*. These are compositional accounts, not controlled evidence about background listening.

Proposed listening subjects: *Once Upon a Time in the West* for identity and sustained anticipation; *For a Few Dollars More* for recurring objects/motifs. These scene-level properties need verification against the films before detailed annotation. The aim would be original motifs and general scoring principles, rather than reproducing an existing theme.

### The Kraken Wakes — Alan Edward Williams / BBC radio adaptation

Primary [composer interview](https://scifibulletin.com/books/audiobooks/dangerous-visions/dangerous-visions-interview-the-kraken-wakes-alan-williams/) describes listening to 1950s/60s B-movie music, orchestral textures and presenting the same theme in a John Barry-like jazz treatment. This is a directly relevant model for varying a musical identity across contexts.

The composer's [own catalogue](https://alanwilliams123.wordpress.com/compositions/orchestral-and-large-scale/) identifies the adaptation as commissioned for BBC Radio Drama with live studio performance, broadcast in 2016. A [university catalogue record for the full score](https://salford-repository.worktribe.com/output/3801705/the-kraken-wakes-full-score) links to [the deposited score](https://salford.figshare.com/articles/dataset/The_Kraken_Wakes_full_score/7347392). The score itself was not accessible through the research browser, so no bar-by-bar claims are made here.

Williams also wrote [Scoring the Unseen](https://salford-repository.worktribe.com/output/2126352/scoring-the-unseen-composition-film-music-for-radio-drama), an account of the production. The catalogue abstract was available; the full chapter was blocked. Search-index excerpts describe the orchestra suggesting an unseen threat; that is promising but is not a substitute for reviewing the chapter and audio together.

### Historical cue sheets — Library of Congress

The [Silent Film Scores and Arrangements collection](https://www.loc.gov/collections/silent-film-scores-and-arrangements/about-this-collection/) catalogue describes film-specific scores, cue sheets and stock music with piano/orchestral materials. The collection is potentially valuable for inspecting explicit scene-to-cue instructions. It is silent-film material, so it does not directly answer how to support spoken dialogue. Individual items would need inspection before selecting anything for reuse; nothing was downloaded or bundled.

## Proposed original starting points

These values/ranges are design hypotheses, not measured properties of the reference scores. The original renderer lacked recipe-specific timbres. It now adds simple guitar-, reed-, piano- and rounded-bass-like synthesis colours, without claiming realistic instruments. Recipe-specific patterns, harmonic rhythm and background balances complement the six preference traits.

| Starting point | Musical identity | Background behaviour | Foreground behaviour |
|---|---|---|---|
| Frontier / spacious | Original short motif, open fifths, guitar-like and breathy solo colours | Slow harmonic movement, long swells, occasional thinning to near silence | Widely spaced answers; limited repetition; reserve rhythmic motion for sustained action |
| Caper / intrigue | Muted bass, light reeds, restrained plucked accents | Warm connected harmony with gaps in inner voices | Short recurring phrases, syncopation and playful variation; suits a first Stainless Steel Rat experiment |
| Unseen threat / retro science fiction | Low strings, woodwinds, restrained metallic colour | Long tension and release, evolving register/voicing | Fragments appear sparingly; retain identity as orchestration changes |
| Intimate dialogue | Small chamber ensemble | Few moving parts and slower changes | Melody often rests while conversation continues; answers between larger narrative beats |

Each starting point needs structural controls beyond the current genome: rest probability and length, motif spacing, harmonic rhythm, orchestration, register, and how long scene energy persists. Tempo can remain fixed during a first experiment. Activity and subdivision can provide movement while preserving continuity.

## A practical reference study

1. Choose around 12–20 short excerpts across dialogue, landscape/reflection, anticipation, action and aftermath. Include places where music is absent and moments either side of a cue transition. Select sources we can actually access; do not assume a repository record includes playable audio.
2. Manually annotate scene function, speech density, music entry/exit, lead presence, register, approximate note-onset density, pulse/subdivision, harmonic change rate, motif recurrence and transition shape. Use exact timecodes only after inspecting the specific edition. Distinguish soundtrack music from environmental sound.
3. If audio is available for local analysis, estimate onset density/tempo as supporting measurements and manually check them. Mixed dialogue/effects can contaminate music measurements; automatic stem separation is optional and its artifacts should not become reference truth.
4. Implement two or three original sketches that preserve these broad behaviours. Use the same Awen passage, seed and comparison duration. Compare different starting points first, then evolve a preferred one with the six-choice profile gallery.
5. Ask separately whether a sketch fits the scene, is pleasant, and makes reading harder. Preference alone could select an engaging piece that competes with the text. Keep cancellation and undo cheap; avoid requesting feedback on every paragraph.

Recommended first experiment: contrast spacious frontier, restrained caper and intimate dialogue on the same three Rat passages. These prototype recipes are now implemented; real-scene listening/annotation and reader evaluation remain open. No large model or training pipeline is necessary: authored seeds/palettes and a few local scoring rules provide starting points, with user selection guiding subsequent mutations.

## Implemented small experiment — 26 October 2026

The written-source review was refreshed using the original [Alan Williams interview](https://scifibulletin.com/books/audiobooks/dangerous-visions/dangerous-visions-interview-the-kraken-wakes-alan-williams/), [Morricone interview](https://www.bfi.org.uk/sight-and-sound/interviews/if-you-want-call-yourself-composer-you-follow-every-step-instrumentation-ennio-morricone-interviewed-2006), and [Souza/Barbosa study](https://doi.org/10.5334/joc.273). Williams describes contrasts between intimate characters and large-scale threat, and reuse of a theme across orchestral/jazz treatments. Morricone discusses deriving musical direction from scripts and choosing instrumental strands. The reading study supports caution about lyrics; it does not validate these instrumental recipes. These accounts motivated experiments in spacing, identity and orchestration, not a claim to have reproduced their scoring systems.

All four new recipes use original short motifs authored for Awen. Frontier uses two widely spaced answers and open chord colours; caper uses five reed-like figures and occasional soft accents; unseen threat uses bowed fragments over slower harmony; dialogue leaves alternate four-bar phrases without a lead. The continuously available background follows the same harmony, with recipe-specific voice balances/swells. All retain the 72 BPM clock, minimum scene dwell, seeded planning and shared final limiter. The existing classic recipe is preserved.

The recipe ID is kept separately from numeric preference traits inside the serialised genome. Mixed-parent exploration inherits the first selected recipe, rather than randomly mixing incompatible harmonic systems. A named pin includes recipe identity; older profiles migrate to the classic recipe. Ordinary paragraph navigation never selects a new genre automatically.

A small native Web Audio check rendered each new recipe on the same first three Rat passages (caper/dialogue/chase), at seed `rat-001`, 35% app volume and 30% background. All 12 clips produced finite signal; RMS was approximately 0.019–0.031 and peak approximately 0.061–0.086, below the 0.14 cap. A later dialogue phrase retained background signal during its lead rest. These are signal/behaviour checks, not evidence of pleasantness or reduced distraction. Audio is generated on demand; no reference recordings or rendered corpus is retained.

Remaining gate: use the app to compare the starting points on a few real reading passages, pin a direction, evolve it for a round or two, and judge comfort over several minutes. No production has yet been listened through or annotated by this agent, and the unavailable score/chapter materials above have not been silently treated as read. Keep the larger reference-study task open until actual scene analysis is done.
