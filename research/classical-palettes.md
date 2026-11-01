# Classical sound palettes

Added 31 October 2026. Four entries now appear directly in the reader's **Sound palette** dropdown. All use original procedural synthesis, with no recordings, downloads or runtime model.

| Palette | Bass / chords / melody / pulse | Suggested starting points |
|---|---|---|
| Baroque · harpsichord & strings | Harpsichord / bowed strings / harpsichord / pizzicato | Minor cycle, winter pulse, concertino |
| Cello · bowed chamber | Bowed bass / muted strings / bowed lead / wooden accent | Flowing line, storm motion, winter shelter |
| Romantic · piano & strings | Rounded bass / bowed strings / felt piano / felt accent | Quiet elegy, dialogue gaps |
| Pastoral · flute & strings | Rounded bass / muted strings / flute / wooden accent | Spring calls |

These are instrumental combinations, independent of the compositional starting point. Selecting one keeps the current score position and audio graph. A palette can reinterpret any existing recipe, including authored scores, DSL figures and chapter development. The starting-point description recommends a palette; applying that recipe keeps your current palette choice. Newly generated **Classical-inspired nine** explorer cards use matching palettes from this table. Older generated pages keep their original embedded audio.

The palette selection is a browser setting, separate from the reader profile.
After importing a grid card's profile, manually select the card's named palette.
An exploration backup preserves its own cards and palettes. Regenerate the
explorer after code changes; an older generated page retains its older dropdown
and renderer. [Reproduction commands](README.md#reproduce-the-current-engineering-checks)
cover the generator and isolated browser checks.

The harpsichord uses the existing fractional-delay plucked-string method with a different decay and a quiet octave rank. It is a stylised keyboard colour rather than an acoustic instrument model. Layer-specific palette routing lets its plucked bass/lead coexist with bowed chords; the other new palettes likewise give each layer a defined instrument. The check tone bypasses those instrument substitutions. Existing palettes retain their previous mappings.

The two plucked components are mixed at 65% fundamental rank and 35% octave
rank, with damping 0.993 and 0.996 respectively. The harpsichord's per-note filter
moves from 8.5 kHz toward 2.4 kHz before the shared graph. Layer maps apply to
scheduled note voices; the continuous bed keeps its shared oscillator graph,
with palette cutoff/room and the existing mix controls shaping its colour.

All notes continue through the shared filter, compressor, master and final sample limiter. Palette changes do not raise the output ceiling. Digital bounds do not determine loudness at arbitrary device settings. The developmental renderers record the actual layer-specific timbre in event traces, so evaluation metadata matches playback.

Validation: the palette unit test checks all four layer maps and the unchanged check tone. `tests/classical-palettes.browser.cjs` checks native output for the same 32-second figure in all four palettes, exact all-layer-muted silence, overloaded harpsichord limiting, guitar/harpsichord signal difference at matched energy, live switching, reload without autoplay, recommendations, grid playback and mobile width. Existing audio, evolution and western/palette suites cover continuity, previews, persistence and dropdown contrast. These checks do not establish instrumental realism or artistic quality; listening is still needed.

The [engineering proof](classical-palettes-proof.json) records those native
measurements and the reader source hash. Feedback is test-only, with zero
listener ratings.
