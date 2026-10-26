# Developing scores with an offline teacher

26 October 2026. The user wants LLMs available during development, with a finished reader that runs without an LLM in a browser or on a device. The optional tools here are a development experiment; `index.html` has no new imports, network requests or model dependency.

## What to optimise

There is no validated single score for “good music for this paragraph.” Literal text–audio similarity can favour busy sound painting, while quiet accompaniment may fit a dramatic function without depicting its nouns. Musical enjoyment, narrative fit and ease of reading are different outcomes. Keep a vector of evidence:

| Criterion | Measurement | Role |
|---|---|---|
| Signal correctness | Finite samples, peak cap, audible RMS at a fixed reference volume | Hard rejection |
| Continuity | No automatic seed, palette, recipe or harmonic-regime jump/reset inside a chapter; bounded expression changes | Hard rejection |
| Some development | At least two distinct symbolic phrase patterns across four phrases; cap note-onset density | Experimental hard rejection, subject to calibration |
| Narrative fit | Audio-capable judge hears the full timed sequence with the text | Separate pairwise preference, with abstention |
| Musical coherence | Same judge evaluates identity, rests, development and transitions | Separate pairwise preference |
| Likely intrusion | Same judge estimates whether audio competes with reading | Proxy only; do not call it measured reading comfort |
| Personal taste, comfort, comprehension and fatigue | Short voluntary reading/listening sessions, then longer sessions | Human acceptance; never inferred from the model score |

Continuity means preserving the piece while it develops. It does not freeze every note, chord or instrument. Existing authored harmony, motif answers and bar-aligned scene activity remain allowed. Larger *automatic regime changes* may occur at a chapter boundary; they are not mandatory. Explicit user choices, restart and seeking are separate operations. The prototype searches one fixed regime per candidate, so it cannot exploit paragraph-by-paragraph preset switching. It does not yet implement a new chapter-aware runtime director.

The current thresholds are engineering proposals, not perceptual standards: peak ≤0.140001, RMS ≥0.0005, maximum smoothed state change ≤0.11 per eighth-note step inside a chapter, at least two symbolic phrase patterns, ≤4 note onsets/second. The variation signature ignores expression level and compares layer, pitch, duration, timbre and relative onset. It permits repeated motifs. It can miss a perceptually monotonous piece and reject a useful minimal texture; the audio judge and later listening must assess that. It is a guard, not a quantity to maximise. No pitch entropy, loudness, attack count or constant novelty reward is used as a proxy for musical merit.

## Research basis and limits

[MusicEval (Liu et al., ICASSP 2025)](https://arxiv.org/abs/2501.10811) separates assessment of generated music from synthesis and supplies expert ratings with a CLAP-based assessment model. This supports testing an evaluator against human evidence. Its music-description prompts and expert ratings do not validate paragraph accompaniment, personal taste or reading comfort. We have not downloaded its dataset or trained an evaluator.

[Modrzejewski and Radzikowski (9 October 2026 preprint)](https://arxiv.org/abs/2610.13247) probe audio-language judges with removed/replaced audio, swapped pairs and reworded instructions. They find material differences in what judges track, including slot sensitivity and confusion between alignment and quality. These are grounds to calibrate a judge rather than accept a plausible explanation. This prototype implements identical-audio and missing-audio controls plus both pair orders. Audio replacement and prompt rewording remain a required follow-up; model self-attestation and timestamps do not prove it listened.

[Zheng et al. (NeurIPS 2023)](https://arxiv.org/abs/2306.05685) document position and other biases in text LLM judges. Their agreement with people on chatbot answers is not evidence of musical judgement. Blinding candidate recipes, allowing ties/abstention and keeping dimensions separate are design precautions, not a claim that bias is eliminated.

An audio–text embedding such as CLAP could become another development diagnostic after checking it against our listening choices. Do not compare a novel paragraph directly with generic music captions and declare its cosine score to be fit. A development LLM could first propose a short dramatic-function brief, but it must remain independent of the rule output being evaluated and should not dictate the judge's answer. Never use the current classifier's own scene labels as ground truth for tuning it.

## Run a small experiment

The maintenance tools require Node and optional Playwright, using the same isolated headless setup as the existing tests. No build step is added to the reader.

```sh
node --test tests/score-lab.test.cjs
node tools/score-lab.cjs search --out .score-lab/experiment-001 --seed lab-001 --budget 4
```

The first batch is the existing Connected ensemble baseline and three seeded alternatives based on Frontier, Dialogue and Caper. Later batches mutate only the accepted parent's bounded numeric genome; they retain its palette/recipe. The current search does not generate code, new chord grammars, tempo rules or samples. Use it to establish an evaluator before widening the parameter space.

Two development cases (Rat and Riders) each have three successive opening paragraphs and the first paragraph of the next chapter. Paragraph changes are scripted every four bars; this is deliberately a transition fixture, not natural reading behaviour or a representative literary benchmark. One unseen book, War, is reserved for a later report. One seed/book is a smoke test, not generalisation evidence; fresh seeds, unseen chapters and other scene functions must be added after the gate is useful, without tuning repeatedly on the holdout.

The tool renders the production native Web Audio graph at 24 kHz, 35% app volume, 30% background, all mixer layers enabled, with matched seeds, passage order and musical start. Expression is stepped with the production exponential smoother on the score grid; DSP scheduling is consistent between candidates, not a claim of sample-identical live playback. Audio has a one-second final fade. Each WAV is approximately RMS balanced to 0.018 by attenuation only, never boosted. Hard gates inspect the original samples. Recordings contain only our synthesiser, with no microphones or downloaded soundtracks.

Each fresh output directory contains `round-0/run.json`, WAVs, per-clip event/state traces, `judge-packet.json`, the judge instructions, and a status file. SHA256 hashes bind the judgement to the rendered WAV bytes; source HTML, fixtures, tools, metrics, rubric, engine, browser and Playwright versions are recorded. Raw experiments and model responses are ignored by Git under `.score-lab/`; [the small measured proof summary](score-lab-proof.json) is committed separately. The tool refuses to overwrite an existing experiment directory or replace an already judged decision.

Without a judge, it stops at **awaiting-audio-judge**. It never calls the highest-RMS or most-varied candidate “best.” A real development judge can return the strict JSON exchange in [the rubric](score-lab-judge.md):

```sh
node tools/score-lab.cjs judge --run .score-lab/experiment-001/round-0 --responses actual-judge-responses.json
```

Use an audio-capable model, attach the actual WAV bytes referenced by each request, and record the real model/version. A text-only judge, MIDI description, transcription service or invented response is insufficient. No provider adapter or credentials are bundled, and the measured proof has **no model judgements**. Literary text and model responses are untrusted data; they never execute in the reader.

For a bounded automatic development loop, provide a local CommonJS adapter exporting `async function(packet, {directory})`. It must attach the local audio files to a suitable provider, apply `judge-instructions.md`, and return the response object. The adapter owns credentials, retries, provider-specific duration limits and a cost ceiling; nothing reads credentials or uploads audio by default. Keep prompts/sampling settings and provider usage in its response archive. The packet excludes recipe names, numeric settings, rule-derived labels and answer keys, though repeated opaque file identities are not perfect blinding.

```sh
node tools/score-lab.cjs search --out .score-lab/experiment-002 --seed lab-002 --budget 4 --rounds 3 --judge-module /absolute/path/to/local-audio-adapter.cjs
```

Budget is capped at four candidates and three rounds. A four-candidate round prepares 14 requests (12 swapped comparisons plus two controls), at most 42 requests for three rounds; plan provider costs and audio-duration limits before enabling an adapter. For each candidate versus the incumbent, the judge hears both pair orders on both development cases. It must tie identical recordings and abstain without audio. A candidate advances only when paired outcomes agree, reported confidence is ≥0.7, neither case worsens on any dimension, and fit or coherence improves somewhere. The confidence threshold is an uncalibrated filter, not a statistical confidence bound. A control failure, uncertainty or no supported improvement stops the loop. Ties between supported alternatives use fit-win count, coherence-win count, then stable ID; those counts are not a universal quality score. This deliberately conservative rule may find no winner.

An accepted result produces a **proposal.json**, never changes app defaults or a personal profile. Check an unseen book once:

```sh
node tools/score-lab.cjs holdout --out .score-lab/unseen-001 --proposal .score-lab/experiment-002/round-0/proposal.json
```

This compares the proposal with the original default on the held-out fixture. It does not tune on the holdout. Judge/listen separately, and stop using that fixture as held out if its results guide changes. Promotion still requires reader feedback and regression tests. Ultimately we can keep small authored recipes, rule thresholds or a tiny local model; the development teacher and its evaluation assets are not needed for the finished browser/device score.

The recorded engineering proof rendered four candidates on both development cases (eight native clips). Each had three or four distinct symbolic phrase patterns, zero within-chapter resets/regime breaks, and a raw peak below 0.093. No LLM was invoked and no musical winner was selected. Synthetic unit verdicts test the acceptance/rejection logic; they are never saved as model evidence. The Rat fixture exercised different scene intentions; the chosen Riders opening stayed reflective under the current classifier. These few openings do not cover all scene functions, books or long-session repetition.

## Next autonomous work and the human gate

Beads tracks the remaining strands: richer musical traits (`awen-3fr.3`), fair replay (`awen-3fr.5`), continuity/development (`awen-7x1.3`) and calibration of this judge (`awen-3fr.6`). Additional engineering fixtures, archived replay, failed-control probes and versioned rule proposals can be developed without listener input. Actual personal taste, reading comfort and fatigue require the listener; a model cannot supply those labels for them. Keep that gate small before generating a large corpus.
