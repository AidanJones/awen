# MuQ-MuLan versus CLAP: small matched-file diagnostic

31 October 2026; `awen-3fr.6.2.2`. This is the first actual alternate-encoder inference experiment in Awen. It does not train a model or run another evolutionary search.

## Frozen scope

The [suite](muq-comparison-suite.json) selects five already rendered search-seed clips before MuQ scores are inspected: familiar warm ensemble, original Driving strings, desert, background-led, and the earlier CLAP-evolved strings. Two ten-second windows start at preview seconds 2 and 18. Both models receive identical PCM and the same six descriptions from the previous grid experiment. Three unrelated captions check extreme text-tower collapse. Silence and a half-amplitude copy of the evolved clip are separate controls, not selectable music.

All clips belong to the same previously inspected Rat safe-drop paragraph. The candidate pool was produced using CLAP; it is not an unbiased test set. No human fit, taste or distraction labels exist. We compare within-model rankings, action-versus-reflective margins, wording/window reversals and control failures. Raw cosine magnitudes from different models are not calibrated and do not establish which model is more accurate.

## Exact model and implementation

The [model specification](muq-model.json) pins MuQ-MuLan revision `2e01c796b71dca71b45251384c04cd7b237c9020`, source commit `28847ea50cd31ac4b8b6a7dacc051ad7d1c7606a`, audio architecture config and XLM-R configuration/tokenizer revisions. The main 2,653,954,401-byte checkpoint has SHA256 `d42ae3f7cb9b66759ee0089ddc70e2f28b130c2d8ba621457358272d32dd0444`. Additional local config/tokenizer files have explicit size/hash checks. The installed package's 23 Python source files are hashed against the pinned source tree.

This implementation uses the official MuQ/MuLan modules and forward path. To avoid downloading redundant base-network weights, the adapter instantiates both base architectures from pinned local configs, then strictly loads the complete main state dictionary. The successful preflight loaded all 805 entries with no missing or unexpected keys. This is not partial loading, a substitute encoder, or a new trained model. The local pinned tokenizer is supplied explicitly. Offline environment settings prevent implicit downloads or remote code execution at inference.

Inference is CPU float32 with two threads, a fixed seed, evaluation/inference mode and deterministic PyTorch algorithms. Audio is exactly 240,000 mono PCM16 samples divided by 32768, with no resampling or gain change for MuQ. The official single-clip serial path returns a 512-dimensional embedding, validated for shape, finite values and unit norm. Text is processed individually with the pinned tokenizer; overlong text is rejected. CLAP uses its previously pinned preprocessing and verified cached vectors from its original environment. No CLAP feature is recomputed using the MuQ environment.

Official MuQ code is MIT; released weights are CC BY-NC 4.0. This is a local research comparison, with no weights redistributed or bundled into the reader. Sources: [official repository](https://github.com/tencent-ailab/MuQ), [pinned weights](https://huggingface.co/OpenMuQ/MuQ-MuLan-large/tree/2e01c796b71dca71b45251384c04cd7b237c9020), [weight licence](https://github.com/tencent-ailab/MuQ/blob/28847ea50cd31ac4b8b6a7dacc051ad7d1c7606a/LICENSE_weights).

## Environment, cache and recovery

Use a separate environment. The existing CLAP installation remains unchanged (Transformers 4.57.1/tokenizers 0.22.2); MuQ uses Transformers 4.38.2/tokenizers 0.15.2. On this machine the new environment references the existing CPU Torch installation through a local `.pth` file to save disk, while its own packages take precedence. A fresh standalone environment with the pinned requirements is also supported; the shared-library optimisation is not required.

```powershell
python -m venv .score-lab/muq-venv
& ./.score-lab/muq-venv/Scripts/python.exe -m pip install torch==2.8.0 torchaudio==2.8.0 torchvision==0.23.0 --index-url https://download.pytorch.org/whl/cpu
& ./.score-lab/muq-venv/Scripts/python.exe -m pip install -r tools/muq-requirements.txt
& ./.score-lab/muq-venv/Scripts/python.exe tools/prepare_muq.py --download
& ./.score-lab/muq-venv/Scripts/python.exe tools/compare_muq.py start --source OLD_GRID_EXPERIMENT --max-new-features 3
& ./.score-lab/muq-venv/Scripts/python.exe tools/compare_muq.py resume NEW_EXPERIMENT
```

The helper downloads only explicitly pinned files; without `--download` it only verifies them. Checkpoint loading also verifies checksums. Weights are downloaded once and reused, without corpus collection. The fixed benchmark requires 22 distinct MuQ features (nine text, ten clip windows, silence and two level-control windows). All corresponding CLAP vectors must already exist in the verified original cache; missing vectors cause an explicit failure, not silent encoder substitution.

The driver reuses the existing atomic job journal, OS locks, content-addressed feature cache, per-attempt logs and timestamp/UUID experiment/invocation names. Cache identities include the separate model, code, package versions and preprocessing. A budget of zero permits completed/cache reuse without fresh inference. Source, model or package changes require a new experiment. Tests use synthetic scores only for engineering checks; they are never entered as benchmark results or listener preferences.

## Completed results

Run `.score-lab/muq-comparison/20261031T112116.671508Z-c2abf97a78e443a3a4e05ff66b9cc3d0` completed with 22 new MuQ features and no new native audio renders. The [proof](muq-comparison-proof.json) records all per-window/per-caption scores, both complete model identities, original audio hashes, package/source hashes and the report checksum. The original CLAP vectors were read from their verified cache; no CLAP inference was run in the alternate environment.

| Within-model diagnostic | CLAP | MuQ-MuLan |
| --- | ---: | ---: |
| Best target-description mean | Evolved strings | Desert |
| Best unused-description mean | Evolved strings | Warm ensemble |
| Clips below silence on target mean | 2/5 | 5/5 |
| Clips below silence on unused mean | 5/5 | 2/5 |
| Candidate pairs reversed between windows | 0/10 | 6/10 |
| Candidate pairs reversed between target descriptions | 1/10 | 1/10 |
| Clips with positive action-minus-reflective margin | 2/5 | 0/5 |

Both text towers passed the same extreme-collapse guard. That does not establish semantic reliability. The models agree on 7/10 target-ranking pairs and 4/10 unused-ranking pairs. Halving the evolved clip's amplitude changes target mean by −0.001963 for CLAP and −0.003488 for MuQ; these are within-model changes, not accuracy differences.

MuQ reduces one silence failure count but worsens the target-mean silence result and window stability. It favours a different interpretation under unused wording. This mixed evidence does not support a dependable replacement reward. It also does not prove CLAP more accurate at narrative fit: there are no listener reference labels and the pool was previously selected using CLAP. No weights were trained, no new candidates were generated, and no runtime defaults/preferences were changed.

The real experiment paused after three features, replayed at zero budget, resumed to completion and replayed again at zero budget. Each executed job has one attempt, and completed replay required no fresh inference or checkpoint loading. Unit checks cover artifact tampering and separate silence/wording/window/level diagnostics; the full Python suite passed 55 tests with two optional skips and the JS unit suites passed 53 tests. The existing open paper was updated in place with the measured comparison and successfully recompiled. The next useful gate is explicit listener calibration, or a separately controlled learned-preference reward probe—not a larger search against either raw cosine.
