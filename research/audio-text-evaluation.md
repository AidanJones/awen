# Audio–text embeddings and reference material

26 October 2026. Research supporting the development evaluator. The [small CLAP probe](clap-probe.md) is now implemented and measured; MuQ-MuLan, CLaMP 3 and reference-corpus comparisons remain backlog work. None adds a runtime dependency to the reader.

## Existing CLIP-like audio models

| Model | What its authors provide | Possible Awen use |
|---|---|---|
| [LAION CLAP](https://github.com/LAION-AI/CLAP) | Contrastive audio/text embeddings, with checkpoints including music/speech training | First small retrieval/association diagnostic over music descriptions and rendered audio |
| [MuQ-MuLan](https://github.com/tencent-ailab/MuQ) | Music/text joint embeddings; distinct from the audio-only MuQ encoder | Compare music-specific descriptions against the general audio model |
| [CLaMP 3](https://github.com/sanderwood/clamp3) | Shared music retrieval representations across text, audio and symbolic/visual music modalities | Later compare symbolic score plans and actual audio against the same brief |

The official MuQ repository specifies 24 kHz audio, approximately 700M parameters for MuQ-MuLan, MIT code and CC-BY-NC 4.0 model weights. Its input rate matches the lab WAVs, but that does not establish alignment quality. Check each chosen checkpoint's actual revision, licence, preprocessing, truncation/windowing and hardware needs before installation. MuQ/CLaMP weights have not been downloaded or benchmarked here. CLAP checkpoints were downloaded for the separate local probe; all remain development tools rather than browser/device requirements.

A joint embedding makes cosine similarity possible; it does not make a play paragraph a music caption. Retrieval of “tense strings” is different from deciding whether a quiet suspended accompaniment supports an ironic conversation. Literal mention of gunshots or a train could reward sound effects rather than useful music. Do not turn similarity into a universal musical-quality score or manufacture LLM-style coherence/comfort votes from it.

Start with a few independently authored dramatic-function briefs, positives and plausible counterexamples. Compare matched and shuffled pairs; include ambiguous text and silence/no-music examples. Extract time-aligned windows around changes instead of averaging away the entire scene. Cache features by exact audio bytes, text, checkpoint and preprocessing. Check agreement with separate listener fit/taste/comfort labels before using a score to select candidates. Whole-work/book/genre holdouts matter more than randomly splitting overlapping clips.

If this works, the development loop could use cheap embedding diagnostics to shortlist candidates and an audio-capable LLM for richer comparisons of finalists. A small trained ranking layer may eventually be enough; training a new joint encoder from scratch is not the first experiment. Keep both mechanisms outside the finished local reader. Track this comparison as **`awen-3fr.6.2`**.

The first CLAP slice (`awen-3fr.6.2.1`) found a collapsed text tower in the music-only checkpoint, added a rejection guard and measured a pinned general/music/speech replacement on four existing windows. Intended scene briefs won only 2/4 versus swapped briefs, paraphrasing changed the sign twice, and silence outscored two intended pairings. See [the full results and limitations](clap-probe.md). This does not establish a usable optimisation reward; the broader comparison and listener/held-out calibration stay open.

## Do scripts describe the background score?

Sometimes, but not reliably or completely. The [BBC radio scene-format guide](https://downloads.bbc.co.uk/writersroom/scripts/bbcradioscene.pdf) says music is generally indicated for source cues or a function such as scene transitions. The [radio-drama writing manual preserved by Lancaster University](https://www.lancaster.ac.uk/transculturalwriting-archive/radiophonics/contents/usr/downloads/radiophonics/Radio_Drama.pdf) gives explicit entry/fade/under/hold instructions. Such cues are useful supervision for *when* music supports speech, but they are not a complete note-level account of the performed score. A screenplay, production script, music spotting document and performed recording can therefore supply different evidence; inspect the actual items rather than infer a soundtrack from script silence.

Silent films are a useful lead because accompaniment was explicitly planned around action and title cards. The [Library of Congress collection](https://www.loc.gov/collections/silent-film-scores-and-arrangements/about-this-collection/) includes film-specific scores, cue sheets identifying music for particular moments, and stock accompaniment music. The [UCLA collection description](https://oac.cdlib.org/findaid/ark%3A%2F13030%2Fkt0779q0ds) describes cues for title cards and actions. These records establish promising source types; they do not prove that a particular scan or associated recording has been inspected, or that a modern transfer uses the historical cue sheet.

Film and radio audio can mix music with dialogue/effects. Silent-film transfers may carry later accompaniments, and orchestral recordings without aligned dramatic context do not themselves label narrative function. These are alignment problems before they are training problems. A useful tiny manifest should record:

- The exact work, script version, score/cue sheet and recording/transfer, with source and permitted use for each; old or black-and-white appearance alone is insufficient provenance.
- Verified time ranges, corresponding scene text or intertitles, source music versus underscore, music/no-music entry/exit and transition shape.
- Dramatic function, instrumentation/register, motif recurrence, speech/effect contamination, uncertain or missing cues, and who supplied each annotation.
- Whole-work/composer splits and non-overlapping windows, avoiding leakage from nearly identical passages/recordings into held-out evaluation.

Begin with a few accessible, suitable examples and test retrieval against those labels before fine-tuning, separation pipelines or dataset expansion. Track the aligned-reference pilot as **`awen-7x1.2.2`**, alongside the existing film/audio-drama reference study. Finding aids are leads, not reviewed scores or training licences.
