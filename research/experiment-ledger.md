# Evaluator experiments and next gates

Updated 31 October 2026. This ledger distinguishes executed evidence, engineering preparation and proposed studies. No real human study labels have been collected.

| Stage | Status | Evidence / decision |
| --- | --- | --- |
| Checkpoint/backend sanity | Executed | Earlier music-only text tower failed the extreme-collapse guard; pinned general CLAP passed that guard, not semantic validation. `clap-probe-proof.json` and rejected-checkpoint record. |
| Small scene-association probe | Executed | Four audio windows; wording and silence failures. `clap-probe.md`. |
| Nine-grid bounded evolution | Executed | 21 candidates + 3 fresh-seed renders. Mean gain, but unresolved controls/specificity. `grid-clap-proof.json`. |
| Fixed-pool objective comparison | Executed | Six methods selected five unique clips. Ensemble winner fell slightly below unchanged strings on new-description mean; contrastive selected an earlier variant, but silence/wording concerns remain. Post-hoc, same encoder, not an independent-model or equal-budget-optimiser benchmark. `evaluator-comparison-proof.json`. |
| Alternate encoder comparison | MuQ versus CLAP executed | Five matched existing clips and controls, 22 MuQ features, no new renders or training. Mixed silence and window results do not establish a reliable replacement. `muq-comparison-proof.json`. Other models remain unbenchmarked. |
| Audio-language judge controls | Protocol specified | Real audio dependence, swaps, missing/identical audio, abstention, wording and order controls; not yet run. No model-provider result is invented. |
| Human preference calibration | Interface prepared; labels absent | Existing blinded packet and exploratory grid. Use explicit fit, enjoyment and distraction feedback; an unheard/unselected card is not a rejection. |
| Personal ranker | Proposed | Begin regularised small model on engine/passage features; add embeddings in an ablation after labels exist. No RLHF or ranker training performed. |
| Matched-budget optimisation / long reading | Proposed | Evaluators must first demonstrate useful listener agreement; retain silence/fixed/diverse-grid baselines and whole-work holdouts. |

## Alternate-model preflight

Primary project documentation checked 27 October 2026; MuQ preflight and inference completed 31 October. Exact files/revisions and hashes are frozen for the executed MuQ comparison. Other entries remain implementation constraints, not local accuracy results.

- **TuneJury primary:** the authors describe a learned preference head over CLAP-Music and MERT features. Its setup documents gated MERT access and a separate roughly 2.2 GB music encoder. The main pipeline is CC BY-NC 4.0. It cannot consume our cached general-CLAP embeddings as a substitute. [Official README](https://github.com/yonghyunk1m/TuneJury), [checkpoint guide](https://github.com/yonghyunk1m/TuneJury/blob/main/checkpoints/README.md).
- **TuneJury audio-only variant:** the checkpoint guide identifies a 512-dimensional CLAP-audio head and matching configuration with an Apache-2.0 exception. It still expects its specified music encoder, and it is not a text-alignment evaluator. The root licence and per-artifact exception must be checked together before redistribution. Do not infer compatibility from the vector length. This is a plausible next generic music-preference baseline, pending an isolated adapter and exact artifact audit. [Artifact guide](https://github.com/yonghyunk1m/TuneJury/blob/main/checkpoints/README.md), [root licence](https://github.com/yonghyunk1m/TuneJury/blob/main/LICENSE).
- **MuQ-MuLan:** the pinned 24 kHz CPU float32 comparison is now complete. Main weights (2.65 GB), installed source and configuration/tokenizer files are checksum-bound; all 805 model-state entries load strictly without redundant base weights. The original CLAP environment is preserved. Mixed controls prevent promotion as a replacement reward. See [benchmark](muq-comparison.md) and [proof](muq-comparison-proof.json). [Official repository](https://github.com/tencent-ailab/MuQ).
- **CLaMP 3:** music retrieval with text/audio/symbolic branches; its documented audio path uses MERT-derived features and further encoder weights. The implementation and dependency tree must be reproduced, rather than treating it as a drop-in cosine formula over current features. [Official repository](https://github.com/sanderwood/clamp3).
- **Audio LLM:** reserve for controlled development judging, not browser inference. Select a genuinely audio-capable model, verify audio handling and access, cap calls, and test controls before comparing with human labels. A text-only critique is not an audio judgement.

The 27 October slice checked score formulations with cached features first. The 31 October slice added one isolated, pinned MuQ installation and a small matched-file diagnostic. It does not establish model superiority or human preference accuracy. Broader model comparison and preference studies remain open under `awen-3fr.6.2` / `awen-3fr.6`. The [paper](paper/main.tex) records measured results, research questions and promotion gates.

## Executed objective comparison

Run `.score-lab/evaluator-comparison/20261027T211526.117415Z-8f2a03146dd847b7bd3b54d75ba38e71` copied and verified the 21 original WAVs and reused their feature cache. A third seed and two new descriptions were fixed before this follow-on ranking. These are development stress checks, not a held-out narrative or preregistration. Selection from a pool produced by the old ensemble search favours that method; no equal-budget optimizer comparison is inferred.

| Selector | Chosen variant | New-description mean | Original-target specificity on new seed |
| --- | --- | ---: | ---: |
| Single caption 1 | Desert G1.4 | 0.206134 | −0.055112 |
| Single caption 2 | Strings G2.3 | 0.195895 | +0.009671 |
| Two-caption mean | Strings G2.3 | 0.195895 | +0.009671 |
| Target mean minus reflective caption | Strings G1.3 | 0.200552 | +0.012343 |
| Unchanged Driving strings | Original | 0.197513 | +0.011576 |
| Familiar warm ensemble | Original | 0.160119 | −0.070582 |

All columns are CLAP-derived, not independent quality measures. The first selector leads the new-description mean while preferring the reflective description over the original action descriptions. The two single-caption rankings agree on 75.7% of 210 candidate pairs. Silence's second-new-caption score is 0.224819 and its new-description mean is 0.195319. These results show objective sensitivity and unresolved construct validity; they do not establish a best musical selector.

Five fresh native renders, 12 new features and 46 shared-cache hits were sufficient. The experiment paused after one render, resumed, then replayed at zero new render/feature budgets. Each executed job has one attempt. The [proof](evaluator-comparison-proof.json) binds the report hash, methods, windows, source reports and model identity. `public/evaluators.html` provides five labelled clips for listening. Automated UI checks verify playback/exclusivity/Stop/Escape/mobile layout; no preferences are inferred from those checks.

```powershell
# In the existing optional CLAP environment, with NODE_PATH and browser channel set:
& ./.score-lab/clap-venv/Scripts/python.exe tools/compare_evaluators.py start --source OLD_GRID_EXPERIMENT --max-new-renders 1
& ./.score-lab/clap-venv/Scripts/python.exe tools/compare_evaluators.py resume NEW_COMPARISON_EXPERIMENT
```

That next slice is now complete: [MuQ/CLAP matched-file results](muq-comparison.md). Next, obtain explicit listener judgements for calibration or run a separate learned-preference reward probe with its own controls. Neither this cache-only rescoring nor the five-clip encoder comparison can train a personal reward without labels or establish a best listener model.
