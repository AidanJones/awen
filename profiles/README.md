# Listening profiles

`personal.json` is a neutral starter profile. Use **Shape your soundtrack → Save profile to file** and choose this file to save your listening choices into the repo. Save again after later choices; browser storage updates independently. Use **Import profile** to restore it on another browser/device.

Browsers without file-picker writes download a JSON copy instead; move it here. Additional listeners can use separate filenames. The app uses one active profile per browser origin, across all books. It does not automatically load these files.

Pinned favourites can now be named in the gallery. Names, the current genome and up to 80 kept decisions are exported together; older version-1 profiles still import with empty optional names/metadata. The latest five choices are summarised in the UI.

The browser shows whether your current choices match the last successful file write or import. This checkpoint is local browser metadata and is not embedded in the portable profile. Cancelled/failed writes leave it unchanged, and it cannot detect later edits/deletion of a disk file. Downloads are requests, not verified repo saves. Use **Download JSON copy** if the file picker is unavailable or fails.

Original musical starting points use an optional `scoreStyle` field alongside the six numeric traits. A pin/name includes this identity. Older files without the field default to Connected ensemble and old name keys migrate; save the updated profile file after importing it.

**Explore chords & direction** can add a compiled `harmony` snapshot to a genome. It includes engine/library version, genre, scene function, family, tonic, chord pitches, form and change rate. Compatible archived snapshots retain their saved pitches even when the current library differs. Invalid or unsupported engines fail import before replacing the active profile. Names and pins include harmonic identity; profile hashes and score checkpoints distinguish these choices. Clear/undo/import are supported. Old profiles without `harmony` still use their authored starting point.
