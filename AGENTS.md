# Working in Awen

## Task tracking

Use Beads (`bd`) for active task tracking. Run `bd ready` to find unblocked work
and `bd show <id>` to read its scope. Mark work `in_progress` before implementation
and close it only after relevant validation. `TODO.md` is the historical roadmap;
the Beads issues hold current status. Do not recreate its tasks on each session.

Before finishing a session that changes issues, run
`bd export -o .beads/issues.jsonl` so the repo snapshot is current. JSONL preserves
issue records for interchange/recovery, not full Dolt history. Keep database,
locks and runtime files ignored. Do not run remote Dolt sync or Git publication
without user authorization. Local Dolt issue commits are separate from Git commits.

## Implementation constraints

Keep the runnable app in `index.html` with inline JavaScript/CSS, no React or
required build step, and minimal dependencies. The embedded books occupy a very
large JSON line: avoid printing it in tool output. Prefer scoped searches or
extract the application script when inspecting code.

Preserve musical continuity and the final shared output limiter for all audio
paths, including previews. Do not add cloud/LLM processing to ordinary reading
or preference evolution. The current renderer is native Web Audio; Strudel is
an optional research direction, not a required migration.

Run `node --test tests/mvp.test.cjs` for relevant logic changes. Use the isolated
Playwright suites for audio/UI changes (`tests/audio.browser.cjs` and
`tests/evolution.browser.cjs`); they are test-only dependencies. Do not claim
audible artistic quality from automated sample checks alone.
