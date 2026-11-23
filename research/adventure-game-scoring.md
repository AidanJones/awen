# Adventure-game scoring: Scrimshaw and iMUSE

Reviewed 23 November 2026. Research and proposed experiments; no runtime change
or new listener results. Active work is tracked under `awen-syq.2`.

## Why this is relevant

Point-and-click exploration is a useful design analogy for reading: the listener
can linger, revisit a place or advance unexpectedly. Our inference is that music
which tolerates uncertain dwell times is a promising starting point. This is not
evidence that game soundtracks improve reading comprehension or comfort.

[Simon Willison's 6 October article](https://simonwillison.net/2026/Oct/6/scrimshaw-jukebox/)
reports an LLM-assisted experiment creating an editable text music format, a
browser player and six original adventure-style compositions. His positive
impression is an anecdotal authoring result; he explicitly calls for controlled
comparisons before concluding that a new model capability has emerged. It does
not validate a scene-matching reward, a reading intervention or an adaptive score.

## What Scrimshaw contributes

The [linked tool](https://tools.simonwillison.net/scrimshaw-jukebox) separates
settings, named voices, multi-bar patterns and arrangement. Patterns can inherit
parts and change or mute voices. Arrangement supports a one-off introduction,
repeating sections, repetition and transposition. Bar validation gives useful
repair diagnostics. Its piano roll and voice muting make the score inspectable.
These are useful authoring ideas for a development-time LLM or a person; playback
can remain entirely local and deterministic.

I inspected the [public source at revision d97b73d](https://github.com/simonw/tools/blob/d97b73dfdb2cd52ea01a76514846a69471901c9a/scrimshaw-jukebox.html).
Its parser compiles patterns into intro/loop event timelines, and its scheduler
repeats those timelines. This is a composed jukebox arrangement, not a
text-conditioned narrative director. The inspected version is the current linked
source, not a recovered snapshot of the article's publication day. Source SHA-256:
`69b478773cc518fbc858f2a7adea8400f1740702d39a8684594719368f1a919d`.

## What adaptive adventure scores contribute

In a [2012 firsthand interview](https://alternativemagazineonline.co.uk/2012/01/02/interview-in-conversation-with-peter-mcconnell-video-game-music-composer/),
Peter McConnell describes iMUSE transitions as depending on the current musical
position, with musically meaningful transition points and composer-planned
instrumental part enabling. He identifies Monkey Island II as its first outing.
The original Monkey Island inspiration in Simon's prompt and Monkey Island II's
adaptive architecture are distinct references.

The [Land–McConnell technical disclosure](https://patents.google.com/patent/US5315057A/en)
describes musical markers/hooks, queued commands and prepared transition material.
The practical lesson is to compose allowable exits and connections: merely
crossfading two unrelated phrases does not make them harmonically compatible.
This document describes a design, not evidence of listener preference.

McConnell's [2011 interview](https://www.squareenixmusic.com/features/interviews/petermcconnell.shtml)
also describes different composers handling islands in Monkey Island II while
using shared themes alongside local material. For Awen, this suggests retaining
a book's identity while offering related scene treatments. It does not imply
that a character/location classifier or a universal emotion-to-chord mapping
already exists.

## Mapping to Awen

These are proposals derived from the sources above and the existing engine.

| Idea | Existing support | Bounded extension |
|---|---|---|
| Related musical sections | Seeded motifs, DSL figures and chord cycles | Named multi-bar sections and explicit A / A-prime / B form |
| Variation without losing identity | Persistent cursor, scene dwell and layer controls | Keep harmony/theme; vary accompaniment, rests, register and motif spacing |
| Prepared transitions | Bar/phrase scheduling and chapter harmony crossfade | Context-valid exit markers and short authored bridges |
| Inspectable score | DSL parser and partial symbolic export | Validate section lengths and expose arrangement/voice provenance |
| Model-assisted composition | Development-only evaluation tools | Generate original grammar-valid candidates offline; no model during reading |

The current recipe DSL is not a general explicit-note sequencer. Numeric
preference evolution does not yet mutate multi-section form. Neither Scrimshaw's
parser nor its instruments have been imported. Awen should first test a small
extension rather than replace its renderer or require Strudel.

Within chapters, preserve the current structural stability policy: gentle
expression/layer changes, with larger changes at chapters or explicit user
selection. A transition planner must bound waiting time and handle rapid
navigation, backward jumps and sustained notes. Browser previews must retain the
shared limiter. MIDI needs note cleanup and separate listening on the FM1;
its own audio output is outside the browser limiter, and the same notes need not
sound equally good on different patches.

## Small proof before scaling

1. Author one original 16-bar family for a Stainless Steel Rat caper passage,
   with a quieter related treatment for reflection. Sixteen bars is an experiment
   choice, not a literature-derived optimum. Retain a common theme and harmonic
   plan; add intentional breathing space and a compatible loop seam.
2. Compare the current composer with the authored arrangement using the same
   passage, palette, seed, playback duration and comparable measured level.
   First isolate arrangement from timbre. Add adaptive layering/bridges only
   after this static comparison is useful.
3. Check symbolic timing, bounded pitches/voices, loop seams, deterministic
   replay/checkpoints and note release. Save unique run manifests and resumable
   state through the existing development lab.
4. Listen across several loop cycles. Collect scene fit, enjoyment and reading
   distraction independently, including optional FM1 listening. Use the existing
   [recurrence protocol](recurrence-listening.md) and
   [reader feedback](reader-feedback.md); engineering checks are not quality
   judgements. CLAP may remain a diagnostic, not the selection authority.

If this pilot helps, extend structural evolution to arrangement choices and
evaluate marker-aware transitions under `awen-syq.2` and `awen-cjl`. Do not create
a large film/game corpus or train a reward model before this comparison produces
real evidence. See also the [DSL](bach-dsl.md),
[classical development](classical-directions.md) and
[continuous-score review](../continuous_score_review.md).
