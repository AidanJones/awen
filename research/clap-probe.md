# A small CLAP association probe

26 October 2026. Implemented as a development-only diagnostic; the finished HTML is unchanged. No encoder is trained, no reference corpus is created, and no CLAP score is used to adopt a musical candidate.

## What was tested

Four existing native-rendered WAVs: Connected ensemble and Spacious frontier, each on Rat and Riders. Each contributes a fixed ten-second window inside one declared paragraph interval. The [suite](clap-probe-suite.json) contains developer-authored accompaniment briefs for an ingenious escape and a reflective western landscape, their paraphrases, and two deliberately unsuitable descriptions (metal with screamed vocals; speech/traffic). Briefs were written before scores were inspected and do not use the engine's scene labels. They are proposals, not independently annotated human ground truth. Instrument/palette names are absent from the briefs.

The comparison swaps the two scene briefs, without searching for a favourable permutation. A separate all-zero waveform tests silence. Three unrelated captions test extreme text-encoder collapse before scene/audio comparison. There are 14 distinct features: three sanity captions, six comparison descriptions, four audio windows and silence. Repeated audio identities reuse cached vectors.

The [pinned model specification](clap-probe-model.json) selects [LAION larger_clap_general](https://huggingface.co/laion/larger_clap_general), revision `ada0c23a36c4e8582805bb38fec3905903f18b41`. Its model card describes training on general audio, music and speech and labels the checkpoint Apache-2.0. The weight file is approximately 776 MB, with its SHA256 checked before loading. The processor is loaded from the same revision. We use CPU float32, evaluation/inference mode, a fixed seed and two threads; PCM16 mono 24 kHz is resampled to 48 kHz with a specified polyphase filter. Exact ten-second inputs avoid random long-clip crops. Text is padded to 77 tokens and longer input is rejected rather than silently truncated. L2-normalised embeddings are compared by cosine, not treated as probabilities.

### Rejected checkpoint

The initial music-only `laion/larger_clap_music` checkpoint failed an independent API sanity check: unrelated dog, piano and speech captions had pairwise cosine similarities above 0.999. Dynamic/fixed padding and the supported attention mode produced the same problem. The [recorded rejection](clap-probe-rejected-checkpoint.json) includes the exact checkpoint and observed matrix. A [public MTEB issue](https://github.com/embeddings-benchmark/mteb/issues/5069) reports the same failure. This is evidence about the tested checkpoint/stack, not a general conclusion about CLAP.

The replacement's three sanity similarities were approximately 0.188, 0.316 and 0.137. The new guard rejects an encoder when **all** pairwise similarities for those unrelated captions exceed 0.995, and stops before scene/audio scoring. That threshold detects this extreme failure; passing it does not validate semantic accuracy. The first diagnostic archive remains local, with no musical winner selected. Its scene scores are excluded from conclusions. The briefs and audio windows were kept unchanged for the replacement.

## Results and what they permit

[Full measured results and recovery proof](clap-probe-proof.json):

| Check | Result |
|---|---|
| Intended brief preferred over its swapped counterpart | 2 / 4 audio windows |
| Mean intended minus swapped cosine | +0.0191 |
| Intended brief above both deliberately unsuitable descriptions | 4 / 4 |
| Preference sign changed under paraphrasing | 2 / 4 |
| Silence scored above the real music's intended brief | 2 / 4 |

This is a useful engineering proof of joint embedding extraction and a weak result for paragraph-level fitness. Obvious mismatches were separated, but intended versus swapped scene direction was unreliable and wording-sensitive. Silence is especially important: similarity alone could reward an unhelpful outcome. Existing signal gates must remain separate. **Do not use this score as an evolution reward or call any preset the musical winner.**

The four examples are alternate renderings of two scenes, not four independent observations or a held-out benchmark. There is no significance claim, human taste/fit/comfort label, comprehension result or longer-session evaluation. Our simple synthetic instruments may differ from the recorded material on which the encoder was trained. Caption association is not the same task as quiet musical support for a passage. More checkpoints and held-out scenes remain under `awen-3fr.6.2`; listener calibration remains under `awen-3fr.6`.

## Calibration roadmap — 27 October 2026

Decision: keep CLAP diagnostic-only until it can rank alternatives for the same passage in agreement with listener judgements on unseen material. There is no assurance that raw CLAP similarity can become a reliable reward for reading accompaniment. A calibrated combination of features may work; replacing the encoder or dropping its contribution are valid outcomes.

1. **Define the target before collecting more audio.** Rank scene fit separately from enjoyment, musical coherence and reading comfort. Use independently authored musical-function briefs rather than long prose or the current classifier's own labels. Prefer relative improvement over the same-scene incumbent to absolute cosine scores. Compare levels, seeds, timing and musical context fairly.
2. **Build a tiny labelled comparison set.** Start with around six varied scenes and three or four existing-engine alternatives per scene, including a plausible but unsuitable direction. A short first round of roughly 20–30 blinded pairwise judgements can reveal gross failures; it is not enough to establish reliability. Record fit, ties/uncertainty, preference and distraction separately. An audio-capable LLM may supply provisional development labels, but retain their provenance and calibrate against listener choices. Keep the encoder frozen initially; do not train a new joint encoder.
3. **Try a small ranking layer, not a larger corpus first.** Compare the shipped incumbent, raw CLAP, a predeclared paraphrase ensemble, and a simple regularised ranker using CLAP similarities/margins plus a few audio/symbolic descriptors. Tune only on development labels. Do not invent weights or combine every dimension into a quality score before evidence supports it. Use cached features; a small linear/logistic ranking model is the first learned experiment. If CLAP adds nothing beyond simple descriptors, omit it. Compare MuQ-MuLan/CLaMP only against this same fixed task rather than assume a bigger encoder is better.
4. **Attack the reward.** Include silence, near-silence, a constant drone, excessive/repeated attacks, loudness-only changes, noise, mismatched music, shuffled passage/audio, and deliberately discontinuous transitions. Evaluate multiple timed windows and longer sequences so a good ten-second average cannot hide a jarring transition. Preserve sample/voice/scheduling limits and within-chapter continuity as separate constraints; never allow a semantic score to compensate for a failed gate. Larger automatic regime changes belong at chapter boundaries, with explicit user controls treated separately. The chapter-aware runtime director remains its own open task.
5. **Test generalisation and uncertainty.** Freeze captions, feature choices, weights and thresholds before touching held-out whole books/chapters and fresh seeds. Report pairwise listener agreement, ties/abstentions, paraphrase stability, control failures and ranking reversals. Group uncertainty estimates by independent scene/work, not overlapping audio windows. The ranker should beat both chance and an unchanged/simple baseline with useful uncertainty bounds and no important subgroup regression; the present four correlated windows cannot establish that. If test results guide tuning, retire those cases from holdout status.
6. **Trial conservative use before autonomous selection.** First use the model to shortlist several choices for a listener. Then run a bounded development search against a fixed incumbent, looking for exploitation and held-out regressions. Require supported improvement rather than selecting every round's numerical maximum. Store versions/lineage and keep rollback. Only promote small accepted recipes, rules or parameters after listening acceptance; the reader still has no LLM or embedding-service requirement.

The immediate next deliverable is a replayable, blinded calibration packet and label format, with a few diverse same-scene alternatives and the existing controls. Engineering setup can proceed independently; personal taste and reading comfort still need listener evidence. No new ratings or calibrated ranker have been produced by this documentation update. Tracked under `awen-3fr.6` and `awen-3fr.6.2`, with the chapter policy under `awen-7x1.3.2`.

[MusicEval](https://arxiv.org/abs/2501.10811) provides precedent for learning CLAP-based assessment from expert ratings rather than assuming raw similarity is a quality metric; it does not validate literary accompaniment. The [audio-language judge probes](https://arxiv.org/abs/2610.13247) support checking audio dependence, pair order and wording before treating an LLM's labels as supervision. These papers motivate the evaluation design, not the proposed pilot size or acceptance thresholds, which remain Awen proposals.

## Optional environment

The native evaluator remains standard-library Python. Only this separate CLAP tool needs ML packages. Python 3.11+ is required by the optional pins; tested here on Python 3.12. Windows setup (use `bin/python` instead of `Scripts/python.exe` on Unix):

```powershell
python -m venv .score-lab/clap-venv
& ./.score-lab/clap-venv/Scripts/python.exe -m pip install torch==2.8.0 --index-url https://download.pytorch.org/whl/cpu
& ./.score-lab/clap-venv/Scripts/python.exe -m pip install -r tools/clap-requirements.txt
```

Run the following commands with that interpreter or its activated environment:

```sh
python tools/score_embeddings.py start --run PATH/round-000/run.json --audio-root PATH --download-model
python tools/score_embeddings.py status EXPERIMENT_PATH
python tools/score_embeddings.py resume EXPERIMENT_PATH
```

`--run` points to a completed native score-lab `run.json`. `--audio-root` is the directory against which its relative WAV paths resolve: the experiment root for Python-generated runs, or the round directory for the original JavaScript CLI. The first two eligible candidates are selected by default; `--max-candidates` accepts 1–4. No new audio is synthesised by this tool. Native gate eligibility is preserved; silence is an explicit diagnostic control, not a candidate.

`--download-model` permits downloading only the pinned model/processor files. No audio or brief is uploaded. Without it, loading is offline-only and missing weights produce a clear error. Ordinary local checkpoint files avoid Windows symlink privileges. Weights, optional environments, raw audio, logs and cached vectors stay under ignored `.score-lab/` directories and are not bundled in the reader or Git. Checkpoint downloads require substantial disk space even for a tiny feature experiment; the failed initial checkpoint was also downloaded during this investigation.

## Cache, unique logs and recovery

Every start creates a timestamp/UUID directory and each invocation/attempt gets unique logs, using the native evaluator's lock and atomic job journal. The experiment manifest is pinned by checksum. Source WAVs are verified and copied into the experiment, with selected windows bound to exact PCM hashes. Feature keys include transformed audio/text hashes, model/revision/weight checksum, preprocessing, backend code and installed package versions. Cache entries validate shape, finite values, unit norm and vector checksum. Model weights are verified when loaded; corrupt completed vectors/audio fail instead of being silently replaced. CPU settings are recorded; bit-identical computation across different hardware is not promised.

```sh
python tools/score_embeddings.py start --run PATH/round-000/run.json --audio-root PATH --max-new-features 2
python tools/score_embeddings.py resume EXPERIMENT_PATH
python tools/score_embeddings.py resume EXPERIMENT_PATH --max-new-features 0
```

`--max-new-features` limits fresh inference in an invocation. Completed jobs and valid shared cached features can still be reused at zero budget. Cache/model directories can be selected with `--cache` and `--model-cache` on start. Shared feature entries have their own OS locks; another process holding that lock causes a resumable local failure. Source/package/preprocessing changes require a fresh experiment, preventing mixed results. A local inference interrupted before publication can retry; if its vector was published, resume reuses it. There are no paid provider calls in this path.

The real run paused after two features, resumed the remaining 12, then ran a cache-only repeat. All 14 jobs retained one attempt. A fresh experiment reused all 14 shared entries with zero new inference and no model loading. The [proof JSON](clap-probe-proof.json) records source fingerprints and unique invocation log names; dense vectors remain in the ignored cache.

```sh
python -m unittest discover -s tests -p test_score_embeddings.py -v
```

The 14 plumbing tests use explicitly fake vectors and need no ML packages. They check identity keys, explicit silence/window hashes, chunked resume, publication-time crashes, shared-cache reuse, tampering, changed packages/audio/manifests, collapsed encoders, shuffled controls and wording sensitivity. The proof above is separate real-model evidence. The shipped reader still uses local deterministic synthesis and has no model, Python, build or network requirement.
