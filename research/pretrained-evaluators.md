# Pretrained evaluators: what we can actually reuse

Primary-source review and public artifact metadata checked 1 November 2026.
This is an inventory/preflight, not new model inference. The earlier
[prototype](multiobjective-roadmap.md) already documents native audio, actual
CLAP and synthetic-label test heads; those heads are not human preference models.

## Shortlist

| Candidate and source reviewed | Existing target / release | Awen role and limitation |
|---|---|---|
| [Meta Audiobox Aesthetics](https://github.com/facebookresearch/audiobox-aesthetics), README, model and inference code, package metadata, HF file metadata | Released four-axis predictor: content enjoyment/usefulness and production complexity/quality. CC BY 4.0 model metadata; bundled components have separate notices. | First audio-only baseline for generic appeal/production quality. Does not assess a supplied paragraph or reading distraction. Do not invert complexity into an annoyance reward. |
| [TuneJury](https://github.com/yonghyunk1m/TuneJury), README and [checkpoint guide](https://github.com/yonghyunk1m/TuneJury/blob/main/checkpoints/README.md) | Learned human-pair preference heads; full version uses specified CLAP-Music/MERT representations. Guide releases a separate Apache-2.0 audio-only head; other heads are CC BY-NC 4.0. | Candidate preference/scene-brief alternative after preflight. Audio-only variant cannot measure paragraph alignment. Matching feature dimension does not make our existing cached encoder compatible. The guide specifies a roughly 2.2 GB CLAP-Music encoder, even for a small head. |
| [MuQ-Eval A1](https://github.com/dgtql/MuQ-Eval), model card and released HF artifact metadata | Frozen MuQ-310M plus a learned quality head, trained on MusicEval expert ratings. Card specifies 24 kHz, ten-second input and MI/TA outputs; it explicitly notes audio-only limitations. | Candidate Musical Impression baseline. Its TA output is not alignment to our paragraph because the model does not consume that text. Our installed MuQ-MuLan retrieval model is not automatically its compatible encoder. Repository/HF MIT metadata does not replace an audit of upstream assets before reuse. |
| [SongEval](https://github.com/ASLP-lab/SongEval), README, inference and requirements | Trained song-aesthetic toolkit: coherence, musicality, memorability, structure and vocal naturalness. Intended for full songs with vocals; source includes a CPU path and MuQ dependency. CC BY-NC-SA 4.0 stated. | Possible later long-form comparison. Short instrumental excerpts do not exercise vocal/whole-song constructs. Source expects a local `ckpt/model.safetensors`; that artifact's independent download/checksum was not verified in this pass. |
| [Essentia models](https://essentia.upf.edu/models.html), official catalogue and example inference | Downloadable arousal/valence, approachability, engagement and other music heads with matching embedding models; MTG models list CC BY-NC-SA 4.0. | Useful intermediate descriptors for scene/texture targets, not “good music” or low distraction. Arousal can be appropriate during a chase. Audit platform/runtime requirements and each head/backbone pair before installation. |

These are different prediction tasks. Report them separately; a model trained
on ordinary generated songs may not rank sparse synthetic underscore usefully.
Author-reported benchmark correlations are not Awen measurements and should not
be compared across unrelated test sets to select a winner.

The [28 October MuQ-Eval v2 abstract](https://arxiv.org/abs/2603.22677v2)
reports selective sensitivity to signal artifacts but insensitivity to tested
musical-structural distortions. The inspected model card still lists degradation
sensitivity as untested. Record that source/revision discrepancy rather than
treating the card as a complete account of the newer paper; neither is an Awen
result. This also motivates a separate symbolic structural critic.

## A concrete first download candidate

Audiobox is the first M2 candidate because the official release provides all
four axes together and a tensor-input path. [Metadata](pretrained-model-metadata.json)
records the public repository revision, advertised file sizes and SHA256 values:

- Weights revision: `9b1dd8e5df9af7216e836a98974fe3b82c56ded6`.
- `model.safetensors`: 415,472,992 bytes (about 396 MiB), advertised SHA256
  `a5a3c2412649cc2384ec525ffd5180ce6c4778f43bed6108e0a1303de04d014e`.
- Source revision: `2618e9d451b456e9328b39495b5e6234678aa550`.
- Inspected inference code converts to 16 kHz mono and uses ten-second windows;
  source has a CPU selection path. CPU speed/memory and loading compatibility
  have **not** been measured locally. Upstream package metadata lists PyTorch,
  torchaudio and auxiliary dependencies; use a separate environment.

Those hashes were obtained from repository metadata. Weight bytes were not
downloaded or locally checksum-verified. Fetch only pinned config/source/weight
artifacts, verify bytes and strict state loading, disable unexpected secondary
downloads, then score a tiny subset of the existing WAVs before the full pilot.
Do not install into the CLAP/MuQ environments or invalidate their recovery paths.

MuQ-Eval's metadata separately advertises `model_state_dict.pt` at 1,336,614,308
bytes and another checkpoint container. We did not download either, inspect
their state dictionaries or establish whether extra backbone downloads would
be avoided. The preflight record distinguishes expected artifact identity from
completed local inference.

## Annoyance, pleasantness and what they do not tell us

There is relevant earlier work. [ARAUS](https://github.com/ntudsp/araus-dataset-baseline-models)
provides urban-soundscape data and baseline training code for affective responses.
Those stimuli concern environmental scenes/maskers, not instrumental support
for reading. Ready-to-run checkpoint availability was not established here.
This is evidence of prior learned pleasantness work, not a validated transferable
reading-annoyance model or a negative search result proving none exists.

[MoSQITo](https://github.com/Eomys/MoSQITo) provides signal-based sound-quality
tools. It is an algorithmic route, not a learned preference critic; physical
interpretations need appropriate signal/calibration assumptions. Neither a
production-quality score nor a soundscape pleasantness prediction establishes
personal reading comfort.

## Three complementary critic layers

1. **Symbolic rules:** inspect planned notes, harmony, rhythm and structure before
   audio is rendered. The [implemented symbolic critic](symbolic-critic.md) is
   cheap and explainable but cannot hear the synthesiser.
2. **Acoustic/perceptual feedback:** inspect actual WAVs using signal descriptors
   and one pretrained model. This can expose rendering/timbre problems that
   identical scores conceal.
3. **Narrative/personal calibration:** compare musical behaviour with an explicit
   text target and sparse listener feedback. The [dictionary backlog](narrative-dictionary-plan.md)
   keeps scene definitions and proposed musical mappings separate from taste.

Use the existing unique/resumable evaluator jobs and pinned caches. The first
model replacement should reuse the 27 verified prototype WAVs, not create a
large dataset or automatically change the reader. Generic enjoyment is a useful
candidate signal; reading comfort remains unvalidated until tested for that task.
