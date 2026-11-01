# Symbolic criticism without listening to the waveform

Implemented 1 November 2026. `tools/symbolic_critic.py` evaluates scheduled note
events and explicit harmonic context. It is rule-based, explainable and cheap;
it neither trains a model nor loads an audio evaluator. It does not replace
physical signal checks or establish musical enjoyment/reading comfort.

## What it measures

| Measurement | Interpretation / important limit |
|---|---|
| Melodic motion | Large within-phrase leaps, excluding long gaps and four-bar boundaries. Figured and lyrical styles have different advisory thresholds. A deliberate leap can be appropriate. |
| Harmonic context | Chord-tone proportion at note onsets, using the production DSL's actual chord plan. Chromatic notes are not automatically errors. |
| Ornament behaviour | Whether a non-chord melody onset moves to a chord tone within two slots and three semitones. This is a narrow local test, not full suspension/counterpoint analysis. With no explicit harmony, it abstains. |
| Rhythm and activity | Both notes/second and distinct onset clusters/second, so a chord is not mistaken for several separate attacks. A developer-selected calm/neutral/active range produces a soft target-match score. The ranges are Awen proposals, not validated text labels. |
| Repetition and contour | Repeated rhythmic/relative-pitch bar patterns and coverage. Repetition is reported, not universally penalised: an ostinato can be useful. |
| Overlapping intervals | Semitone-class and tritone-class note overlaps. These are symbolic diagnostics, not acoustic roughness or automatic bad-harmony penalties. |

The critic emits separate `melodicEconomy`, `ornamentResolution` and
`activityTargetMatch` advisory scores, with `null` when evidence is insufficient.
It does not average them into a universal quality score. Empty scores get no
positive score. Polyphonic melody layers abstain from single-line analysis.

The [music21 voice-leading documentation](https://music21.org/music21docs/moduleReference/moduleVoiceLeading.html)
demonstrates existing score-analysis machinery. Full parallel/hidden-fifth
checks require stable simultaneous voice identities; we do not implement them
from ambiguous layer numbers. They would also need a stylistic rationale rather
than being imposed on every genre.

[Herremans and Chew's MorpheuS](https://arxiv.org/abs/1812.04832) illustrates
structured generation with prescribed tension and repeated-pattern constraints.
It supports exploring a tension trajectory rather than maximising consonance.
Our first critic does **not** implement MorpheuS, Spiral Array tension or music21;
those are source-informed extensions, not claims about the current metrics.

## Run against the existing prototype

```powershell
python tools/symbolic_critic.py start --source EXISTING_MULTIOBJECTIVE_EXPERIMENT
python tools/symbolic_critic.py resume PRINTED_SYMBOLIC_EXPERIMENT
python -m unittest discover -s tests -p test_symbolic_critic.py -q
```

The importer verifies the completed source manifest, render input/result hashes
and trace checksums. `tools/symbolic-plan.cjs` exports chords from the same
production DSL compiler without starting Web Audio. This first exporter supports
fixed DSL contexts and explicit harmony overrides; dynamic chapter-state
reconstruction is not implemented and is rejected rather than guessed.

The analysed events are the full scheduled render trace, before preview cropping,
not necessarily the exact cropped listening interval. They include selected
note voices but omit the continuous oscillator bed and acoustic envelope details.
The nine silence/half-level/loop waveform controls are deliberately skipped:
their transformed WAVs do not have transformed symbolic scores. Reusing the
original score to claim those controls were assessed would be misleading.

Each analysis uses a timestamp/UUID directory, immutable inputs/source identities,
per-job results, unique invocation/attempt logs, atomic state and a writer lock.
Completed/published results recover through the existing evaluator journal.
Source/trace corruption is rejected. No waveform decoding, synthesis, new model
inference, reader profile update or default adoption is performed.

## Evidence and remaining work

The next controlled engineering experiment is implemented in
`tools/calibrate_symbolic.py`: 14 notation fixtures and 17 expected relations,
including style-sensitive advice, transposition, repetition and abstention.
See the [ordered work plan](critic-work-plan.md) and
[contrast proof](symbolic-contrasts-proof.json). Expectations are authored
alongside the rules; they are not independent perceptual calibration.

The initial run analysed all 18 saved musical score streams from the three-scene
prototype. It identified the intended resolving neighbours in the flowing
figure and flagged large lyrical leaps in the spring calls. Those calls can be
intentional; this is evidence that style assumptions matter, not that spring
music is wrong. The original symbolic-variation gate remains unchanged.

Unit tests cover resolved/unresolved ornaments, unknown harmony, style/phrase
boundaries, clustered attacks, polyphonic abstention, repetition, empty input,
invalid events, published-result recovery and tamper rejection. The saved
analysis proof records replay and coverage separately from ML results.

The [proof](symbolic-critic-proof.json) includes an audited replay that forbids
audio-file opens, preserves the report hash and creates zero new job attempts.

Next steps are better voice/phrase metadata, harmonic-context changes and
style-specific tension curves, then calibrated integration into the Pareto
evaluator. The [text dictionary backlog](narrative-dictionary-plan.md) should
supply explicit narrative targets. [Pretrained acoustic critics](pretrained-evaluators.md)
remain useful for rendering/timbre and perceptual properties that a score cannot
reveal. All these outputs remain distinct from actual reader preferences.
