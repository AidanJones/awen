# Research and implementation map

Documentation updated 3 November 2026. Classical audio work dates from 31 October;
critic and dictionary engineering runs extend through 3 November. This index separates
what runs in the reader from design evidence, development experiments and
uncompleted listener studies.

## Find a feature or its evidence

The [ordered critic work plan](critic-work-plan.md) links the recent research
to active Beads tasks and records the first controlled score-only experiment.
The [versioned symbolic export](symbolic-score.md) now records authored DSL parts,
chapter epochs and bed-harmony targets, with explicit coverage limits.

| Strand | Guide / specification | Evidence or implementation |
|---|---|---|
| Classical repertoire and source scope | [Classical inspiration](classical-inspiration.md) | [Source-linked recipes and cue rules](classical-knowledge.json) |
| Nine classical directions, text mapping and chapter route | [Directions and limits](classical-directions.md) | [Engineering proof](classical-directions-proof.json), `tests/classical.test.cjs`, `tests/classical.browser.cjs` |
| Classical sound palettes and harpsichord | [Palette guide](classical-palettes.md) | [Engineering proof](classical-palettes-proof.json), `tests/classical-palettes.browser.cjs` |
| Declarative score grammar and profile compatibility | [DSL guide](bach-dsl.md) | Inline parser/planner in the [reader](../index.html), `tests/score-dsl.test.cjs` |
| Wider personal exploration and backups | [Nine-card explorer](nine-direction-exploration.md) | [Standalone-page generator](../tools/exploration_page.py) |
| Film/theatre harmonic knowledge | [Scoring knowledge](scoring-knowledge.md) | [Library](scoring-knowledge.json), [schema](scoring-knowledge.schema.json) |
| Instrument articulation and kinetic choices | [Articulation guide](instrument-articulation.md) | `tests/instruments.browser.cjs` |
| Reproducible development audio evaluation | [JavaScript lab](score-lab.md), [Python bridge](score-lab-python.md), [judge contract](score-lab-judge.md) | Unique runs, source hashes, native renders, cache/checkpoint recovery; models remain development-only |
| CLAP probes and grid evolution | [Probe](clap-probe.md), [bounded grid search](grid-clap-evolution.md) | Their linked proofs; optimisation gains did not establish a reliable reward |
| Evaluator and encoder comparisons | [Experiment ledger](experiment-ledger.md), [MuQ comparison](muq-comparison.md) | Completed diagnostics, model identities and remaining decision gates |
| Multi-objective ML feedback | [Roadmap and prototype](multiobjective-roadmap.md), [reward research](multiobjective-reward.md) | Native-audio/CLAP plus fitted synthetic-label test-head prototype; pretrained enjoyment/comfort replacement and scientific calibration remain open |
| Released pretrained critics | [Model inventory](pretrained-evaluators.md), [Audiobox probe](audiobox-probe.md) | Audiobox strict CPU loading and actual four-axis inference; other quality-model candidates remain untested |
| Score-only musical criticism | [Symbolic critic](symbolic-critic.md) | [Proof](symbolic-critic-proof.json), 18 verified note traces, no waveform analysis; style-dependent advisory rules |
| Repetition and variation gates | [Read-only review](variation-gate-review.md) | [Proof](variation-review-proof.json), 18 archived traces plus seven notation controls; no threshold change or listener calibration |
| Recurrence listening materials | [Pilot and recovery protocol](recurrence-listening.md) | [Preparation proof](recurrence-listening-proof.json), eight longer controlled clips, 14 blinded comparisons, four independent rating axes; real listener calibration remains open |
| Narrative-to-music dictionary | [Dictionary guide](narrative-dictionary.md), [reader panel](narrative-reader-ui.md) | [Versioned labels/mappings](narrative-dictionary.json), original mapping/UI proofs retain their versions; manual choices and automatic rule estimates remain separate |
| Automatic multi-label detection | [Implementation and limits](automatic-detection.md) | [Proof](automatic-detection-proof.json), all 28 categories reachable in authored controls, matched-book coverage audit; no independent accuracy claim |
| Real preference calibration | [Listening protocol](listening-calibration.md) | Prepared interface; no real listener ratings in the engineering proofs |
| Academic account | [Paper source](paper/main.tex), [paper guide](paper/README.md) | Compiled editor preview; measured results distinguished from proposed experiments |

The [root README](../README.md) covers running the app. The [roadmap](../TODO.md)
is a historical overview; Beads holds active status. Classical listening and
cadential-bridge follow-up is tracked as `awen-cjl`; broader listener/device work
remains under `awen-r42`. Structural grammar evolution and richer score analysis
are still open, rather than implemented by the numeric preference search.

## Which choices do what?

**Starting point / DSL** chooses figures, chord cycles, texture and phrase shape.
**Sound palette** chooses instrumental routing and colour. **Classical development
mode** chooses whether to hold a recipe, follow text gently, or develop between
chapters. **Harmony direction** can override the recipe's chord pitches and
pacing. The palette and composition are independent; selecting a recipe does not
silently replace the listener's palette.

Reader profiles preserve musical genomes, DSL and classical policies, pins and
history. They do not store the active sound palette. After importing a grid
card's profile, select its named palette manually. A full exploration backup is
a different, engine-bound format and preserves the grid rounds and palettes.
Browser settings/progress remain local to the browser origin. Downloads enter
Git only when the user saves and commits them; automated test choices are not
personal feedback.

## Reproduce the current engineering checks

The reader itself needs only `index.html`. Python below is an authoring/test
utility; Node/Playwright are optional development dependencies.

```powershell
# Verify the embedded classical library without changing the reader.
python tools/compile_classical.py --check

# Pure JavaScript planning, profiles, DSL and lab contracts.
node --test tests/mvp.test.cjs tests/score-lab.test.cjs tests/score-dsl.test.cjs tests/classical.test.cjs

# Create a fresh explorer: choose a new output name on every attempt.
python tools/exploration_page.py --output .score-lab/exploration/my-classical-check
$env:AWEN_EXPLORATION_PAGE = '.score-lab/exploration/my-classical-check/explore.html'
$env:AWEN_BROWSER_CHANNEL = 'msedge'
# Install Playwright in your test environment, or set NODE_PATH to its location.
node tests/classical.browser.cjs
node tests/classical-palettes.browser.cjs
node tests/score-dsl.browser.cjs
node tests/exploration.browser.cjs
node tests/audio.browser.cjs
node tests/evolution.browser.cjs
node tests/western.browser.cjs
```

The recorded 31 October unit run passed 63 JavaScript tests; palette/native
regressions also passed. The palette proof measures four 32-second renders;
the direction proof measures nine 64-second renders and asserts a 192-step
chapter traversal. These are different checks and should not be merged into a
single listening experiment. The original classical proof corresponds to the
implementation recorded in commit `d09ad62`; the palette proof is recorded in
`e92cdb5`. Hashes identify the exact tested source snapshots, not a promise that
every future checkout has identical bytes or DSP output.

Keep generated explorers and experiment directories distinct. Old pages embed
their own renderer; refreshing an old page does not install later code. Regenerate
after changes, and use the printed new path. Temporary localhost preview ports
are conveniences, not durable publication URLs. Existing lab recovery requires
matching source/model identities; start a new experiment for changed code or musical/model
configuration rather than weakening the resume checks. Follow the lab guides
for crashed runs, failed attempts, caches and ambiguous provider responses.

No CLAP, MuQ or LLM is required to read, synthesise or evolve numeric preferences
in the browser. None of the earlier embedding comparisons evaluated the new
classical grid or learned its cue mappings. Digital bounds, signal differences
and passing UI tests do not establish enjoyment, historical authenticity,
paragraph suitability or improved reading. Those remain explicit listening and
research tasks.
