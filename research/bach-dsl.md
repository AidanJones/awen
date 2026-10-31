# Bach-inspired score DSL v1

Implemented 31 October 2026 in the single-file reader and the generated nine-direction explorer. These are original adaptations of techniques discussed in the [classical literature note](classical-inspiration.md), not BWV 1007 playback, a transcription, or a learned Bach model.

## Use it

In the reader's tuning controls, open **Score language editor**. Choose Flowing figured cello, Minor sequence or Figured dialogue gaps, then **Use this score**. **Compare Bach-inspired directions** opens the existing six-choice audition workflow. The sound palette **Warm ensemble · synthesised** preserves the requested bowed, guitar or felt articulation; other palettes intentionally reinterpret instruments. **Return to authored phrase recipe** and the existing undo control provide a route back.

Generate an explorer with `python tools/exploration_page.py`. Its **Bach-inspired nine** starting set crosses three original figures with bow, guitar and felt instruments. The broad set remains available. Earlier rounds, up to three retained parents, seeded variations, backups and reader-profile downloads use the existing workflow. These nine choices are a first structural/articulation comparison, not nine historical styles.

## Example and bounds

```text
score 1
name "Flowing figured cello"
key G2 major
instrument bow
bass pedal
figure b 1 2 n2 2 1 2 1
cycle I IV V7 I vi ii V7 I
gate 0.95
neighbor 0.4
cadence 4
breath 0
```

The fixed pulse is 72 BPM in 4/4, with eight eighth-note slots per bar. It deliberately simplifies the Prelude's surface rhythm. `b` selects bass; `1`/`2` select upper chord voices; `n1`/`n2` select a seeded lower diatonic neighbour and must resolve to the corresponding voice in the following slot; `-` is a rest. Upper voices use economical register movement. This is a procedural single-line figure, not independent counterpoint.

The strict parser accepts exactly one of every required field, at most 6,000 characters, and no executable code. Key roots cover C2–G3 with major/minor mode; instruments are bow/guitar/felt/reed/flute; bass is pedal/roots. Figures have exactly eight slots and include bass. Cycles contain 4, 8, 12 or 16 chords from `I i ii ii_dim iii IV iv V V7 vi VI vii_dim`. `gate` is 0.4–1.05; `neighbor` is 0–1; `cadence` is 4/8 harmonic steps and divides the cycle (one step per bar by default); endpoints must support V/V7 or V/V7–I/i closure. `breath` is 0/1, allowing a closing phrase gap. Presets are examples of this grammar, not a general notation importer.

## Integration and reproducibility

Canonical DSL source is stored in the genome's versioned `scoreDSL` snapshot, including pins, profile files, history, retained parents and evaluator candidates. Musical identity ignores comments and the display name. Seeded decisions and composer checkpoints retain deterministic planning. Composer version is now `awen-score-5`: incompatible older score checkpoints restart rather than silently continue with different notes. Archived generated review pages keep their embedded renderer.

Changes while playing queue at the existing phrase boundary. Paragraph navigation retains the audio graph, scene dwell and smoothing. Existing harmonic-library choices override the DSL chord cycle while retaining figuration; remove that choice to hear the authored cycle. The existing layer mixer and final output limiter also cover DSL playback and previews.

Evolution currently changes the existing bounded numeric genome traits and preserves the DSL source. It does **not** mutate grammar, discover counterpoint, or fit a classical style. Editing and preset selection provide structural changes. The development renderer uses the same recipe and native audio path, so later embedding/judge experiments can compare it without a second synthesiser. No model is required by the reader.

## Validation and limits

`tests/score-dsl.test.cjs` covers parsing, canonical identity, bounds, resolving neighbours, seeded replay, checkpoint continuation, harmonic overrides and profile/evolution preservation. `tests/score-dsl.browser.cjs` covers the editor, queued live changes, pins/export/undo/reload, grid evolution/mobile layout, nine native offline renders, silence and the evaluator signal/continuity gates. Those tests establish engineering behaviour, not cello realism, artistic quality or reading benefit. Actual listener comparisons are still needed.

The [classical directions extension](classical-directions.md) adds optional `texture line|lyric|pulse|chords`, `hold 1|2|4` (bars per chord) and `shape steady|swell|answer` fields with defaults `line`, `1` and `steady`. Existing sources remain valid. These fields create contrasting attack spacing, durations and phrase shapes. The separate versioned classical policy controls text expression and chapter changes; applying a raw DSL exits that policy.
