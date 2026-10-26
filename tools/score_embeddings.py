"""Tiny resumable CLAP diagnostics over already-rendered Awen audio, never a quality judge."""
from __future__ import annotations

import argparse
import contextlib
import json
import math
from pathlib import Path
import re
import sys
import uuid
import wave

import score_lab as lab
from clap_backend import ClapBackend, packages

VERSION = "awen-embedding-probe-1"
ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "research/clap-probe-model.json"
SUITE = ROOT / "research/clap-probe-suite.json"
SOURCES = ["tools/score_embeddings.py", "tools/clap_backend.py", "tools/score_lab.py",
           "research/clap-probe-model.json", "research/clap-probe-suite.json"]


def source_hashes():
    return {name: lab.sha((ROOT / name).read_bytes()) for name in SOURCES}


def model_identity(spec):
    return {"spec": spec, "packages": packages(),
            "backendSha256": lab.sha((ROOT / "tools/clap_backend.py").read_bytes())}


def vector_valid(result, key, identity, dimension):
    if result.get("version") != VERSION or result.get("cacheKey") != key or result.get("identity") != identity:
        raise ValueError("Embedding cache identity mismatch")
    values = result.get("vector", [])
    if len(values) != dimension or not all(isinstance(v, (int, float)) and not isinstance(v, bool)
                                          and math.isfinite(v) for v in values):
        raise ValueError("Invalid cached embedding")
    if abs(sum(v * v for v in values) - 1) > 1e-4:
        raise ValueError("Embedding must have unit L2 norm")
    if lab.sha(lab.encode(values)) != result.get("vectorSha256"):
        raise ValueError("Embedding vector checksum mismatch")
    return result


def pcm_window(directory, feature, spec):
    file = lab.safe(directory, feature["file"])
    if lab.sha(file.read_bytes()) != feature["wavSha256"]:
        raise ValueError("Source WAV checksum mismatch")
    with wave.open(str(file), "rb") as audio:
        if (audio.getnchannels(), audio.getsampwidth(), audio.getframerate(), audio.getcomptype()) != (
                1, 2, spec["preprocessing"]["sourceSampleRate"], "NONE"):
            raise ValueError("Expected native mono 24 kHz PCM16 WAV")
        start, count = feature["startFrame"], feature["frameCount"]
        if not isinstance(start, int) or start < 0 or count != 240000 or start + count > audio.getnframes():
            raise ValueError("Invalid ten-second audio window")
        audio.setpos(start)
        pcm = audio.readframes(count)
    if feature["silence"]:
        pcm = bytes(count * 2)
    if len(pcm) != count * 2 or lab.sha(pcm) != feature["pcmSha256"]:
        raise ValueError("Audio window checksum mismatch")
    return pcm


def feature_key(identity, feature):
    data = {"textSha256": feature["textSha256"]} if feature["kind"] == "text" else {
           "pcmSha256": feature["pcmSha256"], "sampleRate": 24000, "frameCount": feature["frameCount"]}
    return lab.sha(lab.encode({"identity": identity, "kind": feature["kind"], "data": data}))


def create(root, run_path, audio_root, *, max_candidates=2, cache=None, model_cache=None):
    spec, suite = lab.read(SPEC), lab.read(SUITE)
    identity = model_identity(spec)
    run_path, audio_root = Path(run_path).resolve(), Path(audio_root).resolve()
    raw = run_path.read_bytes()
    run = json.loads(raw)
    if run.get("version") != "awen-score-lab-1" or not 1 <= max_candidates <= 4:
        raise ValueError("Expected score-lab run and 1..4 candidates")
    candidates = [c for c in run["candidates"] if c["eligible"]][:max_candidates]
    if not candidates or len({c["id"] for c in candidates}) != len(candidates):
        raise ValueError("No distinct eligible candidates")
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    directory = root / (lab.stamp() + "-" + uuid.uuid4().hex)
    directory.mkdir()
    features, texts, rows, assets = [], [], [], {}
    sanity = []
    for text in spec["textTowerSanity"]["texts"]:
        item = {"kind": "text", "text": text, "textSha256": lab.sha(text.encode("utf-8"))}
        item["cacheKey"] = feature_key(identity, item)
        features.append(item)
        sanity.append(item["cacheKey"])
    for probe in suite["probes"]:
        for role in ("brief", "paraphrase"):
            text = probe[role]
            item = {"kind": "text", "text": text, "textSha256": lab.sha(text.encode("utf-8"))}
            item["cacheKey"] = feature_key(identity, item)
            features.append(item)
            texts.append({"id": probe["id"] + "/" + role, "cacheKey": item["cacheKey"]})
    for negative in suite["unsuitable"]:
        item = {"kind": "text", "text": negative["text"], "textSha256": lab.sha(negative["text"].encode("utf-8"))}
        item["cacheKey"] = feature_key(identity, item)
        features.append(item)
        texts.append({"id": "unsuitable/" + negative["id"], "cacheKey": item["cacheKey"]})
    for candidate in candidates:
        for probe in suite["probes"]:
            fixture = next(c for c in run["cases"] if c["id"] == probe["caseId"])
            passage_index = next(i for i, p in enumerate(fixture["timeline"]) if p["paragraphId"] == probe["paragraphId"])
            passage = fixture["timeline"][passage_index]
            following = fixture["timeline"][passage_index + 1]["seconds"] if passage_index + 1 < len(fixture["timeline"]) else float("inf")
            start = probe["startSeconds"]
            if start < passage["seconds"] or start + 10 > following + 1 / 24000:
                raise ValueError("Probe crosses the declared passage interval")
            clip = next(c for c in candidate["clips"] if c["caseId"] == probe["caseId"])
            source = lab.safe(audio_root, clip["file"])
            data = source.read_bytes()
            if lab.sha(data) != clip["sha256"]:
                raise ValueError("Input run's audio hash mismatch")
            asset = "assets/" + clip["sha256"] + ".wav"
            lab.atomic(directory / asset, data, exclusive=True)
            assets[asset] = clip["sha256"]
            with wave.open(str(directory / asset), "rb") as audio:
                if (audio.getnchannels(), audio.getsampwidth(), audio.getframerate()) != (1, 2, 24000):
                    raise ValueError("Unsupported source audio format")
                audio.setpos(round(start * 24000))
                pcm = audio.readframes(240000)
            if len(pcm) != 480000:
                raise ValueError("Source clip too short")
            item = {"kind": "audio", "file": asset, "wavSha256": clip["sha256"],
                    "startFrame": round(start * 24000), "frameCount": 240000,
                    "silence": False, "pcmSha256": lab.sha(pcm)}
            item["cacheKey"] = feature_key(identity, item)
            features.append(item)
            rows.append({"id": candidate["id"] + "/" + probe["id"], "candidate": candidate["id"],
                         "probe": probe["id"], "paragraphId": probe["paragraphId"],
                         "startSeconds": start, "endSeconds": start + 10,
                         "cacheKey": item["cacheKey"], "sourceWavSha256": clip["sha256"]})
    silence = {**next(f for f in features if f["kind"] == "audio"), "silence": True,
               "pcmSha256": lab.sha(bytes(480000))}
    silence["cacheKey"] = feature_key(identity, silence)
    features.append(silence)
    manifest = {"version": VERSION, "id": uuid.uuid4().hex, "createdAt": lab.now(),
        "sources": source_hashes(), "identity": identity, "identitySha256": lab.sha(lab.encode(identity)),
        "suite": suite, "sourceRun": {"path": str(run_path), "sha256": lab.sha(raw), "runId": run["id"]},
        "assets": assets, "features": list({f["cacheKey"]: f for f in features}.values()),
        "texts": texts, "rows": rows, "silenceKey": silence["cacheKey"], "sanityKeys": sanity,
        "cache": str(Path(cache or ROOT / ".score-lab/embedding-cache").resolve()),
        "modelCache": str(Path(model_cache or ROOT / ".score-lab/huggingface").resolve())}
    lab.atomic(directory / "source-run.json", raw, exclusive=True)
    manifest_bytes = lab.encode(manifest)
    lab.atomic(directory / "experiment.json", manifest_bytes, exclusive=True)
    lab.atomic(directory / "state.json", lab.encode({"version": VERSION, "status": "created", "jobs": {},
               "manifestSha256": lab.sha(manifest_bytes),
               "renderer": None, "judgeIdentity": None, "judgeCallsStarted": 0,
               "computedFeatures": 0, "featureCacheHits": 0}))
    return directory


def cosine(a, b):
    if len(a) != len(b) or not a:
        raise ValueError("Mismatched embedding dimensions")
    return sum(x * y for x, y in zip(a, b))


def text_tower_sanity(vectors, threshold):
    if len(vectors) < 3:
        raise ValueError("At least three unrelated text controls required")
    similarities = [cosine(a, b) for i, a in enumerate(vectors) for b in vectors[i + 1:]]
    return {"usable": min(similarities) <= threshold, "pairwiseCosines": similarities,
            "rejectThreshold": threshold, "meaning": "Extreme-collapse check only; not semantic validation."}


def diagnostics(manifest, vectors):
    texts = {t["id"]: vectors[t["cacheKey"]] for t in manifest["texts"]}
    probes = manifest["suite"]["probes"]
    if len(probes) != 2:
        raise ValueError("This preregistered shuffle expects exactly two scene briefs")
    rows = []
    for row in manifest["rows"]:
        vector = vectors[row["cacheKey"]]
        other = next(p["id"] for p in probes if p["id"] != row["probe"])
        scores = {key: cosine(vector, text) for key, text in texts.items()}
        matched, shuffled = scores[row["probe"] + "/brief"], scores[other + "/brief"]
        margin = matched - shuffled
        paraphrase_margin = scores[row["probe"] + "/paraphrase"] - scores[other + "/paraphrase"]
        unsuitable = max(value for key, value in scores.items() if key.startswith("unsuitable/"))
        rows.append({**row, "scores": scores, "matched": matched, "shuffled": shuffled,
                     "margin": margin, "paraphraseMargin": paraphrase_margin,
                     "wordingSignChanged": (margin > 0) != (paraphrase_margin > 0),
                     "matchedAboveUnsuitable": matched > unsuitable})
    silence = {key: cosine(vectors[manifest["silenceKey"]], vector) for key, vector in texts.items()}
    matrix_values = [s for row in rows for s in row["scores"].values()]
    return {"version": VERSION, "status": "diagnostic-only", "experimentId": manifest["id"],
        "identity": manifest["identity"], "suiteId": manifest["suite"]["id"], "rows": rows,
        "summary": {"audioExamples": len(rows), "matchedPreferred": sum(r["margin"] > 0 for r in rows),
                    "meanMatchedMinusShuffled": sum(r["margin"] for r in rows) / len(rows),
                    "matchedAboveUnsuitable": sum(r["matchedAboveUnsuitable"] for r in rows),
                    "wordingSignChanges": sum(r["wordingSignChanged"] for r in rows),
                    "constantScoreMatrix": max(matrix_values) - min(matrix_values) < 1e-6},
        "silenceScores": silence,
        "silenceBeatsMatchedMusic": [r["id"] for r in rows if silence[r["probe"] + "/brief"] > r["matched"]],
        "musicalWinner": None, "trainingPerformed": False, "qualityOrReadingBenefitEstablished": False,
        "limitations": manifest["suite"]["limitations"] + [
            "Same-book windows and alternate renderings are not independent observations.",
            "No statistical significance or calibrated reward is inferred from this smoke test."]}


class EmbeddingEngine(lab.Engine):
    """Reuse the existing atomic job journal; replace native/provider execution with local features."""
    def __init__(self, directory, log, *, max_new=None, download=False, backend_factory=ClapBackend, fault_hook=None):
        self.directory = Path(directory).resolve()
        self.manifest, self.state = lab.read(self.directory / "experiment.json"), lab.read(self.directory / "state.json")
        if self.manifest["version"] != VERSION or self.state["version"] != VERSION:
            raise ValueError("Unsupported embedding experiment")
        if self.state.get("manifestSha256") != lab.sha((self.directory / "experiment.json").read_bytes()):
            raise ValueError("Pinned embedding manifest changed")
        if self.manifest["identitySha256"] != lab.sha(lab.encode(self.manifest["identity"])):
            raise ValueError("Invalid embedding identity checksum")
        if self.manifest["sources"] != source_hashes() or self.manifest["identity"] != model_identity(self.manifest["identity"]["spec"]):
            raise ValueError("Embedding source/package identity changed; start a new experiment")
        self.log, self.retry = log, set()
        self.max_new_renders, self.new_renders = None, 0
        self.max_new, self.download, self.factory = max_new, download, backend_factory
        self.backend, self.new_features = None, 0
        self.fault_hook = fault_hook or (lambda *_: None)

    def cache_path(self, payload):
        if not re.fullmatch(r"[0-9a-f]{64}", payload["cacheKey"]):
            raise ValueError("Invalid feature cache key")
        return Path(self.manifest["cache"]) / self.manifest["identitySha256"] / payload["cacheKey"] / "vector.json"

    def verify(self, job, result_path):
        result = super().verify(job, result_path)
        payload = lab.read(lab.safe(self.directory, job["input"]))
        return vector_valid(result, payload["cacheKey"], self.manifest["identitySha256"],
                            self.manifest["identity"]["spec"]["dimension"])

    def execute(self, kind, payload):
        _, job = self.ensure_job(kind, payload)
        durable = job["attempts"] and (lab.safe(self.directory, job["attempts"][-1]["directory"]) / "result.json").exists()
        if job["status"] != "complete" and not durable and not self.cache_path(payload).exists():
            if self.max_new is not None and self.new_features >= self.max_new:
                raise lab.Paused("Feature chunk complete; resume this embedding experiment")
        return super().execute(kind, payload)

    def worker(self, command, input_path, output_path, log_path):
        payload = lab.read(input_path)
        spec = self.manifest["identity"]["spec"]
        cache = self.cache_path(payload)
        cache.parent.mkdir(parents=True, exist_ok=True)
        with Path(log_path).open("x", encoding="utf-8") as stream:
            with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream), lab.RunLock(cache.parent):
                if cache.exists():
                    result = vector_valid(lab.read(cache), payload["cacheKey"], self.manifest["identitySha256"], spec["dimension"])
                    self.state["featureCacheHits"] += 1
                    self.log.event("feature_cache_hit", cacheKey=payload["cacheKey"])
                else:
                    if self.backend is None:
                        self.log.event("backend_loading", model=spec["modelId"], revision=spec["revision"])
                        self.backend = self.factory(spec, Path(self.manifest["modelCache"]), self.download)
                    pcm = pcm_window(self.directory, payload, spec) if payload["kind"] == "audio" else None
                    vector = self.backend.feature(payload["kind"], payload, pcm)
                    result = {"version": VERSION, "cacheKey": payload["cacheKey"],
                              "identity": self.manifest["identitySha256"], "vector": vector,
                              "vectorSha256": lab.sha(lab.encode(vector))}
                    vector_valid(result, payload["cacheKey"], self.manifest["identitySha256"], spec["dimension"])
                    lab.atomic(cache, lab.encode(result), exclusive=True)
                    self.new_features += 1
                    self.state["computedFeatures"] += 1
                    self.log.event("feature_computed", cacheKey=payload["cacheKey"])
                lab.atomic(output_path, lab.encode({"requestSha256": lab.sha(input_path.read_bytes()),
                           "result": result}), exclusive=True)

    def drive(self):
        self.state["status"] = "running"
        self.save()
        for name, checksum in self.manifest["assets"].items():
            if lab.sha(lab.safe(self.directory, name).read_bytes()) != checksum:
                raise ValueError("Pinned source audio changed")
        vectors = {}
        for feature in self.manifest["features"]:
            result = self.execute("embedding-" + feature["kind"], feature)
            vectors[feature["cacheKey"]] = result["vector"]
            if all(key in vectors for key in self.manifest["sanityKeys"]):
                health = text_tower_sanity([vectors[key] for key in self.manifest["sanityKeys"]],
                         self.manifest["identity"]["spec"]["textTowerSanity"]["rejectIfMinimumPairwiseCosineAbove"])
                if not health["usable"]:
                    report = {"version": VERSION, "status": "unusable-checkpoint", "experimentId": self.manifest["id"],
                              "textTowerSanity": health, "summary": {"checkpointUsable": False}, "musicalWinner": None}
                    lab.atomic(self.directory / "report.json", lab.encode(report), exclusive=True)
                    self.state["status"] = "unusable-checkpoint"
                    self.save()
                    return
        report = diagnostics(self.manifest, vectors)
        report["textTowerSanity"] = health
        lab.atomic(self.directory / "report.json", lab.encode(report), exclusive=True)
        self.state["status"] = "diagnostic-only"
        self.save()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    start = commands.add_parser("start")
    start.add_argument("--run", type=Path, required=True)
    start.add_argument("--audio-root", type=Path, required=True)
    start.add_argument("--root", type=Path, default=ROOT / ".score-lab/embeddings")
    start.add_argument("--cache", type=Path)
    start.add_argument("--model-cache", type=Path)
    start.add_argument("--max-candidates", type=int, choices=range(1, 5), default=2)
    resume = commands.add_parser("resume")
    resume.add_argument("experiment", type=Path)
    status = commands.add_parser("status")
    status.add_argument("experiment", type=Path)
    for command in (start, resume):
        command.add_argument("--max-new-features", type=int)
        command.add_argument("--download-model", action="store_true")
    args = parser.parse_args(argv)
    directory = create(args.root, args.run, args.audio_root, max_candidates=args.max_candidates,
                       cache=args.cache, model_cache=args.model_cache) if args.command == "start" else args.experiment.resolve()
    print("Embedding experiment:", directory, flush=True)
    if args.command == "status":
        state = lab.read(directory / "state.json")
        print(json.dumps({k: state[k] for k in ("status", "computedFeatures", "featureCacheHits")}, indent=2))
        return 0
    with lab.RunLock(directory):
        log = lab.Invocation(directory)
        print("Log:", log.path, flush=True)
        engine = None
        try:
            if args.max_new_features is not None and args.max_new_features < 0:
                raise ValueError("Feature limit must be nonnegative")
            engine = EmbeddingEngine(directory, log, max_new=args.max_new_features, download=args.download_model)
            log.event("embedding_invocation_started", command=args.command, experiment=engine.manifest["id"])
            engine.drive()
            log.event("embedding_complete")
            print(json.dumps(lab.read(directory / "report.json")["summary"], indent=2))
            return 0
        except lab.Paused as error:
            engine.state["status"] = "paused"
            engine.save()
            log.event("paused", reason=str(error))
            print(str(error))
            return 0
        except Exception as error:
            if engine:
                engine.state["status"] = "failed"
                engine.save()
            log.event("embedding_failed", exception=type(error).__name__)
            print(f"{type(error).__name__}: {error}", file=sys.stderr)
            print(f'Resume: python tools/score_embeddings.py resume "{directory}"', file=sys.stderr)
            return 1
        finally:
            log.close()


if __name__ == "__main__":
    sys.exit(main())
