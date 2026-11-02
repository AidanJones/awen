# Authored parts and chapter context

Implemented 1 November 2026. `awen-symbolic-score-1` is a development-only
representation exported by `tools/symbolic-score.cjs`. It calls the production
`planStep` function without Web Audio. The reader remains a single HTML file;
its sound generation, continuity and limiter are unchanged.

## Representation and coverage

- A bounded request includes genome, seed, book, step count and an explicit
  intent timeline. Chapter policies require that timeline. An optional composer
  snapshot continues the exact absolute clock, gate/density state and epoch.
  Invalid snapshots are rejected rather than silently restarted.
- Each event has a local step, absolute step, original planner role and a stable
  authored part: `dsl.bass`, `dsl.figure` or `dsl.chord`. The figure includes
  resolving neighbours; cadence bass belongs to the bass part. These identities
  come from declared DSL roles, not inferred layer or pitch. They do not assert
  independent contrapuntal voices or physical oscillator identity.
- Each step records actual chord pitch classes, style, active preset, epoch and
  tonal region, as well as requested/active chapter. Harmony overrides retain
  their absolute harmonic clock; classical recipe cycles use their actual epoch.
  Non-DSL planners currently fail explicitly because they lack declared roles.
- Continuous-bed harmony targets are recorded from the planner's voicing.
  Oscillators, acoustic envelopes, crossfades, mix, activity filtering and sound
  levels are outside this representation. Planned notes are not a native render
  trace. The exporter makes that distinction machine-readable in `coverage`.

`tools/symbolic_score.py` validates source identities, voice declarations,
per-step context, note bounds and clocks. It analyses each part separately,
splitting at active chapter/preset/epoch/style changes. Absolute phrase origins
prevent a resumed window from inventing a melodic transition across a phrase
boundary. Empty parts and simultaneous notes in a part produce the critic's
existing abstentions. Per-part activity is not whole-score activity. Pattern
metrics describe local segment bars, including possible partial bars.

There is no counterpoint/fifths penalty or combined quality reward. The previous
[scheduled-trace critic](symbolic-critic.md) still reports its separate coverage.
Neither representation assesses annoyance or listening preference.

## Small reproducible pilot

```powershell
# Choose a new output filename; the generator refuses to replace an old export.
node tools/symbolic-score-fixtures.cjs .score-lab/NEW-scores.json
python tools/symbolic_score.py start --input .score-lab/NEW-scores.json
python tools/symbolic_score.py resume PRINTED_EXPERIMENT_DIRECTORY
node --test tests/symbolic-score.test.cjs
python -m unittest discover -s tests -p test_symbolic_score.py -q
```

For custom requests, `node tools/symbolic-plan.cjs INPUT_JSON NEW_EXPORT_JSON`
accepts an array of requests. Existing fixed-context callers still receive
`chords` and `style`; richer metadata is additive. Start creates a timestamp/UUID
directory, frozen input/source identities, atomic journal and unique invocation
and attempt logs. Published results recover without rerunning completed jobs.
Changed sources or corrupt results require a fresh experiment; archived reports
remain evidence of their original versions.

The [fixture](symbolic-score-fixtures.json) runs all nine classical homes for
96 steps each. A requested chapter change at step 11 commits at 32; backward
navigation requested at 59 commits at 64. All nine exports and analyses completed:
864 planner steps, 27 active-context segments and nine journalled jobs. The
[proof](symbolic-score-proof.json) binds the sources, input and report; an audited
completed replay forbids waveform opens, preserves the report and adds no attempts.

Tests compare every exported event and bed-harmony target with the production
planner, check mid-phrase snapshot continuation, fixed harmonic compatibility,
missing context, polyphonic abstention, crash-publication recovery and tamper
rejection. These are engineering results on authored controls, not a listener
study or proof that the critic predicts good music. The next planned task is the
[narrative dictionary](narrative-dictionary-plan.md), before multi-critic selection.
