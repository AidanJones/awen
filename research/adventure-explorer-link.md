# Link the preferred review score to exploration

23 November 2026, `awen-syq.2.7`. The first adaptive grid linked back to a review
but used the reader's existing presets. It did not inherit the user's preferred
point-and-click arrangement. That mismatch is corrected in the **Adventure ·
your review favourite** starting set.

## What the user gets

The first card is **Original review favourite**: the original 16-bar arranged
score, seed and Romantic instrumental palette from the two reported A choices.
The caper and quiet-reflection plans are compiled from the original pilot, not
from the subsequent form-only comparison. The new set opens on the original
safe-drop paragraph, with the spaceport reflection also available. Its default
64-second excerpt spans a complete 16-bar cycle.

The other eight cards develop that score through spacing, longer lines, related
phrase orders, guitar/strings and a small number of harmonic treatments.
Descendants of adventure parents stay in this family, including wider branches;
they do not silently turn into unrelated ordinary presets. The first card remains
unchanged when selected as a parent. Normal preset families retain their existing
branching path.

The linked review is now checked against the actual preferred packet SHA-256.
Optional packaging copies only that frozen public review and its audio, with
byte-range serving for seeking. The older generic grid is preserved as a
separate frozen page. The adventure page uses a separate local-storage namespace,
so it does not overwrite earlier explorer choices. Prior review ratings remain
their original records; user preferences are not fabricated in browser storage.

## Score identity and limits

`research/adventure-starting-score.json` is a compact versioned seed containing
the original baseline genome, note/harmony plans and preferred packet identity.
`node tools/adventure-seed.cjs --check` checks it against the original compiler.
`tools/adventure-explorer.cjs` interprets only bounded form/texture descriptors;
it does not execute imported text. Cache keys and branch identities include this
descriptor, and backups retain it with the source seed hash.

Native scheduling of the reference card's first full cycle is checked against
every original note pitch, onset, duration and layer. The preview uses the same
production synthesizer and limiter; its excerpt length, edge fades and balancing
mean it is not a byte-identical copy of the archived 165-second WAV. Palette
and harmonic variations are intentional in other cards. Different sample hashes
are engineering evidence, not an audible-quality judgement.

The explicit-note arrangement is currently **explorer-only**. Full exploration
backups preserve it, but the ordinary reader profile format cannot represent it.
Its reader-profile button is disabled with an explanation, so it cannot export
an ordinary genome that would play different music. Reader/MIDI integration
needs a versioned score representation and remains follow-up work. The main
reader engine and its six-card gallery are unchanged.

## Reproduce

```powershell
node tools/adventure-seed.cjs --check
python tools/exploration_page.py --initial-set adventure --include-reader `
  --review-public ORIGINAL_PILOT/public --previous-page EARLIER_GRID/explore.html
python tools/serve_review.py PRINTED_DIRECTORY --port 54019
```

The two copy arguments are optional. A supplied review must match the preferred
packet; the later form packet is rejected. `--previous-page` preserves an older
standalone explorer beside the new one. The output directory is always new.

See the [engineering proof](adventure-explorer-link-proof.json). Tests cover the
source seed, exact note/harmony plans for both passages, bounded variations,
actual browser scheduling, nine native previews, family-preserving widening,
unchanged favourite, reload, backups, reader-export guard and review navigation.
All automated selections are synthetic. New listening on the linked family is
still needed; no new winner or learned reward is asserted.
