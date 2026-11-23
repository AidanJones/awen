# Form comparison with one-click preference

23 November 2026. `awen-syq.2.4` follows the user's
[two initial preferences](adventure-listener-feedback.json) for the authored
adventure arrangement. This experiment asks whether phrase ordering matters,
without changing the notes and harmony between conditions. It does not change
the reader's default score.

## Listen and choose

The new page has two passages. Play A and B, then choose **A**, **B**, **About the
same**, or **Neither**. No description, rating scale, confidence or listening
checkbox is required. You can skip, clear or revise a choice. Choosing stops
playback; it does not automatically move to another passage. Finishing downloads
the choices, and the download button is available throughout. Browser storage
preserves progress; JSON download/restore provides a portable backup.

This is an **overall preference only**. It does not establish separate scene fit,
enjoyment, distraction, comprehension or fatigue scores. Those axes remain
unknown rather than receiving the overall choice. Paired comparisons suit this
one-factor experiment; the existing nine-card explorer remains the route for
broader stylistic exploration. This change does not generate nine near-duplicate
candidates or require descriptions in order to choose.

## Controlled musical difference

The two versions contain the same related four-bar phrase materials:

| Condition (kept outside the public review) | Four-bar phrase order |
|---|---|
| Alternating, shorter recurrence | A · B · A · B |
| Grouped, longer recurrence | A · A · B · B |

Both use the same four-bar harmonic cycle, i–VI–V7–i. This new common cycle
controls the comparison; it is not an exact replay of the earlier winning
recording. Phrase figures derive from that pilot's original A/answer materials.
Each version contains each phrase twice, over the same 16 bars. Three cycles
plus a tail make each recording 165 seconds. The caper and reflection passages,
seed, Romantic palette, production scene-expression input, mixer and output
limiter remain matched. The quieter reflection treatment is applied equally to
both versions.

Tests verify identical harmony at every bar and the same multiset of
phrase-local onset, MIDI pitch, duration, layer and level tuples. The caper
conditions each contain 94 attacks per cycle; the quiet conditions each contain
60. Bass/support events also match. The first phrase is identical; differences
begin after four bars (about 13 seconds).

The caper version's two quiet support attacks stay at the same absolute bars
in both conditions. Thus shorter recurrence describes the melodic phrase order;
the entire caper backing is not an exact eight-bar repeated waveform. This
keeps the backing fixed while changing the melody's placement above it.

Only ordering differs, but ordering necessarily changes local musical context,
repetition distance and the placement of melodic gestures. Attack positions at
every absolute time are not identical. These effects cannot be separated by
this experiment. Whole-clip RMS is matched by attenuation only; it is not a
perceptual loudness match. One listener, two selected passages, one seed/palette
and no reversed repeats make this a small personal comparison, not a population
study or a general form rule. Removing repeat trials is a deliberate reduction
in feedback burden; order-consistency evidence is not collected here.

## Reproduce and recover

```powershell
python tools/adventure_listening.py start --study form --max-new-renders 1
python tools/adventure_listening.py resume PRINTED_DIRECTORY
python -m http.server 8003 --bind 127.0.0.1 --directory PRINTED_DIRECTORY/public
python tools/choice_ratings.py PRINTED_DIRECTORY DOWNLOADED_CHOICES.json
```

Open `http://127.0.0.1:8003/review.html`. Serve only `public`. Each passage has a
fixed A/B assignment within its packet and a stable passage number. Labels are
assigned independently of condition names; named phrase materials above are
not the public candidate labels. The public folder excludes the treatment key.

The existing lab provides unique run/invocation IDs, immutable source and input
hashes, atomic artifacts, clip-level recovery, measured signal gates and paired
attenuation. Changed sources require a new run; earlier frozen review pages
remain playable with their audio even when their orchestration sources change.
`awen-choice-labels-1` exports contain packet identity, an anonymous local rater,
trial identity, choice and answer timestamp. They do not claim how much audio
was heard. Imports validate the packet and private-key hashes and preserve raw
choices plus a decoded summary in a fresh archive. This new format is separate
from the previous multi-axis recurrence ratings and conversational feedback.

## Validation and remaining work

The [engineering proof](form-comparison-proof.json) identifies the prepared
recordings and checks. Unit tests cover form controls, grammar, original-pilot
regressions, simple packet order, tie/neither, source-bound archival imports and
cached recovery. `tests/choice.browser.cjs` checks real clip playback, exclusive
audio, one-click choices, revision, clearing, download/restore, wrong-packet
rejection, keyboard activation and dark mobile layout in an isolated profile.
Automated answers are synthetic and excluded from real feedback.

No new listener choices or musical winner are recorded at preparation time.
No reward model, automatic default promotion, live MIDI arrangement path or
chapter-transition planner is introduced. Feedback can guide the next small
comparison; broader integration still needs continuity and device checks.
