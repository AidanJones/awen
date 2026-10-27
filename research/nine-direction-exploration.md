# Nine-direction personal exploration

Implemented for `awen-w3k`, 27 October 2026. This is a wider personal search interface alongside the blinded calibration review. It does not change the reader's current profile or consume its A/B labels.

Generate a portable page with the standard Python library:

```sh
python tools/exploration_page.py
# Optional: --output <new-directory> --paired-url http://127.0.0.1:50473/review.html
# --previous-url <earlier-explorer-url> keeps older sounds/backups accessible
```

Open the printed `explore.html` directly, or serve its directory locally. It embeds the production engine, harmonic library and six pilot passages in one HTML file; it needs no network, model, CDN or build tooling to run. The generator refuses to overwrite a directory and emits a manifest with page/engine hashes. Regenerate after engine changes; backups from a different engine hash are rejected rather than silently replayed differently. The main reader remains `index.html`.

## Starting grid and refinement

The desktop grid is 3 × 3 (two columns on tablets, one on phones). The updated nine starting cards cover six authored phrase recipes, six sound palettes and nine distinct recipe/harmony identities:

| Direction | Phrase recipe / palette | Harmony |
| --- | --- | --- |
| Warm ensemble | Classic / ensemble | Original authored form |
| Open frontier | Frontier / frontier | Open modal space |
| Desert horizon | Frontier / desert | Held-root suspension |
| Intimate chamber | Dialogue / chamber | Gentle release |
| Clockwork caper | Pizzicato / ensemble | Minor-sixth intrigue |
| Suspended space | Dialogue / synth | Major-third colour |
| Driving strings | Pursuit / ensemble | Minor driving cycle |
| Background led | Dialogue / ensemble, no lead | Warm added-note continuity |
| Noir caper | Caper / noir | Minor-sixth intrigue |

These combine existing original synthesised material; they are not recordings or imitations of named film composers. Background led removes lead melody but retains sparse bass and the continuous bed. Each direction also varies numeric traits. Broad structural choices are deliberately authored rather than hoping small random mutations produce a different genre.

Listen, mark up to three cards as promising, then **Explore selected directions**. The next nine-card round retains each selected parent unchanged and fills the remaining cards with deterministic mutations distributed across those parents. A child changes two bounded numeric traits and retains its parent's palette, phrase recipe and harmony. Parents are not averaged together. The original ensemble is always available through **Return to nine starting points**. Previous round restores earlier choices; exploring again branches and replaces later rounds. Backups retain up to 40 rounds. This bounded search is intentionally modest; it introduces no learned reward or automatic assertion that a child is better.

Seed and passage apply equally to all nine cards. Playback renders a fresh excerpt from the start of the same seeded composition, not a resume of the live reader's playback cursor. Changing passage can change performance. Excerpts of 32/64 seconds allow phrase repetition and dialogue gaps to be heard. Listen across several passages before adopting a favourite.

## Playback and data

Audio is rendered on demand using the exact production `AudioAdapter` in a native 24 kHz `OfflineAudioContext`, with the shared production compressor, master and final 0.14 sample limiter intact. After cropping the first second and applying 200 ms edge fades, per-card RMS is attenuated toward 0.018; quiet cards are never amplified. Playback volume is another attenuation-only gain. This is not equal perceived loudness or physical speaker/hearing protection. One live buffer can play at a time; Stop, Escape, passage changes and hiding the tab cancel pending playback. Rendering is serialised and a 12-buffer LRU bounds memory. There is no autoplay or external request. The waveform uses the actual post-volume signal.

Selections and settings persist under `awen.exploration.1.<engine-hash>`. **Export exploration backup** gives a unique timestamp/UUID JSON download with full rounds and musical snapshots; restore validates version, engine hash, bounds and shape before replacing state. Storage failures leave export available. Downloads do not write directly into Git. Save a real exported backup into a chosen repo folder if you want it versioned; no listener choices have been fabricated or committed.

Each card also downloads an existing reader-compatible preference profile. Import it using the reader's profile controls, then manually select the card's named **Sound palette**: the current reader profile format stores musical traits/harmony but not the active palette. Exploration JSON is a separate format and cannot be imported as calibration labels or a reader profile.

This is preference exploration, not a calibrated listening experiment. “Promising” is not a fit/comfort judgement. Named cards, self-selected comparisons, transient preview levels and familiarity can bias choices. Use the existing blinded paired tool for independent fit, enjoyment and distraction labels. No exploration choices currently train CLAP or an automatic reward.

## Verification and remaining work

```sh
python -m unittest discover -s tests -p 'test_exploration_page.py'
# Isolated Playwright, installed only in the development environment:
# AWEN_EXPLORATION_PAGE=<generated explore.html>; AWEN_BROWSER_CHANNEL=msedge
node tests/exploration.browser.cjs
```

The isolated native-audio proof renders all nine starting directions for one Rat passage/seed and checks different waveform hashes, non-silent output, RMS at or below 0.018 and peaks below 0.14. It verifies six phrase recipes/six palettes/nine harmonic identities, readable dark/mobile UI, no autoplay/network, single-source playback, Stop during rendering, deterministic multi-parent refinement, reader-profile compatibility, reload and validated export/restore. These checks establish working audio and interaction, not perceptual distinctness or musical quality. The production audio and evolution regression suites also run separately. See [instrument and kinetic-scoring changes](instrument-articulation.md) for the second listening iteration.

Next listening work: judge whether the broad directions are sufficiently different and comfortable over a longer read, identify useful extra composition traits beyond the current six, and decide how explicit taste/fit/comfort feedback should be archived. The broad starting grid does not establish a reliable evolution reward; the calibration roadmap and held-out evaluation gates still apply.
