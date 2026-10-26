"""Resumable, development-only Python orchestration of Awen's native audio evaluator.

No Python dependencies beyond the standard library. Rendering needs Node/Playwright.
Run with --help. Provider adapters are optional trusted local Python modules.
"""
from __future__ import annotations

import argparse
import contextlib
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import traceback
import uuid

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "tools/score-lab-worker.cjs"
VERSION = "awen-score-lab-python-1"
SOURCES = ["index.html", "tools/score_lab.py", "tools/score-lab-worker.cjs",
           "tools/score-lab.cjs", "tools/score-lab-metrics.cjs",
           "research/score-lab-fixtures.json", "research/score-lab-judge.md"]


def now():
    return datetime.now(timezone.utc).isoformat()


def stamp():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False,
                       allow_nan=False) + "\n").encode("utf-8")


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def atomic(path, data, *, exclusive=False):
    """Publish complete bytes; an interrupted write leaves only a unique temp file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if exclusive and path.exists():
        if path.read_bytes() != data:
            raise ValueError(f"Refusing to replace archived artifact: {path}")
        return
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    with temp.open("xb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, path)
    if os.name != "nt":
        fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


def safe(root, relative):
    result = (root / relative).resolve()
    if result == root or not result.is_relative_to(root):
        raise ValueError("Artifact path escapes experiment")
    return result


class RunLock:
    """Kernel lock, released even after process death; no stale PID deletion."""
    def __init__(self, directory):
        self.path = directory / "run.lock"

    def __enter__(self):
        self.handle = self.path.open("a+b")
        if self.path.stat().st_size == 0:
            self.handle.write(b"0")
            self.handle.flush()
        self.handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(self.handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.handle.close()
            raise RuntimeError("Another process is already working on this experiment") from None
        return self

    def __exit__(self, *_):
        if os.name == "nt":
            import msvcrt
            self.handle.seek(0)
            msvcrt.locking(self.handle.fileno(), msvcrt.LK_UNLCK, 1)
        self.handle.close()


class Paused(Exception):
    pass


class UncertainSubmission(Exception):
    pass


class Invocation:
    def __init__(self, directory):
        self.id = uuid.uuid4().hex
        self.path = directory / "logs" / (stamp() + "-" + self.id + ".jsonl")
        self.path.parent.mkdir(exist_ok=True)
        self.handle = self.path.open("x", encoding="utf-8")

    def event(self, event_name, **fields):
        self.handle.write(json.dumps({"time": now(), "invocation": self.id,
                                      "event": event_name, **fields}, allow_nan=False) + "\n")
        self.handle.flush()
        os.fsync(self.handle.fileno())

    def close(self):
        self.handle.close()


def fingerprints():
    return {name: sha((ROOT / name).read_bytes()) for name in SOURCES}


def create(root, *, seed="lab-001", budget=4, rounds=1, judge_limit=14):
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    directory = root / (stamp() + "-" + uuid.uuid4().hex)
    directory.mkdir()
    manifest = {"version": VERSION, "id": uuid.uuid4().hex, "createdAt": now(),
                "sources": fingerprints(), "python": sys.version,
                "config": {"seed": seed, "budget": budget, "rounds": rounds}}
    atomic(directory / "experiment.json", encode(manifest), exclusive=True)
    atomic(directory / "state.json", encode({"version": VERSION, "status": "created",
           "jobs": {}, "judgeCallsStarted": 0, "judgeLimit": judge_limit,
           "adapter": None, "renderer": None, "judgeIdentity": None}))
    atomic(directory / "judge-instructions.md",
           (ROOT / "research/score-lab-judge.md").read_bytes(), exclusive=True)
    return directory


class Engine:
    def __init__(self, directory, log, *, node=None, retry=(), max_new_renders=None,
                 fault_hook=None):
        self.directory = Path(directory).resolve()
        self.manifest = read(self.directory / "experiment.json")
        self.state = read(self.directory / "state.json")
        if self.manifest["version"] != VERSION or self.state["version"] != VERSION:
            raise ValueError("Unsupported experiment version")
        if self.manifest["sources"] != fingerprints():
            raise ValueError("Source fingerprints changed; start a new experiment instead of mixing versions")
        self.log, self.retry = log, set(retry)
        for key in self.retry:
            job = self.state["jobs"].get(key)
            if not job or job["kind"] != "judge" or job["status"] not in ("running", "uncertain", "invalid-response"):
                raise ValueError("--retry-uncertain requires an unfinished judge job ID")
        self.node = node or shutil.which("node")
        if not self.node:
            raise RuntimeError("Node is required for the production renderer")
        self.max_new_renders, self.new_renders = max_new_renders, 0
        self.fault_hook = fault_hook or (lambda *_: None)
        self.adapter_function = None

    def save(self):
        atomic(self.directory / "state.json", encode(self.state))

    def adapter(self, filename=None):
        if filename:
            file = Path(filename).resolve()
            info = {"path": str(file), "sha256": sha(file.read_bytes())}
            if self.state["adapter"] and self.state["adapter"] != info:
                raise ValueError("Adapter differs from this experiment's pinned adapter")
            self.state["adapter"] = info
            self.save()
        info = self.state["adapter"]
        if not info:
            return
        if sha(Path(info["path"]).read_bytes()) != info["sha256"]:
            raise ValueError("Adapter source changed; use a new experiment")
        spec = importlib.util.spec_from_file_location("awen_local_judge_" + info["sha256"], info["path"])
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if not callable(getattr(module, "judge", None)):
            raise ValueError("Python adapter must export judge(request, context)")
        self.adapter_function = module.judge

    def worker(self, command, input_path, output_path, log_path):
        with Path(log_path).open("xb") as output:
            process = subprocess.Popen([self.node, str(WORKER), "judge" if command == "judge-summary" else command,
                                       str(input_path), str(output_path)],
                                      cwd=self.directory, stdout=output, stderr=subprocess.STDOUT)
            try:
                code = process.wait()
            except BaseException:
                process.terminate()
                process.wait()
                raise
        if code:
            raise RuntimeError(f"Native {command} worker exited {code}; see {log_path}")

    def verify(self, job, result_path):
        envelope = read(result_path)
        if envelope["requestSha256"] != job["inputSha256"]:
            raise ValueError("Cached result belongs to another request")
        result = envelope["result"]
        if job["kind"] == "render":
            for key, hash_key in [("file", "sha256"), ("traceFile", "traceSha256")]:
                artifact = result_path.parent / result[key]
                if not artifact.resolve().is_relative_to(result_path.parent.resolve()):
                    raise ValueError("Invalid cached clip path")
                if sha(artifact.read_bytes()) != result[hash_key]:
                    raise ValueError("Cached render artifact hash mismatch; refusing silent replacement")
            if self.state["renderer"] and self.state["renderer"] != result["renderer"]:
                raise ValueError("Renderer version changed during experiment")
            self.state["renderer"] = result["renderer"]
        elif job["kind"] == "judge":
            # Rehydrate provenance after a crash between response publication and state commit.
            identity = [result.get("model"), result.get("modelVersion")]
            if not all(isinstance(value, str) and value.strip() for value in identity):
                raise ValueError("Cached judge provenance is invalid")
            if self.state["judgeIdentity"] and self.state["judgeIdentity"] != identity:
                raise ValueError("Cached judge model/version differs from experiment")
            self.state["judgeIdentity"] = identity
        return result

    def ensure_job(self, kind, payload):
        data = encode(payload)
        key = kind + "-" + sha(data)[:24]
        relative = f"jobs/{key}/input.json"
        atomic(safe(self.directory, relative), data, exclusive=True)
        if key not in self.state["jobs"]:
            self.state["jobs"][key] = {"kind": kind, "input": relative,
                 "inputSha256": sha(data), "status": "pending", "attempts": []}
            self.save()
        job = self.state["jobs"][key]
        if sha(safe(self.directory, job["input"]).read_bytes()) != job["inputSha256"]:
            raise ValueError("Archived job input changed")
        return key, job

    def finish(self, key, job, attempt, result_path):
        result = self.verify(job, result_path)
        attempt["status"] = "complete"
        attempt["resultSha256"] = sha(result_path.read_bytes())
        job["status"], job["result"] = "complete", str(result_path.relative_to(self.directory))
        job["resultSha256"] = attempt["resultSha256"]
        self.save()
        self.log.event("job_complete", job=key, attempt=attempt["id"])
        return result

    def validate_response(self, payload, response, attempt_dir):
        identity = [response.get("model"), response.get("modelVersion")]
        if self.state["judgeIdentity"] and self.state["judgeIdentity"] != identity:
            raise ValueError("Judge model/version changed during experiment")
        request = {"run": payload["run"], "requestId": payload["request"]["id"],
                   "response": response}
        file = attempt_dir / ("validate-" + uuid.uuid4().hex + ".json")
        output = file.with_name(file.stem + "-result.json")
        atomic(file, encode(request), exclusive=True)
        self.worker("validate-verdict", file, output, file.with_suffix(".log"))
        self.state["judgeIdentity"] = identity
        return response

    def commit_response(self, job, payload, response, attempt_dir):
        # Raw response is durable BEFORE validation, so failures never cause a blind paid retry.
        atomic(attempt_dir / "provider-response.json", encode(response), exclusive=True)
        self.validate_response(payload, response, attempt_dir)
        atomic(attempt_dir / "result.json", encode({"requestSha256": job["inputSha256"],
               "result": response}), exclusive=True)

    def execute(self, kind, payload):
        key, job = self.ensure_job(kind, payload)
        if job["status"] == "complete":
            file = safe(self.directory, job["result"])
            if sha(file.read_bytes()) != job["resultSha256"]:
                raise ValueError("Cached job result changed")
            self.log.event("cache_hit", job=key)
            return self.verify(job, file)
        # Recover an artifact published just before process death, without executing again.
        if job["attempts"] and job["status"] in ("running", "uncertain", "invalid-response"):
            previous = job["attempts"][-1]
            directory = safe(self.directory, previous["directory"])
            result_path = directory / "result.json"
            if result_path.exists():
                return self.finish(key, job, previous, result_path)
            if kind == "judge" and (directory / "provider-response.json").exists():
                try:
                    self.commit_response(job, payload, read(directory / "provider-response.json"), directory)
                except Exception:
                    job["status"] = "invalid-response"
                    self.save()
                    if key not in self.retry:
                        raise UncertainSubmission(f"Saved judge response needs attention: {key}") from None
                else:
                    return self.finish(key, job, previous, result_path)
            if kind == "judge" and key not in self.retry:
                job["status"] = "uncertain"
                self.save()
                raise UncertainSubmission(f"Judge may already have processed {key}; reconcile a response or explicitly retry it")
        if kind == "render" and self.max_new_renders is not None and self.new_renders >= self.max_new_renders:
            raise Paused("Render chunk complete; resume this experiment to continue")
        if kind == "judge" and self.state["judgeCallsStarted"] >= self.state["judgeLimit"]:
            raise Paused("Judge request budget reached; resume with an explicit --add-judge-requests if intended")
        attempt = {"id": uuid.uuid4().hex, "status": "running", "startedAt": now()}
        attempt["directory"] = f"jobs/{key}/attempts/{stamp()}-{attempt['id']}"
        directory = safe(self.directory, attempt["directory"])
        directory.mkdir(parents=True)
        job["attempts"].append(attempt)
        job["status"] = "running"
        if kind == "judge":
            self.state["judgeCallsStarted"] += 1
        self.save()  # Write-ahead submission record: never repeat an ambiguous paid request automatically.
        self.log.event("job_started", job=key, kind=kind, attempt=attempt["id"])
        self.fault_hook("before_execution", key)
        try:
            if kind == "judge":
                context = {"directory": str(self.directory), "job_id": key,
                   "attempt_id": attempt["id"], "idempotency_key": self.manifest["id"] + "/" + key,
                   "version": payload["run"]["version"], "run_id": payload["run"]["id"],
                   "instructions": str(self.directory / "judge-instructions.md"),
                   "checkpoint": lambda response: self.commit_response(job, payload, response, directory)}
                with (directory / "adapter.log").open("x", encoding="utf-8") as stream:
                    with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
                        response = self.adapter_function(payload["request"], context)
                self.fault_hook("after_provider_return", key)
                self.commit_response(job, payload, response, directory)
            else:
                self.worker(kind, safe(self.directory, job["input"]), directory / "result.json",
                            directory / "worker.log")
                if kind == "render":
                    self.new_renders += 1
            self.fault_hook("after_result_publish", key)
            return self.finish(key, job, attempt, directory / "result.json")
        except Exception as error:
            job["status"] = "uncertain" if kind == "judge" else "failed"
            attempt["status"] = job["status"]
            self.save()
            atomic(directory / "failure.txt", traceback.format_exc().encode("utf-8"), exclusive=True)
            self.log.event("job_failed", job=key, kind=kind, exception=type(error).__name__)
            raise

    def drive(self):
        self.state["status"] = "running"
        self.save()
        config = self.manifest["config"]
        parent = None
        for round_number in range(config["rounds"]):
            plan = self.execute("plan", {"experimentId": self.manifest["id"],
                "seed": config["seed"], "budget": config["budget"], "round": round_number,
                "split": "development", "parent": parent})
            clips = []
            for candidate in plan["candidates"]:
                for fixture in plan["cases"]:
                    payload = {"candidate": candidate, "fixture": fixture, "steps": plan["settings"]["steps"]}
                    clip = self.execute("render", payload)
                    _, job = self.ensure_job("render", payload)
                    result_dir = safe(self.directory, job["result"]).parent
                    clip = {**clip, **{k: str((result_dir / clip[k]).relative_to(self.directory)).replace("\\", "/")
                                      for k in ("file", "traceFile")}}
                    clips.append(clip)
            assembled = self.execute("assemble", {"plan": plan, "clips": clips})
            round_dir = self.directory / f"round-{round_number:03d}"
            atomic(round_dir / "run.json", encode(assembled["run"]), exclusive=True)
            atomic(round_dir / "judge-packet.json", encode(assembled["packet"]), exclusive=True)
            if not assembled["run"]["candidates"][0]["eligible"]:
                self.state["status"] = "baseline-failed-gates"
                self.save()
                return
            if not self.adapter_function:
                self.state["status"] = "awaiting-audio-judge"
                self.save()
                return
            responses = [self.execute("judge", {"run": assembled["run"], "request": request})
                         for request in assembled["packet"]["requests"]]
            identity = self.state["judgeIdentity"]
            aggregate = {"version": assembled["packet"]["version"], "runId": plan["id"],
                         "model": identity[0], "modelVersion": identity[1],
                         "verdicts": [response["verdict"] for response in responses]}
            result = self.execute("judge-summary", {"run": assembled["run"], "responses": aggregate})
            atomic(round_dir / "judgment.json", encode(result["decision"]), exclusive=True)
            if result["proposal"]:
                atomic(round_dir / "proposal.json", encode(result["proposal"]), exclusive=True)
                parent = result["proposal"]["candidate"]
            else:
                self.state["status"] = result["decision"]["status"]
                self.save()
                return
        self.state["status"] = "development-proposal"
        self.save()

    def recover_response(self, key, filename):
        job = self.state["jobs"].get(key)
        if not job or job["kind"] != "judge" or job["status"] not in ("running", "uncertain", "invalid-response"):
            raise ValueError("Recovery requires an unfinished judge job")
        # Reconciliation is a new, uniquely archived attempt; never replace failed provider output.
        attempt = {"id": uuid.uuid4().hex, "status": "running", "startedAt": now(), "reconciled": True}
        attempt["directory"] = f"jobs/{key}/attempts/{stamp()}-{attempt['id']}"
        directory = safe(self.directory, attempt["directory"])
        directory.mkdir(parents=True)
        job["attempts"].append(attempt)
        self.save()
        self.commit_response(job, read(safe(self.directory, job["input"])), read(filename), directory)
        self.finish(key, job, attempt, directory / "result.json")
        self.log.event("response_reconciled", job=key)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    start = commands.add_parser("start")
    start.add_argument("--root", type=Path, default=ROOT / ".score-lab/python")
    start.add_argument("--seed", default="lab-001")
    start.add_argument("--budget", type=int, choices=range(2, 5), default=4)
    start.add_argument("--rounds", type=int, choices=range(1, 4), default=1)
    start.add_argument("--judge-requests", type=int)
    resume = commands.add_parser("resume")
    resume.add_argument("experiment", type=Path)
    resume.add_argument("--retry-uncertain", action="append", default=[])
    resume.add_argument("--add-judge-requests", type=int, default=0)
    recover = commands.add_parser("recover-response")
    recover.add_argument("experiment", type=Path)
    recover.add_argument("--job", required=True)
    recover.add_argument("--response", type=Path, required=True)
    status = commands.add_parser("status")
    status.add_argument("experiment", type=Path)
    for command in (start, resume):
        command.add_argument("--judge-adapter", type=Path)
        command.add_argument("--max-new-renders", type=int)
    for command in (start, resume, recover):
        command.add_argument("--node", help="Node executable; otherwise found on PATH")
    args = parser.parse_args(argv)
    if args.command == "start":
        limit = args.judge_requests if args.judge_requests is not None else 14 * args.rounds
        if not 1 <= limit <= 100:
            parser.error("Judge request budget must be 1..100")
        directory = create(args.root, seed=args.seed, budget=args.budget, rounds=args.rounds, judge_limit=limit)
    else:
        directory = args.experiment.resolve()
    print("Experiment:", directory, flush=True)
    if args.command == "status":
        state = read(directory / "state.json")
        print(json.dumps({"status": state["status"], "judgeCallsStarted": state["judgeCallsStarted"],
              "judgeLimit": state["judgeLimit"], "jobs": {key: {"kind": job["kind"],
              "status": job["status"], "attempts": len(job["attempts"])} for key, job in state["jobs"].items()}}, indent=2))
        return 0
    with RunLock(directory):
        log = Invocation(directory)
        print("Log:", log.path, flush=True)
        engine = None
        try:
            engine = Engine(directory, log, node=args.node, retry=getattr(args, "retry_uncertain", ()),
                            max_new_renders=getattr(args, "max_new_renders", None))
            log.event("invocation_started", command=args.command, experiment=engine.manifest["id"])
            if args.command == "recover-response":
                engine.recover_response(args.job, args.response)
            else:
                extra = getattr(args, "add_judge_requests", 0)
                if extra < 0 or engine.state["judgeLimit"] + extra > 100:
                    raise ValueError("Total explicit judge budget must remain <=100")
                if extra:
                    engine.state["judgeLimit"] += extra
                    engine.save()
                    log.event("judge_budget_added", requests=extra)
                if args.max_new_renders is not None and args.max_new_renders < 0:
                    raise ValueError("--max-new-renders must be nonnegative")
                engine.adapter(args.judge_adapter)
                engine.drive()
            log.event("invocation_finished", status=engine.state["status"])
            print("Status:", engine.state["status"])
            return 0
        except Paused as error:
            engine.state["status"] = "paused"
            engine.save()
            log.event("paused", reason=str(error))
            print(str(error))
            return 0
        except Exception as error:
            if engine:
                engine.state["status"] = "needs-reconciliation" if isinstance(error, UncertainSubmission) else "failed"
                engine.save()
            log.event("invocation_failed", exception=type(error).__name__)
            print(f"{type(error).__name__}: {error}", file=sys.stderr)
            print(f"Resume: python tools/score_lab.py resume \"{directory}\"", file=sys.stderr)
            return 1
        finally:
            log.close()


if __name__ == "__main__":
    sys.exit(main())
