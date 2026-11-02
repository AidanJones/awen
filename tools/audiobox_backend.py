"""Pinned CPU Audiobox inference; four raw aesthetics axes, not reading comfort."""
import hashlib
import importlib.metadata
import math
import os
from pathlib import Path
import sys
import time
import wave

import score_lab as lab

PACKAGES = ['torch', 'torchaudio', 'numpy', 'safetensors', 'huggingface-hub']


def verify_files(root, spec):
    root = Path(root)
    for name, expected in spec['files'].items():
        file = lab.safe(root, name)
        if file.stat().st_size != expected['bytes']:
            raise ValueError('Wrong artifact size: ' + name)
        digest = hashlib.sha256()
        with file.open('rb') as stream:
            for block in iter(lambda: stream.read(8*1024*1024), b''):
                digest.update(block)
        if digest.hexdigest() != expected['sha256']:
            raise ValueError('Wrong artifact checksum: ' + name)


def weighted_axes(windows, axes):
    if not windows or any(not math.isfinite(w['weight']) or not 0 < w['weight'] <= 1 for w in windows):
        raise ValueError('Invalid window weights')
    for w in windows:
        if set(w['axes']) != set(axes) or any(not math.isfinite(v) for v in w['axes'].values()):
            raise ValueError('Invalid model axes')
    total = sum(w['weight'] for w in windows)
    return {a: sum(w['weight']*w['axes'][a] for w in windows)/total for a in axes}


class AudioboxBackend:
    def __init__(self, spec, root):
        begin = time.perf_counter()
        self.root, self.spec = Path(root).resolve(), spec
        verify_files(self.root, spec)
        packages = {p: importlib.metadata.version(p) for p in PACKAGES}
        if packages != spec['packages']:
            raise ValueError('Evaluator package identity differs from pinned environment')
        os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', HF_HUB_DISABLE_TELEMETRY='1')
        sys.path.insert(0, str(self.root / 'source/src'))
        import torch
        import torchaudio
        from safetensors.torch import load_file
        from audiobox_aesthetics.model.aes import AesMultiOutput
        self.torch, self.torchaudio = torch, torchaudio
        prep = spec['preprocessing']
        if prep != dict(device='cpu', precision='float32', threads=2, seed=0, sampleRate=16000,
            windowSeconds=10, hopSeconds=10, zeroPadLastWindow=True, weightByUnpaddedDuration=True,
            mono='channel mean', resample='torchaudio.functional.resample defaults', levelNormalization=False, windowBatchSize=1):
            raise ValueError('Unsupported preprocessing')
        torch.manual_seed(prep['seed'])
        torch.set_num_threads(prep['threads'])
        torch.use_deterministic_algorithms(True)
        config = lab.read(self.root / 'config.json')
        if config['precision'] != '32' or set(config['target_transform']) != set(spec['axes']):
            raise ValueError('Unexpected model config')
        self.model = AesMultiOutput(**config)
        result = self.model.load_state_dict(load_file(str(self.root / 'model/model.safetensors'), device='cpu'), strict=True)
        if result.missing_keys or result.unexpected_keys:
            raise ValueError('Non-strict model loading')
        self.model.to(device='cpu', dtype=torch.float32).eval()
        self.transforms = config['target_transform']
        self.identity = dict(spec=spec, packages=packages, backendSha256=lab.sha(Path(__file__).read_bytes()),
                             strictStateLoad=True, missingKeys=[], unexpectedKeys=[])
        self.load_seconds = time.perf_counter()-begin

    def read_pcm(self, file):
        with wave.open(str(file), 'rb') as stream:
            rate, channels, frames = stream.getframerate(), stream.getnchannels(), stream.getnframes()
            if stream.getsampwidth() != 2 or not 1 <= channels <= 8 or not 8000 <= rate <= 192000 or not 0 < frames/rate <= 64:
                raise ValueError('Expected bounded PCM16 audio')
            raw = bytearray(stream.readframes(frames))
        if len(raw) != frames*channels*2:
            raise ValueError('Truncated PCM')
        pcm = self.torch.frombuffer(raw, dtype=self.torch.int16).to(self.torch.float32).reshape(-1, channels).T / 32768
        return pcm, rate

    def score_pcm(self, pcm, rate):
        torch = self.torch
        begin = time.perf_counter()
        if pcm.ndim != 2 or not pcm.numel() or not torch.isfinite(pcm).all():
            raise ValueError('Invalid waveform tensor')
        # Match the official resample-then-channel-mean ordering; no loudness normalisation.
        pcm = self.torchaudio.functional.resample(pcm, orig_freq=rate, new_freq=16000).mean(dim=0, keepdim=True)
        windows = []
        with torch.inference_mode():
            for start in range(0, pcm.shape[-1], 160000):
                part = pcm[:, start:start+160000]
                length = part.shape[-1]
                wav = torch.nn.functional.pad(part, (0, 160000-length)).unsqueeze(0)
                mask = torch.zeros_like(wav, dtype=torch.bool)
                mask[:, :, :length] = True
                raw = self.model({'wav': wav, 'mask': mask})
                axes = {a: float(raw[a].item()*self.transforms[a]['std']+self.transforms[a]['mean']) for a in self.spec['axes']}
                windows.append(dict(startSeconds=start/16000, validSeconds=length/16000, weight=length/160000, axes=axes))
        return dict(axes=weighted_axes(windows, self.spec['axes']), windows=windows,
                    inferenceSeconds=time.perf_counter()-begin, levelNormalization=False,
                    readingComfortValidated=False, sceneConditioned=False)

    def score_file(self, file):
        pcm, rate = self.read_pcm(file)
        return self.score_pcm(pcm, rate)

    def official_equivalence(self, pcm, rate):
        """Smoke comparison against upstream predictor on one bounded window."""
        from audiobox_aesthetics.infer import AesPredictor
        from audiobox_aesthetics.model.aes import Normalize
        if pcm.shape[-1] > rate*10:
            raise ValueError('Equivalence check accepts at most ten seconds')
        predictor = object.__new__(AesPredictor)
        predictor.device, predictor.model = self.torch.device('cpu'), self.model
        predictor.sample_rate, predictor.data_col = 16000, 'path'
        predictor.target_transform = {a: Normalize(**t) for a, t in self.transforms.items()}
        official = predictor.forward([dict(path=pcm, sample_rate=rate)])[0]
        ours = self.score_pcm(pcm, rate)['axes']
        error = max(abs(official[a]-ours[a]) for a in ours)
        if error > 1e-5:
            raise ValueError('Upstream preprocessing/transform mismatch')
        return dict(official=official, adapter=ours, maxAbsoluteError=error, tolerance=1e-5)
