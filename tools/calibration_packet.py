"""Resumable blinded listening packets and explicitly human calibration labels (stdlib only)."""
from __future__ import annotations
import argparse
import array
from datetime import datetime
import io
import json
import math
from pathlib import Path
import random
import subprocess
import sys
import uuid
import wave

import score_lab as lab

VERSION = "awen-calibration-1"
LABEL_VERSION = "awen-calibration-labels-1"
ROOT = lab.ROOT
PLAN_WORKER = ROOT / "tools/calibration-worker.cjs"
TEMPLATE = ROOT / "tools/calibration-review.html"
FIELDS = ("fit", "enjoyment", "lessDistracting")
CHOICES = (None, "A", "B", "tie", "unsure")


def sources():
    return {**lab.fingerprints(), **{name: lab.sha((ROOT / name).read_bytes()) for name in (
        "tools/calibration_packet.py", "tools/calibration-worker.cjs", "tools/calibration-review.html",
        "research/calibration-scenes.json")}}


NATIVE_SOURCES = ("index.html", "tools/score-lab.cjs", "tools/score-lab-worker.cjs",
                  "tools/score-lab-metrics.cjs", "tools/calibration-worker.cjs", "research/calibration-scenes.json")


def create(root, seed, reuse_from=None):
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    directory = root / (lab.stamp() + "-" + uuid.uuid4().hex)
    directory.mkdir()
    manifest = {"version": VERSION, "id": uuid.uuid4().hex, "createdAt": lab.now(),
                "sources": sources(), "seed": seed,
                "reuseFrom": str(Path(reuse_from).resolve()) if reuse_from else None}
    raw = lab.encode(manifest)
    lab.atomic(directory / "experiment.json", raw, exclusive=True)
    lab.atomic(directory / "state.json", lab.encode({"version": VERSION, "status": "created",
        "manifestSha256": lab.sha(raw), "jobs": {}, "renderer": None,
        "judgeIdentity": None, "judgeCallsStarted": 0}))
    return directory


def pcm_read(file, crop):
    with wave.open(str(file), "rb") as audio:
        if (audio.getnchannels(), audio.getsampwidth(), audio.getframerate(), audio.getcomptype()) != (1, 2, 24000, "NONE"):
            raise ValueError("Expected production mono PCM16 24 kHz audio")
        start, count = crop["startFrame"], crop["frameCount"]
        if start < 0 or count <= 0 or start + count > audio.getnframes():
            raise ValueError("Invalid crop")
        audio.setpos(start)
        samples = array.array("h")
        samples.frombytes(audio.readframes(count))
    if sys.byteorder != "little":
        samples.byteswap()
    # Attenuate the excerpt boundaries without inserting a new musical cue.
    fade = min(4800, len(samples) // 2)
    for i in range(fade):
        samples[i] = round(samples[i] * i / fade)
        samples[-i-1] = round(samples[-i-1] * i / fade)
    return samples


def rms(samples):
    return math.sqrt(sum(v * v for v in samples) / max(1, len(samples))) / 32768


def wav_bytes(samples, gain):
    if not 0 < gain <= 1:
        raise ValueError("Comparison gain must attenuate only")
    values = array.array("h", (round(v * gain) for v in samples))
    peak = max(map(abs, values), default=0) / 32768
    if peak > .140001:
        raise ValueError("Comparison exceeds production output cap")
    if sys.byteorder != "little":
        values.byteswap()
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as audio:
        audio.setparams((1, 2, 24000, 0, "NONE", "not compressed"))
        audio.writeframes(values.tobytes())
    return buffer.getvalue(), peak


def build_packet(directory, manifest, plan, renders):
    """Private design/key lives outside public/. No preferred music is labelled as truth."""
    rng = random.Random(manifest["seed"] + "|" + manifest["id"])
    packet = {"version": VERSION, "id": manifest["id"], "scenes": [], "trials": [],
              "instructions": "Read the passage and compare music A and B. Rate fit, enjoyment and distraction separately. Ties and unsure are welcome; skip or stop whenever you like.",
              "sampleRate": 24000, "design": "Small developer-selected pilot; no correct musical choice or reading benefit is assumed."}
    key = {"version": VERSION, "packetId": manifest["id"], "planId": plan["id"],
           "scenes": [], "trials": [], "holdoutBooks": plan["suite"]["holdoutBooks"]}
    primary = []
    for scene in plan["scenes"]:
        public_id = "s-" + lab.sha((manifest["id"] + scene["id"]).encode())[:16]
        packet["scenes"].append({"id": public_id, "book": scene["book"], "chapter": scene["chapter"],
                   "paragraphId": scene["current"]["paragraphId"], "text": scene["current"]["text"],
                   "context": scene["previous"]["text"] if scene["previous"] else None})
        pairs = []
        for candidate in scene["candidates"]:
            render = renders[(scene["id"], candidate["id"])]
            if not render["gate"]["eligible"]:
                raise ValueError(f"Native engineering gate failed: {scene['id']}")
            file = lab.safe(directory, render["file"])
            if lab.sha(file.read_bytes()) != render["sha256"]:
                raise ValueError("Native WAV hash mismatch")
            samples = pcm_read(file, scene["crop"])
            pairs.append((candidate, render, samples, rms(samples)))
        target = min(.018, *(value[3] for value in pairs))
        if target < .0005:
            raise ValueError("A cropped comparison is near silent")
        clips = []
        for candidate, native, samples, level in pairs:
            gain = min(1, target / level)
            data, peak = wav_bytes(samples, gain)
            checksum = lab.sha(data)
            filename = "audio/a-" + checksum + ".wav"
            lab.atomic(directory / "public" / filename, data, exclusive=True)
            descriptor = {"file": filename, "sha256": checksum, "seconds": len(samples) / 24000}
            clips.append({"candidate": candidate, "descriptor": descriptor, "gain": gain,
                          "preGainRms": level, "postGainRms": level * gain, "peak": peak,
                          "nativeSha256": native["sha256"]})
        key["scenes"].append({"id": scene["id"], "publicId": public_id,
                              "selectionNote": scene["selectionNote"], "clips": clips})
        for other in (1, 2):
            primary.append({"scene": public_id, "sceneKey": scene["id"], "clips": [clips[0], clips[other]],
                            "kind": "primary", "pair": scene["id"] + "/" + str(other)})
    # Counterbalance incumbent slot across the twelve ordinary comparisons.
    orientations = [False] * (len(primary) // 2) + [True] * (len(primary) - len(primary) // 2)
    rng.shuffle(orientations)
    design = []
    for i, (comparison, reverse) in enumerate(zip(primary, orientations)):
        comparison = {**comparison, "clips": list(reversed(comparison["clips"])) if reverse else comparison["clips"]}
        design.append(comparison)
        if i in (0, 4, 8):
            design.append({**comparison, "clips": list(reversed(comparison["clips"])), "kind": "swapped"})
    # One identical-audio control per book, not a preferred-genre answer key.
    for i in (1, 3, 5):
        scene = key["scenes"][i]
        clip = scene["clips"][0]
        design.append({"scene": scene["publicId"], "sceneKey": scene["id"], "clips": [clip, clip],
                       "kind": "identical", "pair": scene["id"] + "/identical"})
    for i, item in enumerate(design):
        trial_id = "t-" + lab.sha((manifest["id"] + "|" + str(i)).encode())[:20]
        packet["trials"].append({"id": trial_id, "scene": item["scene"],
                                "A": item["clips"][0]["descriptor"], "B": item["clips"][1]["descriptor"]})
        key["trials"].append({"id": trial_id, "scene": item["sceneKey"], "kind": item["kind"],
                  "pair": item["pair"], "A": item["clips"][0]["candidate"]["id"],
                  "B": item["clips"][1]["candidate"]["id"]})
    rng.shuffle(packet["trials"])
    raw = lab.encode(packet)
    packet_hash = lab.sha(raw)
    lab.atomic(directory / "public/packet.json", raw, exclusive=True)
    key["packetSha256"] = packet_hash
    lab.atomic(directory / "private-key.json", lab.encode(key), exclusive=True)
    embedded = json.dumps({"packet": packet, "packetSha256": packet_hash}, ensure_ascii=False).replace("<", "\\u003c")
    html = TEMPLATE.read_text(encoding="utf-8").replace("__CALIBRATION_DATA__", embedded)
    lab.atomic(directory / "public/review.html", html.encode("utf-8"), exclusive=True)
    return {"packetId": packet["id"], "packetSha256": packet_hash, "scenes": len(packet["scenes"]),
            "trials": len(packet["trials"]), "audioFiles": sum(len(s["clips"]) for s in key["scenes"]),
            "status": "awaiting-human-labels", "humanLabels": 0}


class CalibrationEngine(lab.Engine):
    def __init__(self, directory, log, *, node=None, max_new_renders=None, fault_hook=None):
        self.directory = Path(directory).resolve()
        self.manifest, self.state = lab.read(self.directory / "experiment.json"), lab.read(self.directory / "state.json")
        if self.manifest["version"] != VERSION or self.state["version"] != VERSION:
            raise ValueError("Unsupported calibration packet")
        if self.state["manifestSha256"] != lab.sha((self.directory / "experiment.json").read_bytes()) or self.manifest["sources"] != sources():
            raise ValueError("Calibration source/manifest changed; start a new packet")
        import shutil
        self.node = node or shutil.which("node")
        if not self.node:
            raise RuntimeError("Node is required for native rendering")
        self.log, self.retry = log, set()
        self.max_new_renders, self.new_renders = max_new_renders, 0
        self.fault_hook = fault_hook or (lambda *_: None)
        self.reuse_source = Path(self.manifest["reuseFrom"]) if self.manifest.get("reuseFrom") else None
        self.reuse_state = self.reuse_manifest = None
        self.reuse_current = None
        self.last_reused = False

    def reusable(self, payload):
        if not self.reuse_source:
            return None
        if self.reuse_state is None:
            self.reuse_manifest = lab.read(self.reuse_source / "experiment.json")
            self.reuse_state = lab.read(self.reuse_source / "state.json")
            if self.reuse_manifest.get("version") != VERSION or any(
                self.reuse_manifest["sources"].get(name) != self.manifest["sources"][name] for name in NATIVE_SOURCES):
                raise ValueError("Render source has incompatible native engine/scene versions")
            if self.reuse_state["manifestSha256"] != lab.sha((self.reuse_source / "experiment.json").read_bytes()):
                raise ValueError("Reuse source manifest changed")
        encoded = lab.encode(payload)
        key = "render-" + lab.sha(encoded)[:24]
        job = self.reuse_state["jobs"].get(key)
        if not job or job["status"] != "complete" or job["inputSha256"] != lab.sha(encoded):
            return None
        if lab.sha(lab.safe(self.reuse_source, job["input"]).read_bytes()) != job["inputSha256"]:
            raise ValueError("Reusable native input changed")
        file = lab.safe(self.reuse_source, job["result"])
        if lab.sha(file.read_bytes()) != job["resultSha256"]:
            raise ValueError("Reusable native result changed")
        result = lab.read(file)
        if result["requestSha256"] != job["inputSha256"]:
            raise ValueError("Reusable result belongs to another input")
        for name, checksum in (("file", "sha256"), ("traceFile", "traceSha256")):
            artifact = (file.parent / result["result"][name]).resolve()
            if not artifact.is_relative_to(file.parent.resolve()) or lab.sha(artifact.read_bytes()) != result["result"][checksum]:
                raise ValueError("Reusable native artifact changed")
        return {"file": file, "envelope": result, "job": key}

    def execute(self, kind, payload):
        _, own = self.ensure_job(kind, payload)
        self.reuse_current = self.reusable(payload) if kind == "render" and own["status"] != "complete" else None
        limit, before = self.max_new_renders, self.new_renders
        if self.reuse_current:
            self.max_new_renders = None
        self.last_reused = False
        try:
            result = super().execute(kind, payload)
            if self.last_reused and self.new_renders > before:
                self.new_renders -= 1
            return result
        finally:
            self.max_new_renders = limit
            self.reuse_current = None

    def worker(self, command, input_path, output_path, log_path):
        if command == "render" and self.reuse_current:
            source = self.reuse_current
            envelope = source["envelope"]
            for name, checksum in (("file", "sha256"), ("traceFile", "traceSha256")):
                data = (source["file"].parent / envelope["result"][name]).read_bytes()
                if lab.sha(data) != envelope["result"][checksum]:
                    raise ValueError("Reusable artifact changed during copy")
                lab.atomic(output_path.parent / envelope["result"][name], data, exclusive=True)
            result = {**envelope["result"], "reusedFrom": {"experimentId": self.reuse_manifest["id"],
                "manifestSha256": self.reuse_state["manifestSha256"], "job": source["job"]}}
            lab.atomic(output_path, lab.encode({"requestSha256": lab.sha(input_path.read_bytes()), "result": result}), exclusive=True)
            lab.atomic(log_path, ("Verified native reuse: " + source["job"] + "\n").encode(), exclusive=True)
            self.last_reused = True
            self.log.event("native_render_reused", sourceExperiment=self.reuse_manifest["id"], job=source["job"])
            return
        if command != "calibration-plan":
            return super().worker(command, input_path, output_path, log_path)
        with Path(log_path).open("xb") as stream:
            result = subprocess.run([self.node, str(PLAN_WORKER), "plan", str(input_path), str(output_path)],
                       cwd=self.directory, stdout=stream, stderr=subprocess.STDOUT, timeout=60)
        if result.returncode:
            raise RuntimeError(f"Calibration plan failed; see {log_path}")

    def drive(self):
        self.state["status"] = "rendering"
        self.save()
        plan = self.execute("calibration-plan", {"experimentId": self.manifest["id"], "seed": self.manifest["seed"]})
        renders = {}
        for scene in plan["scenes"]:
            for candidate in scene["candidates"]:
                payload = {"candidate": candidate, "fixture": scene["fixture"], "steps": plan["suite"]["renderSteps"]}
                render = self.execute("render", payload)
                _, job = self.ensure_job("render", payload)
                artifact_dir = lab.safe(self.directory, job["result"]).parent
                renders[(scene["id"], candidate["id"])] = {**render,
                    "file": str((artifact_dir / render["file"]).relative_to(self.directory)).replace("\\", "/")}
                print("Ready native clip:", scene["id"], candidate["id"], flush=True)
        proof = build_packet(self.directory, self.manifest, plan, renders)
        lab.atomic(self.directory / "packet-summary.json", lab.encode(proof), exclusive=True)
        self.state["status"] = proof["status"]
        self.save()
        print("Review:", self.directory / "public/review.html", flush=True)


def validate_labels(directory, data):
    packet_file = directory / "public/packet.json"
    packet = lab.read(packet_file)
    private = lab.read(directory / "private-key.json")
    if lab.sha(packet_file.read_bytes()) != private["packetSha256"] or packet["id"] != private["packetId"]:
        raise ValueError("Calibration packet was changed")
    if not isinstance(data, dict):
        raise ValueError("Expected a label object")
    if data.get("version") != LABEL_VERSION or data.get("packetId") != packet["id"] or data.get("packetSha256") != lab.sha(packet_file.read_bytes()):
        raise ValueError("Labels belong to another packet/version")
    rater = data.get("rater", {})
    if not isinstance(rater, dict) or rater.get("kind") != "human" or not isinstance(rater.get("id"), str) or not 1 <= len(rater["id"]) <= 128:
        raise ValueError("This importer requires self-reported human rater provenance")
    trials = {t["id"]: t for t in packet["trials"]}
    responses = data.get("responses")
    if not isinstance(responses, list) or len(responses) > len(trials):
        raise ValueError("Invalid response collection")
    seen = set()
    for response in responses:
        if not isinstance(response, dict):
            raise ValueError("Expected response objects")
        trial_id = response.get("trialId")
        if trial_id not in trials or trial_id in seen:
            raise ValueError("Unknown or duplicate trial")
        seen.add(trial_id)
        if any(response.get(field) not in CHOICES for field in FIELDS):
            raise ValueError("Invalid preference value")
        if not isinstance(response.get("revision"), int) or isinstance(response["revision"], bool) or response["revision"] < 1:
            raise ValueError("Invalid label revision")
        if response.get("confidence") not in (None, "low", "medium", "high") or not isinstance(response.get("heardBoth"), bool):
            raise ValueError("Missing listening/confidence provenance")
        if not isinstance(response.get("notes", ""), str) or len(response.get("notes", "")) > 1000:
            raise ValueError("Notes too long")
        try:
            if not isinstance(response.get("at"), str) or datetime.fromisoformat(response["at"].replace("Z", "+00:00")).tzinfo is None:
                raise ValueError("Timestamp requires a timezone")
        except (KeyError, TypeError):
            raise ValueError("Invalid response timestamp") from None
        played = response.get("playedSeconds", {})
        if set(played) != {"A", "B"} or not all(isinstance(v, (int, float)) and not isinstance(v, bool)
                         and math.isfinite(v) and 0 <= v <= 3600 for v in played.values()):
            raise ValueError("Invalid playback metadata")
    return packet


def import_labels(directory, file):
    if Path(file).stat().st_size > 1024 * 1024:
        raise ValueError("Label file exceeds 1 MB")
    raw = Path(file).read_bytes()
    data = json.loads(raw)
    validate_labels(directory, data)
    target = directory / "imports" / (lab.stamp() + "-" + uuid.uuid4().hex)
    target.mkdir(parents=True)
    lab.atomic(target / "labels.json", raw, exclusive=True)
    lab.atomic(target / "provenance.json", lab.encode({"importedAt": lab.now(), "sha256": lab.sha(raw),
             "raterSource": "self-reported", "responses": len(data["responses"])}), exclusive=True)
    return target


def summary(directory):
    key = lab.read(directory / "private-key.json")
    if lab.sha((directory / "public/packet.json").read_bytes()) != key["packetSha256"]:
        raise ValueError("Public packet checksum changed")
    metadata = {t["id"]: t for t in key["trials"]}
    grouped = {}
    for file in sorted((directory / "imports").glob("*/labels.json")):
        provenance = lab.read(file.parent / "provenance.json")
        if lab.sha(file.read_bytes()) != provenance["sha256"]:
            raise ValueError("Archived label import changed")
        data = lab.read(file)
        validate_labels(directory, data)
        for response in data["responses"]:
            grouped.setdefault((data["rater"]["id"], response["trialId"]), []).append(response)
    latest, conflicts = {}, []
    for pair, values in grouped.items():
        revision = max(v["revision"] for v in values)
        newest = {lab.sha(lab.encode(v)): v for v in values if v["revision"] == revision}
        if len(newest) != 1:
            conflicts.append({"rater": pair[0], "trial": pair[1], "revision": revision})
        else:
            latest[pair] = next(iter(newest.values()))
    counts = {field: {choice: 0 for choice in ("A", "B", "tie", "unsure", "unanswered")} for field in FIELDS}
    identical = {field: {"tie": 0, "nonTie": 0, "unsure": 0} for field in FIELDS}
    swaps = {field: {"consistent": 0, "inconsistent": 0, "unscored": 0} for field in FIELDS}
    usable = {pair: r for pair, r in latest.items() if r["heardBoth"]}
    primary_by_pair = {}
    for (rater, trial), response in usable.items():
        trial_meta = metadata[trial]
        if trial_meta["kind"] == "primary":
            primary_by_pair[(rater, trial_meta["pair"])] = (trial_meta, response)
            for field in FIELDS:
                counts[field][response.get(field) or "unanswered"] += 1
        elif trial_meta["kind"] == "identical":
            for field in FIELDS:
                value = response.get(field)
                identical[field]["tie" if value == "tie" else "nonTie" if value in ("A", "B") else "unsure"] += 1
    canonical = lambda meta, value: meta[value] if value in ("A", "B") else value
    for (rater, trial), response in usable.items():
        meta = metadata[trial]
        if meta["kind"] == "swapped" and (rater, meta["pair"]) in primary_by_pair:
            original, original_response = primary_by_pair[(rater, meta["pair"])]
            for field in FIELDS:
                a, b = canonical(meta, response.get(field)), canonical(original, original_response.get(field))
                swaps[field]["unscored" if a in (None, "unsure") or b in (None, "unsure") else "consistent" if a == b else "inconsistent"] += 1
    observations = []
    for (rater, trial), response in usable.items():
        meta = metadata[trial]
        if meta["kind"] == "primary":
            observations.append({"rater": rater, "trialId": trial, "scene": meta["scene"],
                "pair": meta["pair"], "A": meta["A"], "B": meta["B"],
                **{field: canonical(meta, response.get(field)) for field in FIELDS},
                "confidence": response["confidence"], "revision": response["revision"],
                "selfReportedHeardBoth": True, "playedSeconds": response["playedSeconds"]})
    return {"version": VERSION, "packetId": key["packetId"], "importedResponsesAfterDeduplication": len(latest),
            "selfReportedHeardBoth": len(usable), "notHeardBoth": len(latest) - len(usable),
            "raters": len({pair[0] for pair in latest}), "revisionConflicts": conflicts,
            "primaryResponses": counts, "identicalControls": identical, "swappedControls": swaps,
            "primaryPairs": observations,
            "sceneCoverage": {s["publicId"]: sum(metadata[t]["scene"] == s["id"] for (_, t) in usable) for s in key["scenes"]},
            "rewardCalibrated": False, "rankerTrained": False,
            "limitations": "Self-reported listening and human provenance, not verified perception. Small pilot, not independent held-out validation. No preferences are inferred for missing answers."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    start = commands.add_parser("start")
    start.add_argument("--root", type=Path, default=ROOT / ".score-lab/calibration")
    start.add_argument("--seed", default="calibration-001")
    start.add_argument("--reuse-renders-from", type=Path)
    resume = commands.add_parser("resume")
    resume.add_argument("experiment", type=Path)
    for command in (start, resume):
        command.add_argument("--node")
        command.add_argument("--max-new-renders", type=int)
    imp = commands.add_parser("import-labels")
    imp.add_argument("experiment", type=Path)
    imp.add_argument("--file", type=Path, required=True)
    inspect = commands.add_parser("summarize")
    inspect.add_argument("experiment", type=Path)
    args = parser.parse_args(argv)
    directory = create(args.root, args.seed, args.reuse_renders_from) if args.command == "start" else args.experiment.resolve()
    print("Calibration experiment:", directory, flush=True)
    with lab.RunLock(directory):
        log = lab.Invocation(directory)
        print("Log:", log.path, flush=True)
        engine = None
        try:
            log.event("calibration_invocation_started", command=args.command)
            if args.command in ("start", "resume"):
                if args.max_new_renders is not None and args.max_new_renders < 0:
                    raise ValueError("Render budget must be nonnegative")
                engine = CalibrationEngine(directory, log, node=args.node, max_new_renders=args.max_new_renders)
                engine.drive()
            elif args.command == "import-labels":
                print("Imported:", import_labels(directory, args.file))
            else:
                result = summary(directory)
                target = directory / "summaries" / (lab.stamp() + "-" + uuid.uuid4().hex + ".json")
                lab.atomic(target, lab.encode(result), exclusive=True)
                print(json.dumps(result, indent=2))
            log.event("calibration_invocation_finished")
            return 0
        except lab.Paused as error:
            engine.state["status"] = "paused"
            engine.save()
            log.event("paused", reason=str(error))
            print(error)
            return 0
        except Exception as error:
            if engine:
                engine.state["status"] = "failed"
                engine.save()
            log.event("calibration_failed", exception=type(error).__name__)
            print(f"{type(error).__name__}: {error}", file=sys.stderr)
            return 1
        finally:
            log.close()


if __name__ == "__main__":
    sys.exit(main())
