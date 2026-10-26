# Resumable Python audio evaluation

The Python layer orchestrates development experiments and provider adapters; the real native Web Audio engine and shared JavaScript metrics still render/evaluate the clips. The finished `index.html` is unchanged. Python itself needs only its standard library (3.10+); the renderer needs Node and the same optional Playwright setup documented in README. No provider, model download or upload is enabled by default.

## Start, inspect and resume

```sh
python tools/score_lab.py start --budget 2 --seed trial-001
python tools/score_lab.py status /absolute/path/printed-by-start
python tools/score_lab.py resume /absolute/path/printed-by-start
```

Every start creates a fresh UTC timestamp + UUID directory under `.score-lab/python/`. The full experiment path is printed before work begins. Each invocation has its own timestamp/UUID JSONL log; each job attempt has a new directory and worker/adapter logs. All raw experiment data stays ignored by Git. Resuming preserves previous attempts and appends new ones rather than replacing their logs.

`--root` changes the parent output location. `--node` selects a Node executable. `AWEN_BROWSER_CHANNEL` and `NODE_PATH` work as in the existing lab; testing uses an isolated headless browser profile. No microphone or user Chrome session is involved.

For bounded work chunks:

```sh
python tools/score_lab.py start --budget 2 --max-new-renders 1
python tools/score_lab.py resume /path/to/experiment --max-new-renders 1
```

Only newly rendered clips count toward that invocation's limit. Completed jobs are verified and reused. Missing/corrupt completed artifacts are reported rather than silently replaced. Interrupted local renders without a complete result can retry in a fresh attempt directory; partial artifacts remain archived. A surviving orphaned local renderer may finish its old attempt, but it cannot overwrite a resumed attempt's outputs.

An OS file lock prevents two writers from driving the same experiment and releases on process exit/death. State and results are atomically published with file flush/fsync before replacement. A crash after result publication but before state commit is recovered by checking the durable result. A crash during writing leaves a unique temporary file and the previous state. This relies on ordinary local filesystem atomic-rename/locking behaviour; it is not a distributed/cloud-storage coordination protocol.

Source, fixture, metric, rubric and orchestrator hashes are pinned. An experiment refuses to resume against changed code; create a fresh run when deliberately changing the experiment. Renderer versions are checked across clips, and the judge model/deployment is kept consistent. Do not edit archived manifests to bypass those checks. The original JavaScript-only CLI remains available; use this Python entry point when resumability is required.

## Optional Python audio judge

```sh
python tools/score_lab.py resume /path/to/experiment --judge-adapter /absolute/path/provider_adapter.py
```

A trusted local adapter exports a synchronous `judge(request, context)` function. It gets one blinded request at a time, not private recipe metadata. The `request` contains A/B file paths relative to `context['directory']`, exact audio hashes, durations, text timeline and whether audio is available. The adapter must actually attach those WAVs to an audio-capable model and use `context['instructions']`. The [judge rubric](score-lab-judge.md) still applies.

The function returns one response envelope:

```python
{
    "version": context["version"],
    "runId": context["run_id"],
    "model": "actual-provider/model",
    "modelVersion": "actual-pinned-version-or-deployment",
    "verdict": {
        # One verdict in the format documented in score-lab-judge.md:
        # id, audioHeard, audioSha256, fit, coherence,
        # unobtrusiveness, confidence, evidence
    },
    # Optional provenance/usage fields are retained in the raw response.
}
```

Call `context['checkpoint'](response)` as soon as a complete response is obtained, then return that same immutable response. The raw response is durably saved before validation, and the shared JavaScript validator checks exact attachments, request identity, evidence and values. Raw invalid responses remain archived for inspection. Model identity must agree across requests. This interface supports Python SDK/ML libraries without making them mandatory dependencies of the orchestrator.

The context also supplies a stable `idempotency_key`, logical `job_id` and unique `attempt_id`. Forward the key to providers that support request deduplication; it is not a guarantee that an arbitrary provider honours it. Keep API keys in environment/provider credential stores, not response objects or logs. Adapter code is trusted developer code and its prints/errors go to its private attempt log; the orchestrator does not log environment variables or credentials. Imported adapter code is pinned by hash, but transitive libraries/provider configuration still need recording by the adapter.

## Ambiguous provider calls and failed runs

The runner records an in-flight submission and increments the request budget *before* invoking a provider adapter. If a durable response/result exists after a crash, resume reuses it without a provider call. If there is no durable response, the provider may already have processed/billed it. The runner stops instead of automatically resubmitting. This is intentionally conservative even if the exception happened before a provider received anything.

Inspect `status` and the unique attempt logs. If the provider can recover the original response, place it in the response-envelope format above and reconcile it:

```sh
python tools/score_lab.py recover-response /path/to/experiment --job judge-JOB_ID --response recovered.json
python tools/score_lab.py resume /path/to/experiment
```

Reconciliation archives a fresh attempt and validates the recovered response; it does not overwrite the failed attempt or increment provider-call usage. If recovery is impossible and a repeat request is intended:

```sh
python tools/score_lab.py resume /path/to/experiment --retry-uncertain judge-JOB_ID
```

Retries preserve the logical idempotency key and consume another request-budget slot. Exactly-once external execution cannot be promised without provider support. There are no automatic provider retries hidden in the orchestrator; an adapter must document any it performs itself and its cost policy. An invalid response can likewise be reconciled or explicitly retried; it is not silently regenerated until it passes.

`--judge-requests N` sets a persistent adapter-call cap when starting (default 14 × configured rounds). `resume --add-judge-requests N` explicitly increases it, with an absolute cap of 100. These are request counts, not a dollar ceiling: provider tokens, durations and prices vary, and the adapter must enforce its own monetary budget. `--budget` stays 2–4 candidates and `--rounds` stays 1–3. Without a judge, the run stops at `awaiting-audio-judge`; it never invents a preference from signal statistics. Supported improvement can produce a proposal, with listener/held-out acceptance still required and no automatic change to the reader.

## Verification and follow-ups

```sh
python -m unittest discover -s tests -p test_score_lab.py -v
node --test tests/mvp.test.cjs tests/score-lab.test.cjs
```

Python failure tests use explicitly labelled fake worker/provider results and include real `os._exit` child-process deaths. They check unique logs, completed-cache reuse, atomic-write interruption, corrupted artifacts, new attempts for failed local work, locks, request budgets, response reconciliation and ambiguous-submission refusal. Native renderer smoke checks are separate; no fake verdict is evidence of actual music judgement.

The [recorded native smoke proof](score-lab-python-proof.json) has two candidates across two development cases: pause after one clip, resume the remaining three, then resume again with no new renders. The first completed job stays unchanged, all four render jobs have one attempt, the three invocation logs are distinct, and no provider calls were made. Python-sorted proposal JSON is also tested against the shared planner/holdout validation. Accepted proposals retain the existing format for the separate JavaScript `holdout` command; the usual unseen-work/listener gates still apply.

Pretrained embedding diagnostics and aligned film/radio/silent-cinema reference material are parked in [the research backlog](audio-text-evaluation.md). No embeddings, corpus or model training has been added to this bridge.
