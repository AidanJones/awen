# External synthesizer output: M-VAVE FM1 / Web MIDI

Implemented 4 November 2026, task `awen-tl6`. The single-file reader can send its
continuous score to a selected MIDI synthesizer. Native browser audio remains
available, with its existing shared final limiter. MIDI is an optional local
browser API; no dependency, backend, model or build is required.

## FM1 setup

1. Connect the FM1 to the computer using a USB **data** cable and power it on.
2. Open Awen in Edge or Chrome using localhost or HTTPS. The browser may request
   MIDI permission. Browser/OS support varies; the panel reports unavailable or
   denied access without affecting browser playback.
3. Open **External synthesizer · FM1 / MIDI** below Start soundtrack. Click
   **Find MIDI devices**, grant permission, and select the FM1 MIDI output from
   the list. Port names depend on the installed driver/firmware.
4. Choose a patch on the FM1 and match its receive channel to Awen's channel.
   Start with channel 1; adjust it to the instrument's actual configuration.
   A polyphonic, sustained patch is a useful starting point for ambient harmony.
5. Set the FM1's physical volume low, click **Enable MIDI output**, then use
   **Test MIDI note**. This sends middle C for 0.7 seconds at the current Awen
   volume/velocity limit. Listen through the FM1's speaker, headphones or its
   connected audio system.
6. Click **Start soundtrack**. The default MIDI part is **Ambient harmony**.
   Choose **Harmony & score notes** for the fuller arrangement, or **Score notes
   only** to omit the sustained bed. **Also hear the browser synthesizer** enables
   browser monitoring alongside the hardware.

The FM1 generates the audio. Awen sends note messages, not an audio stream, and
does not capture or meter the FM1's output. The visualizer continues to measure
browser audio; in hardware-only mode the signal label explains that external
audio is not metered. Awen's sound palette controls its browser instruments;
the selected FM1 patch supplies the hardware timbre. All parts currently share
one selected channel/patch. Firmware-specific multitimbral mapping is future work.
Browser-specific filtering, reverb and instrumental envelopes are not translated
into FM1 parameter changes. Preference traits that alter pitches, timing and note
selection affect the MIDI score; timbral traits still depend on the hardware patch.

The FM1 manufacturer lists USB-C, BLE and MIDI input. Its official open-firmware
README documents MIDI receive-channel configuration, but that firmware differs
from stock releases. This implementation uses ordinary channel note messages
and does not depend on installing that firmware. USB is the initial documented
connection. Bluetooth/TRS depend on the OS exposing an appropriate MIDI output
and have not been physically tested here.

## Level and stop controls

Maximum velocity defaults to **56/127** and is adjustable from 8 to a hard ceiling
of **80**. The main volume and layer settings scale note velocity; zero volume
immediately clears queued and held MIDI notes. The background slider and Chords
layer control sustained harmony. Changes to those controls release existing
notes before the next score step applies the new levels.

Velocity is a performance parameter, not an acoustic limiter. Some patches react
strongly to it or ignore it. The browser's 0.14 sample ceiling only limits audio
generated inside the browser. The FM1's own volume and downstream amplification
determine its physical output level.

Pause, Mute now, Escape, **Stop all MIDI notes**, score/book reset and page exit
clear the MIDI queue and release owned notes. Panic also sends sustain-off,
All Notes Off and All Sound Off on the selected channel. This may stop other
performances sharing that device/channel. Device/channel/part/monitor settings
pause playback and disarm MIDI before changing routing; enable it again to resume.

Hiding the page pauses playback and releases MIDI notes to avoid relying on
background timer scheduling. Returning to it requires Start. Audio-context
interruption releases MIDI notes. Disconnection or a send failure stops playback;
reconnection requires explicit selection/enabling. Browser or computer crashes,
a lost cable and hardware that ignores stop messages cannot guarantee a note-off:
use the FM1's controls if a note remains held.

## Integration and timing

The native `planStep` composer remains the sole musical clock and harmony source.
After its normal activity/mix filtering, `AudioAdapter.composeBeat` fans the
performed events and current four-voice harmony into `MidiScoreOutput`. Score
seeds, paragraph detection, scene dwell, chapter transitions, DSL, personal
preferences and saved musical position therefore drive the same plan. There is
no independent MIDI composition loop or paragraph reset.

Web Audio times are converted to `performance.now()` timestamps. A bounded
20 ms pump submits messages within a 25 ms window using Web MIDI timestamps.
Late starts older than 250 ms are discarded. Each pitch has owned note tokens;
overlapping identical pitches share the held key, and only the last token's
release sends Note Off. This avoids a previous note-off cutting a later note.
It deliberately favours legato over re-articulation for overlaps.

Harmony preserves common pitches and releases changed ones. Held background
notes have a renewable 1.5-second lease; absent score updates let them release.
The software limits simultaneous unique pitches to eight, restricts transmitted
pitches to MIDI 36–84, bounds durations to four seconds per lease/note and bounds
the event queue. These are implementation limits, not claims about FM1 polyphony.
No program/bank changes, MIDI clock/transport or SysEx are sent. MIDI access asks
for `sysex:false` and does not open MIDI inputs.

The browser master is attenuated before its existing limiter when hardware-only
output is enabled. Every browser sound still passes through that limiter.
**Gallery previews and Check sound use browser audio**; gallery entry releases
hardware notes and suppresses MIDI until return. Offline measurement and
development render adapters never attach a MIDI sink, so rendering cannot send
hardware notes or reinterpret browser RMS balancing as hardware balancing.

Channel, parts, velocity cap and browser-monitor preference are stored in
`awen.midi.v1`. Device access, selected port and enabled state are session-only.
Reload never requests MIDI permission or enables hardware playback automatically.
The existing reader/profile format and composer checkpoint version remain intact.

## Evidence and remaining hardware acceptance

See the [engineering proof](midi-output-proof.json). Unit tests use recorded fake
ports and deterministic time; isolated Playwright combines real browser Web Audio
with a simulated FM1 port. Tests cover notes/off timing, overlaps, bounded output,
common-tone leases, mute, panic, cancellation, disconnection, reload, permission
failure, MIDI-only/monitor modes and gallery isolation. Existing native audio and
evolution regressions must also pass. These checks establish message behaviour,
not physical FM1 compatibility, patch quality, acoustic volume or latency.

Physical acceptance remains open: confirm the actual port name and receive
channel, a suitable sustained patch, volume response, polyphony, a longer reading
session, cable removal and stop behaviour on the user's installed firmware.

```powershell
node --test tests/mvp.test.cjs tests/midi.test.cjs
# Set NODE_PATH to an isolated Playwright installation if needed.
$env:AWEN_BROWSER_CHANNEL='msedge'
node tests/midi.browser.cjs
node tests/audio.browser.cjs
node tests/evolution.browser.cjs
```

## Primary references checked 4 November 2026

- [M-VAVE FM1 product page](https://www.m-vave.com/product?id=fm-1): manufacturer
  connection information. The rendered page is dynamic; the indexed product
  description lists USB-C, BLE and MIDI input.
- [M-VAVE official open firmware README](https://github.com/m-vave/fm1_open):
  MIDI ports and configurable track receive channels for that firmware; not a
  statement that every stock firmware has the same track mapping.
- [Web MIDI specification](https://webaudio.github.io/web-midi-api/): access,
  selected output ports, timestamped `send`, `clear` and port state changes.
- [MDN Web MIDI API](https://developer.mozilla.org/en-US/docs/Web/API/Web_MIDI_API):
  secure-context and permission requirements and browser availability guidance.
