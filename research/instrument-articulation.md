# Instrument articulation and kinetic scoring

27 October 2026, `awen-ejv`. Listener feedback identified two problems in the nine-card explorer: the safe-drop paragraph felt more kinetic than its accompaniment, and the palettes sounded too similar.

## Diagnosis and implementation

The Rat passage already classifies as `chase` using the existing lexical/context rules. Raising that classification further would not fix the composition: most recipes had few action-specific changes, a 72 BPM clock and slow melody envelopes. Instrument names mostly selected different fixed periodic waves with similar attacks and a dark common low-pass filter. The shared sine bed further reduced contrast. No claim is made that the classifier understands the passage's comic irony.

Changes in `index.html` apply to the reader and newly generated exploration pages:

- **Plucked strings:** guitar, generic pluck and new pizzicato use an original, seeded fractional-delay string excitation. A triangular displacement plus pick noise circulates through a damped averaging loop; upper partials decay over time. Pizzicato damps faster and ends sooner. The final 25 ms fades to avoid hard buffer cuts. An instrument-level balance adjustment occurs before the shared compressor/master/limiter, never after it.
- **Winds:** flute/reed/whistle/brass have sustained envelopes, filtered breath and delayed small vibrato. Reed spectra emphasise odd harmonics. Whistle has much less breath than flute. Brass opens then closes a per-note filter. These are small procedural approximations, not acoustic recordings or a realism benchmark.
- **Bowed strings:** richer partials, a swelling envelope and gentle vibrato; short notes in the pursuit recipe give a repeated bowed articulation.
- **Felt/wood:** felt notes have a fast onset and exponential decay. Wooden accents use short deterministic noise plus a damped body tone. All auxiliary sources disconnect/stop with their owning voice.
- **Arrangement:** the global filter leaves more upper-partial contrast; the continuous bed recedes with smoothed density. Most non-dialogue recipes add restrained wooden accents in action and shorten lead articulation. The beat, harmonic form, motifs, scene dwell and bar-boundary transitions remain continuous. Quiet dialogue and background-led directions remain choices.
- **New recipes:** `pursuit` uses short bowed ostinatos and returning string figures; `pizzicato` uses dry plucked answers and comic bass motion. The grid offers **Driving strings** and **Clockwork caper** alongside warm ensemble, frontier guitar/whistle, desert brass/strings, chamber, space synth, background-led and noir. These recipes can be downloaded as profiles for the current reader. Its existing six-card starting gallery is unchanged.

The fixed tempo remains 72 BPM; the greater sense of motion comes from subdivisions and articulation. There is no phrase reset or paragraph-specific sound effect, no film/audio corpus, no new runtime dependency and no LLM. Material remains original procedural synthesis. A convincing sampled orchestra or guitar would be a separate choice about assets, licences, size and loading; this iteration does not claim to provide one.

## Versioning and earlier choices

Composer version is now `awen-score-3`. Existing seeded random decision streams keep their `awen-score-2` domain so the familiar Rat theme survives; planned action events/articulation and the renderer have changed. Incompatible composer checkpoints restart rather than silently continuing different musical behaviour. Numeric preferences and harmonic snapshots retain their existing schema.

Exploration fingerprints the complete production script. Its new page has a separate local-storage namespace and rejects older-engine backups. Keep the earlier generated page to access those choices and sounds. The generator's optional `--previous-url` adds an explicit link. The existing blinded calibration packet, native audio, private mapping and ratings remain intact and represent the earlier engine. Do not reinterpret those renders as version 3, silently reuse their feature hashes, or treat old listener choices as evidence about these new timbres. New-engine calibration needs new versioned renders when that work resumes.

## Verification and limits

`node tests/instruments.browser.cjs` renders eight isolated instruments at the same pitch/level through production routing in native `OfflineAudioContext`. It checks finite output, the unchanged 0.14 limiter, decays/releases, equal-energy signal differences and string pitch. Unique timestamp/UUID JSON proofs go under ignored `.score-lab/tests/instruments/`. No listener labels are generated.

In the completed isolated 220 Hz probe, guitar tail/early RMS was 0.204, pizzicato 0.000266 and felt 0.0759; sustained flute and bowed strings were about 1.29. The pluck autocorrelation estimate was 220.18 Hz. Equal-energy pairwise waveform distances exceeded 0.35 for tested guitar/flute, guitar/bow, flute/reed, felt/flute and bow/brass pairs. Waveform distance can reflect phase as well as timbre and is not a perceptual similarity metric. These tests expose the former shared-envelope problem but do not prove convincing acoustic identity or artistic fit.

Unit tests assert that the actual safe-drop paragraph is action, that action adds bounded rhythm across the relevant recipes, and that old checkpoints do not masquerade as current playback. Isolated Playwright checks additionally cover the nine-card renders, production audio/limiter stress, palette switching, evolution and storage/export. Human follow-up is still needed: listen to the kinetic cards against the passage, compare guitar/wind identity in context, and assess fatigue over longer reads. Richer evolving traits and perceptual calibration remain `awen-3fr.3`/`awen-3fr.6` work.
