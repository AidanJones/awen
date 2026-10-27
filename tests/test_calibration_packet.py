"""Packet/label contract checks with explicitly synthetic audio and TEST ONLY ratings."""
import array
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import wave

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import calibration_packet as cal
import score_lab as lab


class FakeRenderEngine(cal.CalibrationEngine):
    renders = 0

    def worker(self, command, input_path, output_path, log_path):
        if self.reuse_current:
            return super().worker(command, input_path, output_path, log_path)
        type(self).renders += 1
        wav, trace = b"TEST ONLY NATIVE CACHE", b'{"TEST_ONLY":true}\n'
        lab.atomic(output_path.parent / "audio.wav", wav, exclusive=True)
        lab.atomic(output_path.parent / "trace.json", trace, exclusive=True)
        result = {"file": "audio.wav", "sha256": lab.sha(wav), "traceFile": "trace.json",
                  "traceSha256": lab.sha(trace), "renderer": {"browser": "TEST ONLY"}}
        lab.atomic(log_path, b"TEST ONLY worker\n", exclusive=True)
        lab.atomic(output_path, lab.encode({"requestSha256": lab.sha(input_path.read_bytes()), "result": result}), exclusive=True)


class PacketTests(unittest.TestCase):
    def setUp(self):
        root = (lab.ROOT / ".score-lab/tests").resolve()
        root.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=root)
        assert Path(self.temp.name).resolve().is_relative_to(root)
        self.addCleanup(self.temp.cleanup)
        self.directory = cal.create(Path(self.temp.name), "TEST-ONLY-SEED")
        self.manifest = lab.read(self.directory / "experiment.json")
        self.plan = {"id": "TEST-ONLY-PLAN", "suite": {"holdoutBooks": ["war"]}, "scenes": []}
        self.renders = {}
        for c in range(3):
            file = self.directory / f"native-{c}.wav"
            block = array.array("h", [0, 900 + c * 50, 0, -900 - c * 50])
            if sys.byteorder != "little":
                block.byteswap()
            with wave.open(str(file), "wb") as audio:
                audio.setparams((1, 2, 24000, 0, "NONE", "not compressed"))
                audio.writeframes(block.tobytes() * 2400)
        for i in range(6):
            book = ["rat", "riders", "time"][i // 2]
            scene = {"id": f"TEST-ONLY-scene-{i}", "selectionNote": "PRIVATE TEST NOTE",
                "book": {"id": book, "title": "TEST ONLY BOOK", "author": "TEST ONLY AUTHOR",
                         "url": "https://standardebooks.org/", "revision": "TEST ONLY", "license": "TEST ONLY"},
                "chapter": {"id": "chapter", "title": "TEST ONLY"},
                "current": {"paragraphId": f"{book}:chapter:0", "text": "TEST ONLY </script><script>throw 'bad'</script>"},
                "previous": None, "crop": {"startFrame": 100, "frameCount": 8000},
                "candidates": [{"id": f"TEST-ONLY-c-{c}", "genome": {"private-trait": c}, "palette": "PRIVATE"} for c in range(3)]}
            self.plan["scenes"].append(scene)
            for c, candidate in enumerate(scene["candidates"]):
                file = self.directory / f"native-{c}.wav"
                self.renders[(scene["id"], candidate["id"])] = {"file": file.name,
                    "sha256": lab.sha(file.read_bytes()), "gate": {"eligible": True}}
        self.proof = cal.build_packet(self.directory, self.manifest, self.plan, self.renders)
        self.packet = lab.read(self.directory / "public/packet.json")
        self.key = lab.read(self.directory / "private-key.json")

    def labels(self, trial=None):
        trial = trial or next(t["id"] for t in self.key["trials"] if t["kind"] == "primary")
        return {"version": cal.LABEL_VERSION, "packetId": self.packet["id"], "packetSha256": self.key["packetSha256"],
                "rater": {"id": "TEST-ONLY-RATER", "kind": "human"}, "responses": [{
                "trialId": trial, "revision": 1, "at": "2026-10-27T12:00:00Z", "fit": "A",
                "enjoyment": "B", "lessDistracting": "tie", "heardBoth": True,
                "confidence": "medium", "notes": "TEST ONLY; not a human judgement",
                "playedSeconds": {"A": 2, "B": 2}}]}

    def imported(self, data):
        file = self.directory / ("TEST-ONLY-labels-" + __import__('uuid').uuid4().hex + ".json")
        lab.atomic(file, lab.encode(data))
        return cal.import_labels(self.directory, file)

    def test_six_scenes_eighteen_trials_with_private_key_and_no_gold_winner(self):
        self.assertEqual(self.proof["scenes"], 6)
        self.assertEqual(self.proof["trials"], 18)
        kinds = [t["kind"] for t in self.key["trials"]]
        self.assertEqual(kinds.count("primary"), 12)
        self.assertEqual(kinds.count("swapped"), 3)
        self.assertEqual(kinds.count("identical"), 3)
        self.assertEqual(self.proof["humanLabels"], 0)
        self.assertEqual(len({t["id"] for t in self.packet["trials"]}), 18)
        raw = json.dumps(self.packet)
        for secret in ["PRIVATE", "genome", "palette", "selectionNote", "TEST-ONLY-c-"]:
            self.assertNotIn(secret, raw)
        self.assertNotIn("<script>throw 'bad'", (self.directory / "public/review.html").read_text(encoding="utf-8"))

    def test_balance_only_attenuates_and_shared_output_cap_survives_pcm_export(self):
        for scene in self.key["scenes"]:
            levels = [c["postGainRms"] for c in scene["clips"]]
            self.assertLess(max(levels) - min(levels), 1e-12)
            for clip in scene["clips"]:
                self.assertLessEqual(clip["gain"], 1)
                self.assertLessEqual(clip["peak"], .140001)
                file = self.directory / "public" / clip["descriptor"]["file"]
                self.assertEqual(lab.sha(file.read_bytes()), clip["descriptor"]["sha256"])
        self.assertEqual(self.proof, cal.build_packet(self.directory, self.manifest, self.plan, self.renders))

    def test_duplicate_exports_do_not_duplicate_observations(self):
        data = self.labels()
        a, b = self.imported(data), self.imported(data)
        self.assertNotEqual(a, b)
        result = cal.summary(self.directory)
        self.assertEqual(result["importedResponsesAfterDeduplication"], 1)
        self.assertEqual(len(result["primaryPairs"]), 1)
        self.assertNotEqual(result["primaryPairs"][0]["fit"], result["primaryPairs"][0]["enjoyment"])
        self.assertFalse(result["rewardCalibrated"])

    def test_newer_revision_replaces_label_while_raw_imports_remain(self):
        data = self.labels()
        first = self.imported(data)
        data["responses"][0].update(revision=2, fit="B")
        self.imported(data)
        result = cal.summary(self.directory)
        self.assertEqual(result["primaryPairs"][0]["revision"], 2)
        self.assertTrue((first / "labels.json").exists())

    def test_conflicting_same_revision_is_flagged_and_excluded(self):
        data = self.labels()
        self.imported(data)
        data["responses"][0]["fit"] = "B"
        self.imported(data)
        result = cal.summary(self.directory)
        self.assertEqual(len(result["revisionConflicts"]), 1)
        self.assertEqual(result["primaryPairs"], [])

    def test_missing_listening_is_preserved_but_not_treated_as_preference(self):
        data = self.labels()
        data["responses"][0]["heardBoth"] = False
        self.imported(data)
        result = cal.summary(self.directory)
        self.assertEqual(result["notHeardBoth"], 1)
        self.assertEqual(result["primaryPairs"], [])

    def test_controls_are_not_training_observations_and_swaps_use_candidate_identity(self):
        swapped = next(t for t in self.key["trials"] if t["kind"] == "swapped")
        primary = next(t for t in self.key["trials"] if t["kind"] == "primary" and t["pair"] == swapped["pair"])
        data = self.labels(primary["id"])
        other = copy.deepcopy(data["responses"][0]);other.update(trialId=swapped["id"], fit="B", enjoyment="A")
        data["responses"].append(other)
        identity = next(t for t in self.key["trials"] if t["kind"] == "identical")
        control = copy.deepcopy(other);control.update(trialId=identity["id"], fit="tie", enjoyment="tie")
        data["responses"].append(control)
        self.imported(data)
        result = cal.summary(self.directory)
        self.assertEqual(result["swappedControls"]["fit"]["consistent"], 1)
        self.assertEqual(result["identicalControls"]["fit"]["tie"], 1)
        self.assertEqual(len(result["primaryPairs"]), 1)

    def test_bad_label_contracts_are_rejected_before_import(self):
        for mutate in [lambda d:d.update(packetId="wrong"), lambda d:d.update(packetSha256="wrong"),
             lambda d:d["responses"].append(d["responses"][0]), lambda d:d["responses"][0].update(fit="C"),
             lambda d:d["responses"][0].update(revision=True), lambda d:d["responses"][0].update(at="not-a-date"),
             lambda d:d["responses"][0].update(playedSeconds={"A":float('nan'),"B":0}),
             lambda d:d["rater"].update(kind="model")]:
            data = self.labels();mutate(data)
            with self.assertRaises(ValueError):
                cal.validate_labels(self.directory, data)

    def test_changed_public_packet_and_failed_engineering_gate_cannot_be_used(self):
        file = self.directory / "public/packet.json"
        original = file.read_bytes()
        file.write_bytes(original+b" ")
        with self.assertRaises(ValueError):
            cal.validate_labels(self.directory, self.labels())
        file.write_bytes(original)
        render = next(iter(self.renders.values()))
        render["gate"]["eligible"] = False
        with self.assertRaises(ValueError):
            cal.build_packet(self.directory, self.manifest, self.plan, self.renders)

    def test_archived_import_checksum_is_verified(self):
        imported = self.imported(self.labels())
        file = imported / "labels.json"
        file.write_bytes(file.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "import changed"):
            cal.summary(self.directory)

    def test_verified_render_reuse_needs_no_new_budget_and_becomes_self_contained(self):
        FakeRenderEngine.renders = 0
        source = cal.create(Path(self.temp.name) / "render-source", "TEST ONLY")
        source_log = lab.Invocation(source);self.addCleanup(source_log.close)
        first = FakeRenderEngine(source, source_log, node=sys.executable)
        payload = {"TEST_ONLY_INPUT": "same"}
        first.execute("render", payload)
        destination = cal.create(Path(self.temp.name) / "render-destination", "TEST ONLY", source)
        log = lab.Invocation(destination);self.addCleanup(log.close)
        second = FakeRenderEngine(destination, log, node=sys.executable, max_new_renders=0)
        result = second.execute("render", payload)
        self.assertIn("reusedFrom", result)
        self.assertEqual(second.new_renders, 0)
        self.assertEqual(FakeRenderEngine.renders, 1)
        again = FakeRenderEngine(destination, log, node=sys.executable, max_new_renders=0)
        again.reuse_source = destination / "nonexistent-source"
        self.assertEqual(result, again.execute("render", payload))
        self.assertEqual(FakeRenderEngine.renders, 1)
        with self.assertRaises(lab.Paused):
            second.execute("render", {"TEST_ONLY_INPUT": "different"})

    def test_corrupt_render_reuse_cannot_be_silently_accepted(self):
        source = cal.create(Path(self.temp.name) / "bad-source", "TEST ONLY")
        log = lab.Invocation(source);self.addCleanup(log.close)
        first = FakeRenderEngine(source, log, node=sys.executable)
        payload = {"TEST_ONLY_INPUT": "same"}
        first.execute("render", payload)
        job = next(iter(first.state["jobs"].values()))
        (source / job["result"]).parent.joinpath("audio.wav").write_bytes(b"corrupt")
        target = cal.create(Path(self.temp.name) / "bad-destination", "TEST ONLY", source)
        next_log = lab.Invocation(target);self.addCleanup(next_log.close)
        with self.assertRaisesRegex(ValueError, "artifact changed"):
            FakeRenderEngine(target, next_log, node=sys.executable, max_new_renders=0).execute("render", payload)


@unittest.skipUnless(shutil.which("node"), "Planner requires Node")
class NativePlanTests(unittest.TestCase):
    def test_six_native_scene_plans_keep_war_held_out_and_validate_three_alternatives(self):
        script = "const p=require('./tools/calibration-worker.cjs').plan({experimentId:'TEST ONLY',seed:'test'}); console.log(JSON.stringify(p));"
        result = subprocess.run([shutil.which("node"), "-e", script], cwd=lab.ROOT, capture_output=True)
        if result.returncode and b"Cannot find module" in result.stderr:
            self.skipTest("Optional Playwright package unavailable for planner metadata")
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        plan = json.loads(result.stdout)
        self.assertEqual(len(plan["scenes"]), 6)
        self.assertNotIn("war", [s["book"]["id"] for s in plan["scenes"]])
        self.assertEqual({s["book"]["id"] for s in plan["scenes"]}, {"rat", "riders", "time"})
        for scene in plan["scenes"]:
            self.assertEqual(len({c["id"] for c in scene["candidates"]}), 3)
            self.assertEqual(scene["crop"]["frameCount"], 640000)
            self.assertTrue(scene["current"]["text"])


if __name__ == "__main__":
    unittest.main()
