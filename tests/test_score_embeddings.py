"""Dependency-free fake-vector plumbing tests; actual CLAP results are separate."""
import array
import copy
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import wave

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import score_embeddings as emb
import score_lab as lab
from clap_backend import normalized


class Death(BaseException):
    pass


class FakeBackend:
    calls = []

    def __init__(self, *_):
        pass

    def feature(self, kind, payload, pcm=None):
        key = payload["cacheKey"]
        self.calls.append(key)
        values = [0.0] * 512
        values[0] = 1 / math.sqrt(2)
        values[1 + int(key[:4], 16) % 511] = 1 / math.sqrt(2)
        return values


class EmbeddingTests(unittest.TestCase):
    def setUp(self):
        root = (lab.ROOT / ".score-lab/tests").resolve()
        root.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=root)
        assert Path(self.temp.name).resolve().is_relative_to(root)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.patch = patch.object(emb, "packages", return_value={"TEST-ONLY-PACKAGES": "no-real-model"})
        self.patch.start()
        self.addCleanup(self.patch.stop)
        FakeBackend.calls = []
        candidate = {"id": "TEST-ONLY-CANDIDATE", "eligible": True, "clips": []}
        cases = []
        for index, (case, book) in enumerate([("rat-opening", "rat"), ("riders-opening", "riders")]):
            filename = f"TEST-ONLY-{index}.wav"
            with wave.open(str(self.root / filename), "wb") as audio:
                audio.setparams((1, 2, 24000, 0, "NONE", "not compressed"))
                block = array.array("h", [0, 700 + index, 0, -700 - index])
                if sys.byteorder != "little":
                    block.byteswap()
                audio.writeframes(block.tobytes() * (24000 * 42 // 4))
            candidate["clips"].append({"caseId": case, "file": filename,
                         "sha256": lab.sha((self.root / filename).read_bytes())})
            cases.append({"id": case, "timeline": [
                {"paragraphId": f"{book}:chapter-1:{i}", "seconds": seconds}
                for i, seconds in enumerate([.12, 13.4533, 26.7867])
            ] + [{"paragraphId": f"{book}:chapter-2:0", "seconds": 40.12}]})
        self.run = self.root / "source-run.json"
        lab.atomic(self.run, lab.encode({"version": "awen-score-lab-1", "id": "TEST-ONLY",
                                        "candidates": [candidate], "cases": cases}))
        self.directory = self.create()

    def create(self):
        return emb.create(self.root / "experiments", self.run, self.root, cache=self.root / "cache")

    def engine(self, directory=None, **kwargs):
        directory = directory or self.directory
        log = lab.Invocation(directory)
        self.addCleanup(log.close)
        return emb.EmbeddingEngine(directory, log, backend_factory=FakeBackend, **kwargs)

    def test_feature_identity_uses_content_model_and_preprocessing_not_paths(self):
        manifest = lab.read(self.directory / "experiment.json")
        feature = next(f for f in manifest["features"] if f["kind"] == "audio")
        other = {**feature, "file": "somewhere-else.wav", "startFrame": 100}
        self.assertEqual(emb.feature_key(manifest["identity"], feature), emb.feature_key(manifest["identity"], other))
        identity = copy.deepcopy(manifest["identity"])
        identity["spec"]["revision"] = "different"
        self.assertNotEqual(emb.feature_key(identity, feature), feature["cacheKey"])
        changed = {**feature, "pcmSha256": "different"}
        self.assertNotEqual(emb.feature_key(manifest["identity"], changed), feature["cacheKey"])

    def test_pcm_window_and_silence_are_explicit_and_hashed(self):
        manifest = lab.read(self.directory / "experiment.json")
        for f in manifest["features"]:
            if f["kind"] == "audio":
                pcm = emb.pcm_window(self.directory, f, manifest["identity"]["spec"])
                self.assertEqual(len(pcm), 480000)
                if f["silence"]:
                    self.assertEqual(pcm, bytes(480000))

    def test_chunk_resume_and_second_resume_never_recompute_completed_features(self):
        with self.assertRaises(lab.Paused):
            self.engine(max_new=2).drive()
        before = lab.read(self.directory / "state.json")
        first_jobs = {k: j for k, j in before["jobs"].items() if j["status"] == "complete"}
        self.assertEqual(len(FakeBackend.calls), 2)
        self.engine().drive()
        after = lab.read(self.directory / "state.json")
        for key, job in first_jobs.items():
            self.assertEqual(job, after["jobs"][key])
        count = len(FakeBackend.calls)
        self.engine(max_new=0).drive()
        self.assertEqual(len(FakeBackend.calls), count)
        self.assertEqual(len(set(FakeBackend.calls)), count)
        self.assertEqual(lab.read(self.directory / "report.json")["status"], "diagnostic-only")

    def test_second_experiment_reuses_content_cache_without_loading_backend(self):
        self.engine().drive()
        count = len(FakeBackend.calls)
        other = self.create()
        engine = self.engine(other, max_new=0)
        engine.drive()
        self.assertIsNone(engine.backend)
        self.assertEqual(len(FakeBackend.calls), count)
        self.assertEqual(engine.state["computedFeatures"], 0)
        self.assertEqual(engine.state["featureCacheHits"], len(engine.manifest["features"]))

    def test_crash_after_published_feature_is_recovered(self):
        def fault(event, _):
            if event == "after_result_publish":
                raise Death()
        with self.assertRaises(Death):
            self.engine(fault_hook=fault).drive()
        first = FakeBackend.calls[0]
        self.engine().drive()
        self.assertEqual(FakeBackend.calls.count(first), 1)

    def test_corrupt_cache_is_rejected_without_recomputation(self):
        self.engine().drive()
        other = self.create()
        engine = self.engine(other)
        feature = engine.manifest["features"][0]
        cache = engine.cache_path(feature)
        result = lab.read(cache)
        result["vector"][0] += .2
        lab.atomic(cache, lab.encode(result))
        count = len(FakeBackend.calls)
        with self.assertRaises(ValueError):
            engine.drive()
        self.assertEqual(len(FakeBackend.calls), count)

    def test_changed_package_identity_blocks_resume(self):
        with patch.object(emb, "packages", return_value={"TEST-ONLY-PACKAGES": "changed"}):
            with self.assertRaisesRegex(ValueError, "identity changed"):
                self.engine()

    def test_manifest_mutation_is_detected_before_reusing_vectors(self):
        manifest = lab.read(self.directory / "experiment.json")
        manifest["features"][0]["text"] = "Different TEST ONLY text"
        lab.atomic(self.directory / "experiment.json", lab.encode(manifest))
        with self.assertRaisesRegex(ValueError, "manifest changed"):
            self.engine()

    def test_changed_source_audio_blocks_even_cached_jobs(self):
        self.engine().drive()
        manifest = lab.read(self.directory / "experiment.json")
        file = self.directory / next(iter(manifest["assets"]))
        file.write_bytes(b"corrupt TEST ONLY")
        with self.assertRaisesRegex(ValueError, "source audio changed"):
            self.engine().drive()

    def test_invalid_vectors_and_cache_paths_rejected(self):
        for vector in ([0] * 512, [float("nan")] * 512, [1, 0]):
            with self.assertRaises(ValueError):
                normalized(vector)
        with self.assertRaises(ValueError):
            self.engine().cache_path({"cacheKey": "../../outside"})

    def test_collapsed_text_tower_stops_before_audio_or_scene_scoring(self):
        class CollapsedBackend(FakeBackend):
            def feature(self, kind, payload, pcm=None):
                self.calls.append(payload["cacheKey"])
                return [1.0] + [0.0] * 511
        engine = self.engine()
        engine.factory = CollapsedBackend
        engine.drive()
        report = lab.read(self.directory / "report.json")
        self.assertEqual(report["status"], "unusable-checkpoint")
        self.assertEqual(len(FakeBackend.calls), 3)
        self.assertNotIn("rows", report)


class DiagnosticTests(unittest.TestCase):
    def test_unrelated_text_collapse_is_rejected_before_scene_evaluation(self):
        a, b, c = [1, 0, 0], [0, 1, 0], [0, 0, 1]
        self.assertTrue(emb.text_tower_sanity([a, b, c], .995)["usable"])
        self.assertFalse(emb.text_tower_sanity([a, a, a], .995)["usable"])
    def fixture(self):
        manifest = {"id": "TEST ONLY", "identity": {}, "suite": {"id": "TEST ONLY",
               "probes": [{"id": "one"}, {"id": "two"}], "limitations": []},
               "rows": [{"id": "a", "probe": "one", "cacheKey": "a"},
                        {"id": "b", "probe": "two", "cacheKey": "b"}],
               "silenceKey": "silence", "texts": [
                   {"id": key, "cacheKey": key} for key in ["one/brief", "two/brief",
                   "one/paraphrase", "two/paraphrase", "unsuitable/metal", "unsuitable/news"]]}
        a, b, c, d = [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]
        vectors = {"a": a, "b": b, "silence": c, "one/brief": a, "two/brief": b,
                   "one/paraphrase": a, "two/paraphrase": b, "unsuitable/metal": c, "unsuitable/news": d}
        return manifest, vectors

    def test_matched_shuffled_unsuitable_and_wording_are_separate(self):
        manifest, vectors = self.fixture()
        report = emb.diagnostics(manifest, vectors)
        self.assertEqual(report["summary"]["matchedPreferred"], 2)
        self.assertEqual(report["summary"]["meanMatchedMinusShuffled"], 1)
        self.assertEqual(report["summary"]["matchedAboveUnsuitable"], 2)
        self.assertIsNone(report["musicalWinner"])
        self.assertFalse(report["qualityOrReadingBenefitEstablished"])
        vectors["one/paraphrase"], vectors["two/paraphrase"] = vectors["two/paraphrase"], vectors["one/paraphrase"]
        self.assertEqual(emb.diagnostics(manifest, vectors)["summary"]["wordingSignChanges"], 2)

    def test_shuffling_audio_reverses_margin_and_constant_model_is_flagged(self):
        manifest, vectors = self.fixture()
        vectors["a"], vectors["b"] = vectors["b"], vectors["a"]
        self.assertEqual(emb.diagnostics(manifest, vectors)["summary"]["meanMatchedMinusShuffled"], -1)
        constant = {key: [1, 0, 0, 0] for key in vectors}
        report = emb.diagnostics(manifest, constant)
        self.assertTrue(report["summary"]["constantScoreMatrix"])
        self.assertEqual(report["summary"]["matchedPreferred"], 0)


if __name__ == "__main__":
    unittest.main()
