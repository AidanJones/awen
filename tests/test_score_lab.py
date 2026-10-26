"""Job lifecycle/failure tests; all fake provider replies are explicitly TEST ONLY.

Run: python -m unittest discover -s tests -p test_score_lab.py -v
Native audio integration is a separate, small real-render smoke run.
"""
import importlib.util
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

TOOL = Path(__file__).resolve().parents[1] / "tools/score_lab.py"
spec = importlib.util.spec_from_file_location("score_lab", TOOL)
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)


class SimulatedDeath(BaseException):
    pass


class FakeEngine(lab.Engine):
    """Only deterministic fake IO; does not pretend to render or judge actual music."""
    executions = 0

    def worker(self, command, input_path, output_path, log_path):
        type(self).executions += 1
        lab.atomic(log_path, b"TEST-ONLY worker\n", exclusive=True)
        payload = lab.read(input_path)
        if command == "render":
            wav, trace = b"TEST-ONLY-AUDIO", b'{"TEST-ONLY":true}\n'
            lab.atomic(output_path.parent / "audio.wav", wav, exclusive=True)
            lab.atomic(output_path.parent / "trace.json", trace, exclusive=True)
            result = {"file": "audio.wav", "sha256": lab.sha(wav), "traceFile": "trace.json",
                      "traceSha256": lab.sha(trace), "renderer": {"browser": "TEST ONLY"}}
        else:
            result = {"TEST-ONLY": payload}
        lab.atomic(output_path, lab.encode({"requestSha256": lab.sha(input_path.read_bytes()),
                                           "result": result}), exclusive=True)

    def validate_response(self, payload, response, attempt_dir):
        if response.get("model") != "TEST-ONLY-MOCK" or response.get("runId") != payload["run"]["id"]:
            raise ValueError("Invalid TEST ONLY reply")
        self.state["judgeIdentity"] = [response["model"], response["modelVersion"]]
        return response


PAYLOAD = {"run": {"id": "TEST-ONLY-RUN", "version": "awen-score-lab-1"},
           "request": {"id": "TEST-ONLY-REQUEST", "clips": []}}
RESPONSE = {"version": "awen-score-lab-1", "runId": "TEST-ONLY-RUN",
            "model": "TEST-ONLY-MOCK", "modelVersion": "not-an-actual-judge",
            "verdict": {"id": "TEST-ONLY-REQUEST"}}


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        test_root = (lab.ROOT / ".score-lab/tests").resolve()
        test_root.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=test_root)
        assert Path(self.temp.name).resolve().is_relative_to(test_root)
        self.addCleanup(self.temp.cleanup)
        self.directory = lab.create(Path(self.temp.name))
        self.logs = []
        FakeEngine.executions = 0

    def engine(self, **kwargs):
        log = lab.Invocation(self.directory)
        self.logs.append(log)
        self.addCleanup(log.close)
        return FakeEngine(self.directory, log, **kwargs)

    def test_unique_experiments_logs_and_attempts(self):
        other = lab.create(Path(self.temp.name))
        self.assertNotEqual(other, self.directory)
        a, b = self.engine(), self.engine()
        self.assertNotEqual(a.log.path, b.log.path)
        a.execute("plan", {"test": 1})
        state = lab.read(self.directory / "state.json")
        job = next(iter(state["jobs"].values()))
        self.assertEqual(len(job["attempts"]), 1)
        self.assertTrue((self.directory / job["attempts"][0]["directory"] / "worker.log").exists())

    def test_completed_render_is_reused_without_reexecution(self):
        a = self.engine()
        first = a.execute("render", {"test": 1})
        b = self.engine()
        self.assertEqual(first, b.execute("render", {"test": 1}))
        self.assertEqual(FakeEngine.executions, 1)

    def test_crash_after_artifact_publication_recovers_without_reexecution(self):
        def fault(event, key):
            if event == "after_result_publish":
                raise SimulatedDeath()
        with self.assertRaises(SimulatedDeath):
            self.engine(fault_hook=fault).execute("render", {"test": 1})
        state = lab.read(self.directory / "state.json")
        self.assertEqual(next(iter(state["jobs"].values()))["status"], "running")
        self.engine().execute("render", {"test": 1})
        self.assertEqual(FakeEngine.executions, 1)

    def test_failed_local_worker_retries_in_new_attempt_preserving_old_log(self):
        engine = self.engine()
        original = engine.worker
        def failed(command, input_path, output_path, log_path):
            lab.atomic(log_path, b"TEST-ONLY failure", exclusive=True)
            raise RuntimeError("TEST-ONLY failure")
        engine.worker = failed
        with self.assertRaises(RuntimeError):
            engine.execute("render", {"test": 1})
        key = next(iter(engine.state["jobs"]))
        first = engine.state["jobs"][key]["attempts"][0]
        before = (self.directory / first["directory"] / "worker.log").read_bytes()
        second = self.engine()
        second.execute("render", {"test": 1})
        attempts = second.state["jobs"][key]["attempts"]
        self.assertEqual(len(attempts), 2)
        self.assertNotEqual(attempts[0]["directory"], attempts[1]["directory"])
        self.assertEqual(before, (self.directory / first["directory"] / "worker.log").read_bytes())

    def test_corrupt_cached_audio_is_rejected_instead_of_silently_regenerated(self):
        engine = self.engine()
        engine.execute("render", {"test": 1})
        job = next(iter(engine.state["jobs"].values()))
        (self.directory / job["result"]).parent.joinpath("audio.wav").write_bytes(b"corrupt")
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            self.engine().execute("render", {"test": 1})
        self.assertEqual(FakeEngine.executions, 1)

    def test_missing_cache_and_changed_sources_fail_closed(self):
        engine = self.engine()
        engine.execute("plan", {"test": 1})
        job = next(iter(engine.state["jobs"].values()))
        (self.directory / job["result"]).unlink()
        with self.assertRaises(FileNotFoundError):
            self.engine().execute("plan", {"test": 1})
        manifest = lab.read(self.directory / "experiment.json")
        manifest["sources"]["tools/score_lab.py"] = "different"
        lab.atomic(self.directory / "experiment.json", lab.encode(manifest))
        with self.assertRaisesRegex(ValueError, "fingerprints changed"):
            self.engine()

    def test_ambiguous_judge_call_never_retries_without_explicit_authorization(self):
        engine = self.engine()
        calls = []
        def adapter(request, context):
            calls.append(context["idempotency_key"])
            raise RuntimeError("TEST-ONLY lost provider response")
        engine.adapter_function = adapter
        with self.assertRaises(RuntimeError):
            engine.execute("judge", PAYLOAD)
        key = next(iter(engine.state["jobs"]))
        resumed = self.engine()
        resumed.adapter_function = adapter
        with self.assertRaises(lab.UncertainSubmission):
            resumed.execute("judge", PAYLOAD)
        self.assertEqual(len(calls), 1)
        retried = self.engine(retry=[key])
        retried.adapter_function = lambda request, context: calls.append(context["idempotency_key"]) or RESPONSE
        retried.execute("judge", PAYLOAD)
        self.assertEqual(calls[0], calls[1])
        self.assertEqual(retried.state["judgeCallsStarted"], 2)

    def test_checkpointed_provider_reply_survives_death_without_a_second_call(self):
        engine = self.engine()
        calls = []
        def adapter(request, context):
            calls.append(1)
            context["checkpoint"](RESPONSE)
            raise SimulatedDeath()
        engine.adapter_function = adapter
        with self.assertRaises(SimulatedDeath):
            engine.execute("judge", PAYLOAD)
        resumed = self.engine()
        resumed.adapter_function = lambda *_: self.fail("must reuse durable reply")
        self.assertEqual(resumed.execute("judge", PAYLOAD), RESPONSE)
        self.assertEqual(len(calls), 1)
        self.assertEqual(resumed.state["judgeCallsStarted"], 1)
        self.assertEqual(resumed.state["judgeIdentity"], ["TEST-ONLY-MOCK", "not-an-actual-judge"])

    def test_invalid_reply_is_preserved_and_requires_explicit_recovery(self):
        engine = self.engine()
        engine.adapter_function = lambda *_: {**RESPONSE, "model": "INVALID TEST"}
        with self.assertRaises(ValueError):
            engine.execute("judge", PAYLOAD)
        key = next(iter(engine.state["jobs"]))
        resumed = self.engine()
        with self.assertRaises(lab.UncertainSubmission):
            resumed.execute("judge", PAYLOAD)
        recovery = self.directory / "external-response.json"
        lab.atomic(recovery, lab.encode(RESPONSE))
        resumed.recover_response(key, recovery)
        self.assertEqual(resumed.execute("judge", PAYLOAD), RESPONSE)
        self.assertEqual(len(resumed.state["jobs"][key]["attempts"]), 2)
        self.assertEqual(resumed.state["judgeCallsStarted"], 1)

    def test_explicit_request_budget_survives_resume(self):
        engine = self.engine()
        engine.state["judgeLimit"] = 1
        engine.save()
        engine.adapter_function = lambda *_: RESPONSE
        engine.execute("judge", PAYLOAD)
        resumed = self.engine()
        resumed.adapter_function = lambda *_: self.fail("budget exhausted")
        with self.assertRaises(lab.Paused):
            resumed.execute("judge", {**PAYLOAD, "request": {"id": "second TEST"}})

    def test_lock_prevents_concurrent_writers_and_releases(self):
        with lab.RunLock(self.directory):
            with self.assertRaises(RuntimeError):
                with lab.RunLock(self.directory):
                    pass
        with lab.RunLock(self.directory):
            pass

    def test_render_chunks_only_count_new_work(self):
        engine = self.engine(max_new_renders=1)
        engine.execute("render", {"test": 1})
        engine.execute("render", {"test": 1})
        with self.assertRaises(lab.Paused):
            engine.execute("render", {"test": 2})
        resumed = self.engine(max_new_renders=1)
        resumed.execute("render", {"test": 1})
        resumed.execute("render", {"test": 2})
        self.assertEqual(FakeEngine.executions, 2)

    def test_path_escape_rejected(self):
        with self.assertRaises(ValueError):
            lab.safe(self.directory, "../other")

    def test_interrupted_atomic_write_leaves_previous_state_readable(self):
        file = self.directory / "atomic-test.json"
        lab.atomic(file, lab.encode({"value": "original"}))
        with patch.object(lab.os, "replace", side_effect=RuntimeError("TEST ONLY interrupted rename")):
            with self.assertRaises(RuntimeError):
                lab.atomic(file, lab.encode({"value": "new"}))
        self.assertEqual(lab.read(file), {"value": "original"})
        self.assertEqual(len(list(self.directory.glob("atomic-test.json.*.tmp"))), 1)

    def hard_exit(self, checkpoint):
        code = '''
import os, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from test_score_lab import FakeEngine, RESPONSE, PAYLOAD, lab
directory=Path(sys.argv[2])
with lab.RunLock(directory):
    log=lab.Invocation(directory)
    engine=FakeEngine(directory, log)
    def adapter(request, context):
        if sys.argv[3] == 'yes':
            context['checkpoint'](RESPONSE)
        os._exit(73)
    engine.adapter_function=adapter
    engine.execute('judge', PAYLOAD)
'''
        result = subprocess.run([sys.executable, "-c", code, str(Path(__file__).parent),
                                 str(self.directory), "yes" if checkpoint else "no"],
                                capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 73, result.stderr.decode(errors="replace"))

    def test_real_process_death_releases_lock_and_preserves_checkpointed_reply(self):
        self.hard_exit(checkpoint=True)
        with lab.RunLock(self.directory):
            engine = self.engine()
            engine.adapter_function = lambda *_: self.fail("hard-death recovery must not resubmit")
            self.assertEqual(engine.execute("judge", PAYLOAD), RESPONSE)
        self.assertEqual(engine.state["judgeCallsStarted"], 1)
        self.assertEqual(len(next(iter(engine.state["jobs"].values()))["attempts"]), 1)

    def test_real_process_death_without_reply_requires_reconciliation(self):
        self.hard_exit(checkpoint=False)
        with lab.RunLock(self.directory):
            engine = self.engine()
            engine.adapter_function = lambda *_: self.fail("must not resubmit an ambiguous call")
            with self.assertRaises(lab.UncertainSubmission):
                engine.execute("judge", PAYLOAD)
        self.assertEqual(engine.state["judgeCallsStarted"], 1)


@unittest.skipUnless(shutil.which("node"), "Native protocol checks require Node")
class NativeProtocolTests(unittest.TestCase):
    def setUp(self):
        root = (lab.ROOT / ".score-lab/tests").resolve()
        root.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=root)
        assert Path(self.temp.name).resolve().is_relative_to(root)
        self.addCleanup(self.temp.cleanup)
        self.directory = lab.create(Path(self.temp.name))
        self.log = lab.Invocation(self.directory)
        self.addCleanup(self.log.close)
        self.engine = lab.Engine(self.directory, self.log)

    def test_python_sorted_json_parent_round_trips_through_native_planner(self):
        probe = subprocess.run([self.engine.node, "-e", "require.resolve('playwright/package.json')"],
                               cwd=lab.ROOT, capture_output=True)
        if probe.returncode:
            self.skipTest("Planner metadata requires optional Playwright package")
        first = self.engine.execute("plan", {"experimentId": "TEST ONLY", "seed": "same",
             "budget": 2, "round": 0, "split": "development", "parent": None})
        # Python JSON encoding sorts nested genome keys, unlike the JS constructor.
        parent = json.loads(json.dumps(first["candidates"][1], sort_keys=True))
        second = self.engine.execute("plan", {"experimentId": "TEST ONLY", "seed": "same",
             "budget": 2, "round": 1, "split": "development", "parent": parent})
        self.assertEqual(second["candidates"][0]["genome"], parent["genome"])
        self.assertTrue(all(c["genome"]["scoreStyle"] == parent["genome"]["scoreStyle"]
                            for c in second["candidates"]))

    def test_per_request_bridge_uses_real_shared_verdict_validator(self):
        # Deliberately fake attachment descriptors, not an assertion of listening.
        run = {"version": "awen-score-lab-1", "id": "TEST-ONLY-NATIVE-PROTOCOL",
             "baseline": "base", "cases": [{"id": "case", "timeline": []}],
             "candidates": [{"id": "base", "eligible": True, "clips": [
                 {"caseId": "case", "file": "TEST-ONLY.wav", "sha256": "TEST-ONLY-HASH", "seconds": 58}]}]}
        request_id = "probe-" + lab.sha((run["id"] + "identical").encode())[:12]
        response = {"version": run["version"], "runId": run["id"], "model": "TEST-ONLY-MOCK",
             "modelVersion": "not-a-real-judge", "verdict": {"id": request_id, "audioHeard": True,
             "audioSha256": ["TEST-ONLY-HASH", "TEST-ONLY-HASH"], "fit": "tie", "coherence": "tie",
             "unobtrusiveness": "tie", "confidence": .9, "evidence": [
                 {"slot": slot, "start": 1, "end": 2, "observation": "TEST ONLY"} for slot in ["A", "B"]]}}
        directory = self.directory / "native-protocol"
        directory.mkdir()
        payload = {"run": run, "request": {"id": request_id}}
        self.engine.validate_response(payload, response, directory)
        response["verdict"]["audioSha256"] = ["wrong", "wrong"]
        with self.assertRaises(RuntimeError):
            self.engine.validate_response(payload, response, directory)


if __name__ == "__main__":
    unittest.main()
