# Roadmap: ML feedback for continuous reading music

1 November 2026. The target is a development-time loop that proposes bounded
music, renders the real browser engine, scores separate objectives with ML,
retains useful trade-offs and exports small musical settings. Ordinary reading
and personal numeric evolution remain model-free.

## Stages and promotion gates

| Stage | Deliverable | Acceptance gate / current status |
|---|---|---|
| M0: end-to-end plumbing | Native audio → model inference → objective vector → Pareto parents → seeded offspring → replay page | Implemented in `tools/multiobjective_lab.py`; test/real-run evidence is recorded separately below. No automatic adoption. |
| M1: existing real encoder | Actual pinned CLAP association margin on three scenes, four roots and one small generation | Run with existing local weights, sanity guard, raw window/caption results and diagnostic controls. A successful run proves integration, not fit validity. |
| M2: learned generic music evaluator | Replace synthetic enjoyment feedback with one pretrained audio-only scorer | Preflight Audiobox Aesthetics or a compatible TuneJury audio-only model; pin exact encoder/head/config/preprocessing and licence. Verify CPU costs and degraded/control behaviour on the same WAVs before more search. Not implemented yet. |
| M3: learned scene preference | Compare raw CLAP with a learned text/audio preference reward | Use independent dramatic-function briefs, scene shuffles, unused wording and fresh seeds. Test exact encoder/head compatibility; dimensions alone do not establish compatibility. Not implemented yet. |
| M4: reading comfort / personal taste | Small ranker over frozen representations and separate reader choices | Keep fit, enjoyment and distraction labels distinct. Model-generated estimates are not actual reading comfort. Hold out scenes/works and report uncertainty. No real comfort training yet. |
| M5: richer evolution | Bounded figure, rhythm, harmonic pacing and texture mutations | Parser/voice-leading bounds, chapter-only structural changes, exact lineage, archived replay and fresh-seed checks before promotion. The current pilot mutates numeric traits only. |
| M6: sequential policy, if justified | Optional chapter-level policy learning / RL | Consider only after stable rewards and a demonstrated limitation of the genetic search. More optimisation does not repair a weak reward. |

M0/M1 can proceed without a large corpus or paid judge. M2 is the next model
replacement task, not a reason to train a joint encoder from scratch. Keep a
small reference evaluation frozen while the model changes. A higher score is
not enough to change a runtime default.

## Completed M0/M1 engineering run

Run `.score-lab/multiobjective/20261101T200556.044111Z-1da391d7f77d4f64ad473e182a851c7c`
completed on 1 November. The [proof](multiobjective-prototype-proof.json) binds
the manifest, report, page, model artifacts, source hashes and per-candidate
scores. It contains actual native audio/CLAP evidence and explicitly synthetic
test-model outputs, not human preference results.

- 18 native 32-second musical renders; nine derived diagnostic controls.
- 54 newly computed CLAP features and 12 shared-cache hits; 115 verified jobs.
- 12 musical candidates passed the existing gates. Six storm/spring roots were
  rejected for insufficient symbolic variation; their deliberate repeated
  figures expose a limitation of that heuristic. Maximum musical sample peak
  was 0.072772, below 0.14.
- Three Pareto trade-offs per scene remained. This is a front under the test
  objectives, not three validated musical recommendations.
- Two actual processes exited using the render-publication crash hook. Resume
  recovered both results with one render attempt each. All 115 jobs ultimately
  had one execution attempt. Failed-local-job retries with separate attempts
  are covered by a separate fake-worker unit test.
- Eight unique invocation logs include pauses, crashes, completion and completed
  replay. Zero-budget completed replay preserved the report hash with no new
  render, encoder feature, job attempt or model loading.
- 61 Python tests passed with two optional skips; 63 JavaScript tests passed.
  Isolated Playwright verified real WAV playback, no autoplay, exclusivity,
  Stop/Escape, disclosures and mobile layout.

The controls prevent a quality conclusion. For Rat escape, CLAP margin for the
two-second loop was 0.024531 versus 0.009888 for the flowing baseline; the
synthetic comfort head scored silence about 0.9998. Those controls never enter
the selected front. M2 must replace synthetic feedback and examine these failure
modes before any claim of improved music. The pilot has no fresh-seed or
independent listener validation and has changed no runtime defaults.

## Test models implemented now

`tools/reward_test_models.py` fits three small ridge-regression heads using 192
synthetic feature examples and a separate 48-example synthetic check set. The
targets come from explicit rules, not people, a pretrained critic or listening.
They are intentionally replaceable engineering models:

- **Test fit:** predicts a rule-generated relationship between attack density,
  brightness and an explicitly synthetic scene-density target. This head is
  replaced by actual CLAP when `--fit clap` is selected.
- **Test enjoyment:** predicts an invented preference for moderate activity,
  variation and repetition. It has no access to scene context.
- **Test unobtrusiveness:** predicts an invented penalty for busy, bright,
  repetitive and louder signals. It has no access to scene context.

Actual PCM features include RMS, an amplitude-envelope attack estimate,
zero-crossing rate, a fixed-lag envelope-repeat diagnostic, envelope variation,
crest and a waveform-difference brightness proxy. They are bounded engineering
features, not a validated account of music perception. Model files preserve the
synthetic examples, seed, learned coefficients, feature order and synthetic
check loss. That loss only tests learning/reproduction of the artificial rules.

Future audio-capable models should score the verified WAVs; they must not infer
quality from recipe names, classifier labels or filenames. The replacement
points are `Engine.score_file` and the separate reward-model module. Each new
backend needs pinned artifacts, explicit axis semantics and its own cache
identity; changing model/source requires a new experiment. Do not relabel the
test heads as learned human preference models.

## Frozen pilot

The [suite](multiobjective-suite.json) freezes three already attributed passages:
Rat escape, Riders landscape and Time Machine discussion. Each receives four
classical root directions with matching palettes, then two offspring from
Pareto parents. That is 18 musical clips, not 18 listener observations. Three
diagnostic variants per scene add silence, half-level and a two-second loop.

Two ten-second windows per clip support CLAP scoring. The fit objective is the
mean similarity to the scene's two independent musical briefs minus the mean
similarity to the other scenes' briefs. Raw window/scene means remain in the
report. A third description per scene is excluded from selection and scores
only the final front. It is an unused-wording check, not an independent human
fit label or unseen-work evaluation. No fresh-seed generalisation is claimed
by this first run.

Signal/continuity gates are mandatory before selection. Controls are always
nonselectable, independently of their scores. Pareto dominance compares axes
separately; no arbitrary scalar average combines cosine margins with test
regressions. A normalised crowding calculation picks up to two front members
as parents, seeded numeric mutation generates children, and the final front
retains nondominated ties. There is no single declared musical winner.

The existing symbolic-pattern-count gate is an experimental artistic constraint,
separate from physical signal and continuity correctness. It may reject a
deliberate ostinato. Record such rejections and calibrate the criterion later;
do not weaken it during a run to obtain a desired ranking.

## Run and resume

No change or build is needed to run `index.html`. For development rendering,
install Playwright or point `NODE_PATH` to its existing installation. Use an
isolated browser profile; the user's browser tabs are not required.

```powershell
$env:AWEN_BROWSER_CHANNEL = 'msedge'
# NODE_PATH must resolve Playwright if it is not installed locally.
python tools/multiobjective_lab.py start --fit test --max-new-renders 1
python tools/multiobjective_lab.py resume PRINTED_EXPERIMENT_PATH

# Existing pinned local CLAP environment and weights; no automatic download.
& ./.score-lab/clap-venv/Scripts/python.exe tools/multiobjective_lab.py start --fit clap --max-new-features 3
& ./.score-lab/clap-venv/Scripts/python.exe tools/multiobjective_lab.py resume PRINTED_EXPERIMENT_PATH

# Completed replay must need no new rendering or encoder inference.
& ./.score-lab/clap-venv/Scripts/python.exe tools/multiobjective_lab.py resume PRINTED_EXPERIMENT_PATH --max-new-renders 0 --max-new-features 0
```

The created directory has a timestamp/UUID, immutable manifest, saved test-model
artifact, source/package identities, write-ahead job records, unique invocation
and attempt logs, native WAV/trace hashes, verified CLAP cache entries and atomic
checkpoints. Kernel locks prevent simultaneous writers and release after process
death. Published results can be recovered before re-execution; failed local
jobs get a fresh attempt. Corrupt artifacts or changed source/model identities
fail rather than being silently replaced. Budgets limit new work per invocation.

`public/multiobjective.html` plays actual rendered clips and shows the three
objectives, front membership and excluded controls. Stop, Escape and exclusive
playback are available. The page and report prominently identify synthetic
feedback, zero human labels and `promotionAllowed:false`. No profile or new
default is automatically installed in the reader.

## Evidence boundaries

Unit tests use clearly labelled fake encoders/audio to test contracts, training,
Pareto selection, pause/replay, recovery and tamper rejection. Native runs and
actual CLAP inference must be reported separately. A real CLAP run still has
synthetic enjoyment/comfort heads; it is not a three-objective validated reward.
The existing [learned-feedback plan](multiobjective-reward.md) describes the
scientific controls and model candidates. Further evidence should be added with
exact run/proof references rather than rewriting old results as new validation.
