"""Optional, pinned CLAP feature extraction. Imported lazily by score_embeddings.py."""
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path

PACKAGES = ("torch", "transformers", "numpy", "scipy", "huggingface-hub", "tokenizers", "safetensors")


def packages():
    try:
        return {name: importlib.metadata.version(name) for name in PACKAGES}
    except importlib.metadata.PackageNotFoundError as error:
        raise RuntimeError("Install the optional tools/clap-requirements.txt environment first") from error


def normalized(vector, dimension=512):
    result = [float(v) for v in vector]
    if len(result) != dimension or not all(math.isfinite(v) for v in result):
        raise ValueError("Invalid embedding shape/values")
    norm = math.sqrt(sum(v * v for v in result))
    if norm < 1e-12:
        raise ValueError("Zero embedding")
    return [v / norm for v in result]


class ClapBackend:
    def __init__(self, spec, model_cache, download=False):
        os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
        from huggingface_hub import snapshot_download
        import numpy as np
        import torch
        from transformers import ClapModel, ClapProcessor

        self.spec, self.np, self.torch = spec, np, torch
        prep = spec["preprocessing"]
        np.random.seed(prep["seed"])
        torch.manual_seed(prep["seed"])
        torch.set_num_threads(prep["threads"])
        torch.use_deterministic_algorithms(True)
        # Ordinary local files avoid requiring Windows symlink privileges.
        snapshot = Path(model_cache) / "snapshots" / spec["modelId"].replace("/", "--") / spec["revision"]
        if download:
            snapshot_download(repo_id=spec["modelId"], revision=spec["revision"],
                local_dir=str(snapshot), cache_dir=str(Path(model_cache) / "hub"), token=False,
                allow_patterns=[spec["weights"], "*.json", "merges.txt", "vocab.json", "README.md"])
        elif not (snapshot / spec["weights"]).is_file():
            raise RuntimeError("Pinned local checkpoint missing; run once with --download-model")
        weights = snapshot / spec["weights"]
        digest = hashlib.sha256()
        with weights.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        if weights.stat().st_size != spec["weightsBytes"] or digest.hexdigest() != spec["weightsSha256"]:
            raise ValueError("Pinned model weight checksum mismatch")
        processor_spec = json.loads((snapshot / "preprocessor_config.json").read_text(encoding="utf-8"))
        if processor_spec["sampling_rate"] != prep["targetSampleRate"] or processor_spec["chunk_length_s"] != prep["seconds"]:
            raise ValueError("Unexpected checkpoint preprocessing")
        self.processor = ClapProcessor.from_pretrained(snapshot, local_files_only=True)
        self.model = ClapModel.from_pretrained(snapshot, local_files_only=True,
                       use_safetensors=False, weights_only=True).to(device="cpu", dtype=torch.float32).eval()
        if self.model.config.projection_dim != spec["dimension"]:
            raise ValueError("Unexpected model projection dimension")

    def feature(self, kind, payload, pcm=None):
        torch, np, prep = self.torch, self.np, self.spec["preprocessing"]
        with torch.inference_mode():
            if kind == "text":
                tokens = self.processor.tokenizer(payload["text"], truncation=False)["input_ids"]
                if len(tokens) > prep["textMaxTokens"]:
                    raise ValueError("Brief exceeds the explicit token budget")
                inputs = self.processor.tokenizer(payload["text"], padding="max_length",
                         max_length=prep["textMaxTokens"], truncation=False, return_tensors="pt")
                feature = self.model.get_text_features(**inputs)
            elif kind == "audio":
                from scipy.signal import resample_poly
                source = np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32768.0
                if len(source) != prep["sourceSampleRate"] * prep["seconds"]:
                    raise ValueError("Audio window must be exactly ten seconds")
                audio = resample_poly(source, 2, 1, window=("kaiser", 5.0), padtype="constant").astype(np.float32)
                if len(audio) != prep["targetSampleRate"] * prep["seconds"]:
                    raise ValueError("Unexpected resampling length")
                inputs = self.processor.feature_extractor(audio, sampling_rate=prep["targetSampleRate"],
                          padding="repeatpad", truncation="rand_trunc", return_tensors="pt")
                feature = self.model.get_audio_features(**inputs)
            else:
                raise ValueError("Unknown feature kind")
        return normalized(feature[0].detach().cpu().float().tolist(), self.spec["dimension"])
