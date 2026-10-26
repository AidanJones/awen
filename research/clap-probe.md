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
