# SSX Tricky music-system research

Checked 25 October 2026. This separates first-hand accounts, public reverse engineering and unverified details. No game binaries, music or proprietary code were downloaded or incorporated into Awen.

## Findings

**Tricky used deliberately prepared adaptive music.** In a 2011 interview, composer/remixer Rom Di Prisco credits John Morgan with music direction and describes contributing music, remixes and adaptive preparation. He explains that interactive music required different composition/arrangement and substantial testing. This is first-hand confirmation of an authored adaptive approach, not a public specification of the exact runtime. [Interview](https://www.squareenixmusic.com/features/interviews/romdiprisco.shtml).

**There is useful public code.** vgmstream's `src/meta/ea_schl_map_mpf_mus.c` identifies EA's PathFinder formats. Its MPF/MUS parser specifically labels version 3, subversions 1/2 as used by SSX Tricky and Sled Storm. It reads counts/tables for nodes, events, routers, variables, tracks and samples; its older MAP parser also documents segment-order information. This supports a data-driven segmented-music architecture. It does not reveal Tricky's complete gameplay-to-music rules, transition authoring, random selection policy or a public seed contract. It is decoder/parser code, not the original EA music runtime. [Actual source](https://github.com/vgmstream/vgmstream/blob/master/src/meta/ea_schl_map_mpf_mus.c).

**Fan-port reverse-engineering material also exists.** SSX-Tricky-PC publishes port/runtime work and engineering notes. Its notes describe a music manager, per-track loader, beat-grid configuration and a `PathfinderStream` allocation tag. These are the project's reverse-engineering findings, not original EA documentation, and have not been independently verified here against a game binary. The repository requires the user to supply their own disc and says it does not distribute game code/data. OpenTricky is a continuation, likewise requiring game assets. These are research leads, not drop-in web music engines. [Original project](https://github.com/MatiasRiveraC/SSX-Tricky-PC), [engineering index](https://github.com/MatiasRiveraC/SSX-Tricky-PC/blob/main/docs/notes/RE_NOTES_INDEX.md), [OpenTricky](https://github.com/GiZcesi/OpenTricky).

**Do not confuse Tricky with later SSX.** The 2013 GDC session by EA's Gordon Durity concerns the then-latest SSX and remixing user-provided tracks. A March 2012 interview describes Path Finder's history and the later music/stem workflow. Those accounts are informative but do not establish that the 2001 game had the same custom-track remix system. [GDC session listing](https://www.gdcvault.com/play/1017729/Contextually-Driven-Interactive-Music-in), [2012 interview with Durity](https://digital.copcomm.com/i/57245-march-2012/51). The GDC site can redirect to maintenance; the session description was available in search results, not a watched presentation.

## What remains unverified

- I did not find an official public release of Tricky's EA PathFinder runtime or its original authoring tools. This is a search result, not proof that no archive exists.
- A format parser is insufficient to reconstruct the original game's musical behaviour by itself.
- I have not established an exact stem layout, bar-boundary policy, transition matrix, PRNG or user-visible seed mechanism for Tricky.
- Some community tools advertise music editing for **SSX 3**, which should not be presented as confirmed Tricky support. [Example tool's stated scope](https://github.com/GlitcherOG/SSX-PS2-Collection-Modder).

## Application to Awen

The useful principle is a stable authored musical identity with event-driven arrangement and transitions. For Awen, replace prerecorded segments with our own reusable symbolic phrases, harmonic forms and instrument layers. Keep the musical transport running; let narrative activity adjust layers and expression, and make structural changes at musical boundaries.

The proposed seed is an Awen feature for repeatability, not a claim about how Tricky worked. It should select variations of an original composition rather than imitate or reuse the game's songs. This research strengthens the persistent-composer design in `continuous_score_review.md`; it does not justify cloning EA's runtime or copying soundtrack material.
