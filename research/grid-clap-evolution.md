# CLAP-guided grid pilot

Development-only experiment for `awen-0qr`, 27 October 2026. The question is whether a small CLAP-directed search can move the current nine-option grid toward an accompaniment description for the Rat safe-drop paragraph. This does not assume CLAP is a reliable evolution reward.

## Frozen design

The [suite](grid-clap-suite.json) was fixed before scoring. The [driver](../tools/grid_clap.py) packages the exact current browser grid and uses its actual `renderPreview` path: production composer/synthesis, limiter, 32-second excerpt, fades and attenuation-only level matching. Native note/state traces are captured alongside audio; no alternate Python synthesiser approximates the browser.

- One scene: the Rat safe-drop paragraph, including its preceding context.
- Nine original grid directions, then two generations of six numeric-trait variations. Each generation draws from the two highest-ranked eligible candidates, retains all ancestors, and never changes a child's palette, harmonic snapshot or phrase recipe.
- Fixed search seed `awen-explore-1`; two ten-second windows starting at 2 and 18 seconds.
- Objective: mean cosine similarity across two independently worded target descriptions and both windows. Descriptions describe comic action, momentum, tension and space for narration, without naming the grid's instruments. These are developer-authored accompaniment proposals, not human fit labels or a direct embedding of the long literary paragraph.
- Native safety/continuity gates remain separate. Candidates that fail them cannot be ranked into parenthood. Gates cover finite/bounded/non-silent output, no score/regime resets, smoothed-state bounds, symbolic variation and onset density. They do not measure coherence or artistic value.
- Only after selection: compare the familiar ensemble, best original grid candidate and final selected candidate using a fresh seed and two unused descriptions. The reflective-scene contrast, unsuitable metal/vocals caption, silence and half-amplitude winner are diagnostics, never optimisation targets or selectable candidates. No extra generation follows a failed check.

This is at most 21 search renders, plus fresh-seed finalist renders. Overlapping semantic descriptions and windows are correlated; they are not independent statistical samples. One fresh seed is a development stress check, not a held-out book or proof of generalisation. The phrase recipes/harmonies are bounded existing material; this search cannot invent a new instrument, orchestration rule or compositional structure beyond them.

## Running and recovery

Use the existing optional CLAP environment/checkpoint described in [the original probe](clap-probe.md). No download or upload is performed by this experiment. Node and isolated Playwright are development dependencies only.

```powershell
$env:NODE_PATH='C:/Users/aidan/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules'
$env:AWEN_BROWSER_CHANNEL='msedge'
& ./.score-lab/clap-venv/Scripts/python.exe tools/grid_clap.py start --max-new-renders 2
& ./.score-lab/clap-venv/Scripts/python.exe tools/grid_clap.py status EXPERIMENT
& ./.score-lab/clap-venv/Scripts/python.exe tools/grid_clap.py resume EXPERIMENT
```

Each experiment has a timestamp/UUID directory, pinned sources/model/packages, a captured standalone grid and a manifest checksum. It reuses the native evaluator's OS lock, atomic write-ahead journal, per-attempt directories, unique invocation/worker logs, verified render/trace hashes and the existing shared embedding cache. Feature keys bind exact PCM/text, checkpoint, preprocessing, packages and backend code. A crash after result publication recovers the result; failed local inference may retry but can reuse an already-published feature. Corrupt artifacts fail rather than being silently substituted. Source/package changes require a new experiment.

`--max-new-renders` and `--max-new-features` bound fresh work in an invocation; zero budgets allow verified completed/cache reuse but stop before new work. No paid provider calls are involved. The final report and generation reports are immutable; completed resumes replay cached work rather than doing more search.

Outputs under ignored `.score-lab/grid-clap/…` include `report.json`, `round-1.json`, `round-2.json`, jobs/traces/logs, and `public/comparison.html` with the three listening clips and reader-compatible profile downloads. The exact original grid is `public/explore.html`. Importing a profile remains an explicit listener choice; select its palette separately in the reader. Main reader defaults, saved preferences and prior calibration labels are untouched.

The comparison is openly labelled, not a blinded listener study. It plays one clip at a time, starts only on request, and supports Stop/Escape. Audio stays at its existing limited/attenuated levels. The report explicitly disallows deployment approval and does not invent listener preference or narrative-fit labels.

## Engineering checks

`tests/test_grid_clap.py` checks the frozen budget, exclusion of unused wording from the objective, interrupted-result recovery without a second fake inference, and corruption rejection. Fake features are TEST ONLY and never enter the real experiment. Existing evaluator/cache/recovery tests also apply. A real pause/resume and zero-budget replay are used in the pilot itself. Native browser rendering is verified by the actual experiment jobs; a larger dataset is not required for this proof.

## Completed pilot

Real run: `.score-lab/grid-clap/20261027T185612.586761Z-e3e0ef0d5bf340ca8513ad805fa4206c`. The full experiment ID and report checksum are in the [machine-readable proof](grid-clap-proof.json), along with the exact selected genome, all 21 search scores, per-window/per-caption validation deltas, source/checkpoint hashes and package versions. Raw WAVs, traces, vectors and full report remain in the local experiment, outside Git.

| Search stage | Mean target cosine |
| --- | ---: |
| Familiar warm ensemble | 0.185747 |
| Best original grid: Driving strings | 0.230422 |
| Best after generation 1 | 0.235743 |
| Best after generation 2 | 0.239399 |

The selected descendant retains pursuit strings, ensemble palette and minor-drive harmony. Relative to the original Driving strings card, activity falls from 0.95 to 0.406655, softness from 0.15 to 0 (firmer attacks), and background motion from 0.4 to 0.243618. Other numeric traits stay unchanged. It leaves more melody gaps while keeping the rhythmic string/bass framework; it does not introduce a new score structure or tempo.

The target-description gain over the best original was **+0.008976** on the search seed and **+0.008639** on the unused seed (0.220112 → 0.228750). The two unused descriptions also improved on average: +0.007344 on the search seed and +0.003150 on the unused seed. This is limited evidence that the numerical improvement survives those particular changes, not a confidence interval or independent listener result.

The checks prevent promoting this into a reliable reward:

- Only 3/4 unused-description/window comparisons improved on the search seed and 2/4 on the fresh seed. The fresh seed's second window lost on both unused descriptions; one description's two-window mean also declined on that seed.
- Silence scored **0.216163** on the slapstick check description, above the evolved music's approximately 0.132/0.116 on the two seeds. Its unused-description mean was 0.205376, above all musical finalists. Silence is excluded by native gates, but this still exposes a semantic-model failure.
- The evolved music also gained against the reflective-scene caption. Its action-versus-reflective specificity margin slightly decreased on both seeds. A higher target cosine did not establish a more specific match to the action paragraph.
- Halving the selected waveform's amplitude changed target cosine by −0.001963 (0.239399 → 0.237436). This single control did not erase the full gain, but illustrates that non-compositional changes affect the measurement.

**Conclusion:** the bounded evolutionary loop works and produces a candidate with higher average CLAP association. This run does not establish better literary accompaniment, personal preference or a dependable autonomous evolution reward. Keep CLAP as a development shortlist signal, compare the clips by listening, and obtain actual fit/enjoyment/distraction evidence before expanding the search. No defaults or personal preferences were replaced.

Engineering evidence: 24 native renders (21 search + 3 fresh-seed finalists), all search candidates passed gates; maximum measured post-preview sample peak 0.087693 < 0.14. There were 56 newly computed features and four shared-cache hits. The real run paused after two renders, replayed at zero render/feature budgets, resumed to completion, and replayed the completed experiment again at zero budgets. No job needed a second attempt and no finished render/feature was recomputed. Four unique invocation logs preserve these stages. The comparison page passed isolated Playwright checks for real audio, no autoplay, exclusive playback, Stop/Escape, profile assets and mobile layout. The Python suite passed 50 tests (two optional skips); the JS unit suites passed 53 tests.
