# Academic working paper

**Evaluating and Personalising Continuous Procedural Scores for Literary Reading: A Reproducible Pilot and Research Protocol**

Open this folder or `main.tex` in the desktop app's LaTeX editor for the compiled PDF preview. The source uses a standard article layout, numbered equations, results tables and a bibliography. `comparison-results.tex` is an included section generated from the follow-on experiment; it is kept separate so measured results can be updated without rewriting the protocol.

This is a working paper, not a submitted or peer-reviewed publication. The author line intentionally names the project rather than assigning authorship to individuals. It reports the completed CLAP pilot, clearly distinguishes the post-hoc follow-on from a preregistered study, and specifies future model/judge/preference/reading experiments. Human labels and alternative-model inference are not claimed where none exists. Informal design feedback is not repackaged as study data.

Evidence is linked through `research/grid-clap-proof.json`, the evaluator-comparison proof, frozen suite files and the [experiment ledger](../experiment-ledger.md). Raw audio, features and model weights remain in ignored local experiment directories. No full public benchmark dataset or external human study has been released.

Version 0.2 (31 October 2026) adds the executed five-clip MuQ/CLAP comparison in `muq-results.tex` and replaces the previous statement that no cross-model inference had run. The built-in compiler successfully compiled the updated document; compile again after changing source. Standard local LaTeX tools can also compile `main.tex`. Publishing this draft externally and choosing named authors are separate decisions.

Version 0.3 (31 October) adds classical-analysis references, the bounded DSL,
nine original classical-inspired directions and the optional chapter/text
policy. Version 0.4 (1 November) documents the four dedicated instrument
palettes, layer-specific routing and procedural harpsichord, and expands the
artifact index. These are implementation/engineering additions; no new CLAP,
MuQ, human-preference or reading-benefit result is implied. Historical measured
tables remain tied to their original source snapshots.

Version 0.5 (1 November) describes the multi-objective integration prototype:
native rendering, actual optional CLAP, synthetic-label fitted test heads,
Pareto/crowding selection and one bounded mutation generation. Synthetic test
losses are not human preference accuracy; this does not replace the proposed
pretrained-critic and reader-calibration studies. See the
[implementation roadmap](../multiobjective-roadmap.md) for scope and commands.

Use the [research index](../README.md) for feature guides, proof scope and
reproduction commands. The classical [direction proof](../classical-directions-proof.json)
and [palette proof](../classical-palettes-proof.json) contain engineering data,
not listener labels. The palette choice remains separate from reader-profile
exports and must be selected manually after importing a grid card's profile.
