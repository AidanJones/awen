# Audiobox aesthetics on the existing reading scores

Development experiment, 2 November 2026. The purpose is to replace synthetic
test feedback with an actual pretrained measurement before reward integration.
It does not establish a reliable enjoyment, scene-fit or reading-comfort reward.
The single-file reader is unchanged and never loads this model.

## Model, source and loading

The official [Audiobox Aesthetics repository](https://github.com/facebookresearch/audiobox-aesthetics)
and [model release](https://huggingface.co/facebook/audiobox-aesthetics) provide
four separate axes: Content Enjoyment (CE), Content Usefulness (CU), Production
Complexity (PC) and Production Quality (PQ). These names do not turn the outputs
into personal preferences, paragraph alignment or annoyance measurements.
In particular, low predicted complexity is not evidence of low distraction.

The [model specification](audiobox-model.json) pins repository revisions, 13
artifact sizes/checksums, preprocessing and core package versions. The local
415,472,992-byte safetensors checkpoint matches SHA-256
`a5a3c2412649cc2384ec525ffd5180ce6c4778f43bed6108e0a1303de04d014e`.
Source files were fetched at commit
`2618e9d451b456e9328b39495b5e6234678aa550` and their Git blob identities checked
against that commit's tree before use. The config is pinned alongside weights;
different head shapes or normalisation transforms are not interchangeable.
Upstream code/model attribution is CC BY 4.0 with separate MIT notices for
copied WavLM portions; the local source cache retains README/LICENSE notices.

The adapter constructs the official `AesMultiOutput` from that local config,
loads safetensors with `strict=True` and checks missing/unexpected keys. It never
calls a floating `from_pretrained` or loads a pickle checkpoint. CPU float32,
two threads and deterministic Torch operations are explicit. The isolated
`.score-lab/audiobox-venv` reuses read-only CPU packages from the existing CLAP
and MuQ environments through `.pth` paths; it does not upgrade those environments.
The small `rich` dependency used by the upstream diagnostic import is installed
only in the new environment. Core mathematical package versions are checked on
every invocation; weights/source checksums are checked before model loading.
No weights, package binaries or WAVs are committed.

## Preprocessing and outputs

Bounded PCM16 WAV input is decoded without an audio file backend. The adapter
matches the upstream tensor-input path: resample with torchaudio defaults to
16 kHz, channel mean, non-overlapping ten-second windows, zero-pad the final
window with the corresponding valid-sample mask, and aggregate using unpadded
duration weights. Windows run one at a time to limit memory. It applies the
checkpoint's per-axis inverse mean/std transforms. It adds no loudness
normalisation and does not clamp raw scores to the prototype's 0–1 test range.
Per-window predictions, weights and final raw axes are retained.

A diagnostic compares a bounded ten-second excerpt against the official
`AesPredictor.forward` using the same strict-loaded model and tensor input.
The initial maximum absolute difference was 0.000000347446, below 0.00001.
This checks preprocessing and target-transform fidelity, not listening validity.
Upstream weight-norm/attention-mask deprecation warnings were observed; they
did not prevent CPU inference. Peak resident memory has not been measured.

## Small pilot and interpretation

The initial chunk reused five verified Rat WAVs: flowing and storm scores plus
silence, half-level and two-second-loop controls. No new rendering, text labels,
training or generated musical dataset was needed.

| Rat clip | CE | CU | PC | PQ |
|---|---:|---:|---:|---:|
| Flowing baseline | 5.399 | 7.438 | 1.811 | 7.610 |
| Silence control | 3.252 | 6.463 | 1.702 | 6.751 |
| Half-level control | 5.350 | 7.463 | 1.706 | 7.640 |
| Two-second loop control | 5.120 | 7.467 | 1.819 | 7.838 |
| Storm alternative | 4.922 | 7.439 | 1.891 | 7.910 |

CE separated this baseline from silence and the loop. PQ preferred the loop to
the baseline; CU remained substantial for silence. These are control behaviours,
not proof that CE agrees with this reader or that storm is artistically worse.
The first 32-second score calls took approximately 11–16 seconds each on this
machine; initial import/verification/model loading took about 37 seconds in
the standalone smoke check. CPU timings include window processing and vary with
system load; first-load/official-equivalence costs are recorded separately.

## Completed frozen-pool result

All 27 existing WAVs completed: 18 musical clips and nine controls, across
108 windows, with no new renders. The [proof](audiobox-proof.json) binds source,
checkpoint/package identity, original report, raw axes and per-scene controls.

| Scene | Baseline CE | Silence CE minus baseline | Loop CE minus baseline | Loop PQ minus baseline |
|---|---:|---:|---:|---:|
| Rat escape | 5.399 | -2.147 | -0.279 | +0.228 |
| Riders landscape | 5.410 | -2.158 | -0.291 | +0.230 |
| Time discussion | 5.411 | -2.159 | -0.290 | +0.236 |

CE passed these baseline-versus-silence/loop comparisons in all three scenes;
PQ consistently preferred the loop. Half-level CE changed by approximately
-0.040 to -0.050; this is an observed level response, not calibrated invariance.
The identical silence files produced identical raw axes across scene records.
Because Audiobox does not consume a paragraph, this is not a scene-fit test.
No fresh-seed, independent-label, listener or long-session result is available.

Measured score calls totalled 325.454 seconds, with individual 32-second calls
between 10.762 and 15.704 seconds. The three model-loading sessions recorded
28.961, 13.498 and 16.415 seconds; loading and the official-equivalence checks
are additional to the score-call total. This is one machine's engineering cost,
not a cross-hardware benchmark. The largest upstream-equivalence difference
across those sessions remained below 0.000001.

An actual process was terminated after publishing the sixth result and before
journal completion. A zero-budget resume recovered it without another inference.
All 27 jobs ended with one attempt each. A completed zero-budget replay used a
factory that raises if a model is constructed: report bytes and job records were
unchanged, with zero new attempts. Failed local inference and unique retry
directories are checked separately using a clearly fake backend in unit tests.
Five unique invocation logs capture chunking, interruption, recovery and replay.

Original synthetic-head fronts remain historical TEST ONLY results; these
actual raw axes do not silently replace their contract. The next step is the
style-dependent variation-gate review, then an explicit multi-critic comparison.
CE can be a candidate enjoyment axis, while structural diagnostics, scene targets
and independently collected reading/taste feedback remain separate. No reward
fusion, new generation or runtime promotion has been performed.

## Reproduce and resume

Use the isolated environment with the exact versions in `audiobox-model.json`.
For a fresh install, CPU Torch/torchaudio wheels need their appropriate PyTorch
package index; the core versions include their `+cpu` build identity. The
upstream equivalence diagnostic also imports `rich`, `tqdm` and `requests`.
This machine's existing isolated environment is ready:

```powershell
./.score-lab/audiobox-venv/Scripts/python.exe tools/prepare_audiobox.py
# Explicit installation/download step only if missing:
./.score-lab/audiobox-venv/Scripts/python.exe tools/prepare_audiobox.py --download
./.score-lab/audiobox-venv/Scripts/python.exe tools/audiobox_lab.py start --source COMPLETED_PROTOTYPE --max-new-scores 5
./.score-lab/audiobox-venv/Scripts/python.exe tools/audiobox_lab.py resume EXPERIMENT --max-new-scores 1
./.score-lab/audiobox-venv/Scripts/python.exe tools/audiobox_lab.py resume EXPERIMENT
# Zero budget verifies/replays completed results without loading the model:
./.score-lab/audiobox-venv/Scripts/python.exe tools/audiobox_lab.py resume EXPERIMENT --max-new-scores 0
python -m unittest discover -s tests -p test_audiobox.py -q
```

Each new run uses timestamp/UUID directories, frozen model/source/input
identities, per-job results, unique invocation/attempt logs and a writer lock.
Native clips are checked against archived render inputs/results; all WAVs are
checksum-bound to the frozen source report. Controls remain marked and never
selectable. Resume checks WAV and result identities; source drift or corruption
is rejected. Published local results recover after interruption; failed local
inference retries in a fresh attempt directory. Zero budgets allow recovery of
already-published results without creating a new inference attempt.
