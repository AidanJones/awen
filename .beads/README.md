# Beads in Awen

Beads 1.3.1 is initialised with prefix `awen` and an embedded Dolt database.
No external server is needed. This project has been worked on only on this machine.

## Everyday workflow

```sh
bd ready
bd show awen-3fr.1
bd update awen-3fr.1 --status in_progress
bd close awen-3fr.1 --reason "Implemented and validated"
bd export -o .beads/issues.jsonl
```

Create new tasks with `bd create --title "..." --description "..." --type task --priority 2`.
Add a blocker with `bd dep add <dependent> <prerequisite>`.
`bd list --status open` shows the backlog; `bd blocked` shows blocked work.
Priorities are 0–4, with 1 used for the current personal-evolution direction.

## Migrated roadmap

The original open items from TODO.md are captured in these epics and their children.
TODO.md remains a design snapshot; Beads holds live status. Stable roadmap codes
such as EVO-01 and MUSIC-02 remain in the relevant issue titles. The mapping in
`backlog-map.json` also includes section/item references for tasks without codes.

| Epic | Strand |
|---|---|
| `awen-3fr` | 1. Personal evolution: highest priority |
| `awen-7x1` | 2. Better starting music |
| `awen-6c9` | 3. Profiles and repo storage |
| `awen-xfp` | 4. Narrative interpretation without a large model |
| `awen-syq` | 5. Audio engine and interactive-score research |
| `awen-r42` | 6. Listening evaluation and engineering acceptance |
| `awen-opp` | 7. Reader and longer-term deployment |

Start with **awen-3fr.1 — EVO-01: a gallery with a wider choice**. Wider/narrower
mutation controls and the gallery comparison/replay work depend on that first slice.
Research tasks are otherwise available independently. Completed MVP features were
not recreated as open tasks.

## What is saved in Git

- `config.yaml`, `metadata.json`, the ignore rules and these instructions.
- `issues.jsonl`, an explicit export of issue records, dependencies and comments.
- `backlog-map.json`, links from the migrated roadmap to the created issue IDs.

The embedded Dolt database and runtime/lock files are ignored. Auto-export is
enabled but throttled; run the explicit export before a Git commit to guarantee
freshness. Auto-staging and automatic remote pushing are disabled. No Git hooks
were installed. Repo-local `AGENTS.md` describes the agent workflow.

A Git push carries the issue export, not full Dolt history. For a fresh clone or
recovery without the local database, initialise a fresh embedded database with
`bd init --prefix awen --non-interactive --skip-hooks --skip-agents`, then import
`bd import -i .beads/issues.jsonl`. Preserve a copy of the export before init and
do not reinitialise an existing working database. Full-history backup/replication
is a separate optional `bd backup` / Dolt-remote workflow.

An origin Dolt remote was inferred during init. Its remote history was not checked
because SSH failed inside the sandbox; this did not prevent the fresh local setup.
Only the normal Git project/export is published in this setup; a Dolt remote push
has not been performed.
