# Adaptive nine-card exploration

Implemented 23 November 2026 for `awen-syq.2.6`. This extends the
[existing explorer](nine-direction-exploration.md) following the
[Picbreeder source review](picbreeder-adaptive-exploration.md). It uses bounded
authored musical components; it is not NEAT, a learned reward or unconstrained
score-grammar evolution.

## Use it

Listen to the starting cards and **Select for next round** on one to three
favourites. No explanation or rating scale is required.

- **Explore selected directions** keeps the selected cards unchanged. With one
  parent, the nine cards are that parent, two close relatives, three medium
  departures and three broad alternatives.
- **More different options** widens the mix. It uses selected cards, or the
  retained favourites if nothing new is selected. From the default mix it offers
  one close, two medium and five broad children; widening again offers two
  medium and six broad children. All counts include the unchanged parent as the
  ninth card. At the maximum breadth, further requests resample the wider pool.
- **Refine selected directions** keeps composition, harmonic override and palette
  intact, changing only the existing numeric traits. Select a promising broader
  card to make it a new parent and refine from there.

With two or three parents, each remains unchanged and the remaining slots use
the beginning of the same breadth schedule, distributed across those parents.
Their genomes are not averaged together. Previous round restores earlier
branches; starting again from there replaces the later path. Export a backup to
keep a separate path before replacing it. Existing pins and profiles in the
reader are not touched by explorer actions.

Widening is a **search action**, not an enjoyment, fit, distraction, dislike or
tie rating. Equally enjoyable but different candidates need not trigger it.
History records the action and the actual generated changes without inventing
those missing labels. No dialogue or description is needed to provide feedback.

## What changes in the music

The donor pool combines the existing broad, Bach-inspired and classical-inspired
starting sets. Close children retain their parent's musical structure. Medium
children change one authored component: composition (phrase recipe/DSL), explicit
harmony choice, or instrumental palette. Broad children differ on at least two
of those component identities and retain the parent's warmth/softness preferences.
Other bounded traits come from the donor. Rhythm, gaps, support roles and chord
pacing change through these existing authored recipes; this does not introduce a
new live tempo controller or arbitrary notation generation.

A changed composition may itself affect harmony or instrumentation expressed in
its DSL. These are exploration categories, not isolated perceptual variables.
This is deliberately broader than the controlled form comparison. Component
differences and symbolic duplicate checks do not guarantee audible distance.
Volume is never used to create novelty, and busier music is not automatically
preferred. The native renderer, final output limiter, attenuation-only preview
balancing and single-playback/cancellation controls are unchanged.

This branches reader-compatible presets/genomes. It does not yet evolve the
offline explicit-note 16-bar arrangement from the earlier pilot. The user chooses
the actual parent on this grid; no synthetic selection is saved as their taste.
Ordinary reading, chapter continuity and the main reader's six-card preference
gallery remain unchanged. Adoption still requires an explicit reader-profile
download/import.

## Replay, provenance and compatibility

`tools/exploration-branching.cjs` is a dependency-free pure planner, inlined into
the generated HTML. Seed, parent snapshots, breadth and generation determine
candidate cards. New rounds store a unique ID, time, parent IDs, action, breadth,
donor IDs and changed fields. Duplicate children are rejected against the current
round's musical identities; display names and recipe comments are not novelty.
Generation is bounded and fails without replacing the current round if a valid
distinct branch cannot be made.

Backups retain the existing `awen-exploration-1` envelope with optional branching
version/source hash and round provenance. New exports validate that identity and
lineage on restore. Older backups without the fields are accepted and migrated;
their archived cards remain intact. Regeneration with a changed branching source
requires its corresponding compatible export, rather than silently mixing
algorithms. Replay is a frozen-genome/seed guarantee, not bit-identical DSP across
browser versions.

Generate a new unique bundle and serve it locally:

```powershell
python tools/exploration_page.py --include-reader
python tools/serve_review.py PRINTED_DIRECTORY --port 8004
```

The generator prints `.../explore.html`; pass its containing directory to the
server. The page, production runtime, branching planner and selected passages
are embedded in one HTML file. The optional reader copy is unchanged. The
manifest records engine, branching and page hashes. The localhost server can
serve either a public paired-review folder or a standalone explorer bundle,
and continues to support media byte ranges for paired audio seeking.

## Verification and limits

See the [engineering proof](adaptive-exploration-proof.json). Pure tests exercise
all four breadth levels, several authored families, multiple parents, immutable
snapshots, structural tier guarantees, duplicates, deterministic regeneration,
refinement and bounded failure. Isolated Playwright checks nine actual native
previews in a widened round, sample bounds, attenuation, new controls, replay,
reload, backups, old-backup migration, malformed lineage rejection and mobile
layout. Existing reader, explorer, DSL and classical regression suites cover
the preserved workflows. Automated selections remain synthetic test evidence.

There is no user listening result for the new widened grid yet. Distinct sample
hashes establish differing output, not artistic quality or perceptual distance.
The finite authored library bounds discovery. Longer listening, richer structural
mutation and perceptual calibration remain open; no CLAP or LLM score selects
or promotes a musical winner.
