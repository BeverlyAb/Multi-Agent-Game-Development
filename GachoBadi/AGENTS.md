# AGENTS.md

## Project

This repository contains **Gachō Badi (Goose Buddy)** — a goal-oriented
coding agent built on top of a multi-agent game. A 13-agent Python 3 crew
generates game content; a verification workflow reads the game design doc
(docs/gdd.txt), detects where an agent's output drifts from
what the GDD requires, and rewrites that agent's constraint configuration
until the drift is gone. See `Readme.md` for the full overview.

## Architecture

Python 3 pipeline, stdlib only — no framework, no server, no database.
A `GachoBadiCrew` orchestrates 13 `BaseAgent` implementations that call a
shared LLM client (Anthropic → OpenAI → deterministic mock fallback) and
exchange shared data models; a verification layer wraps the highest-risk
agents; a Phaser 3 client renders the generated content.

See:
- docs/architecture/architecture.md
- docs/domain-models.md
- docs/cli.md

Read the relevant document before making architectural changes. See
docs/contract/ for the contract -> review -> response workflow, with one
directory per Contract ID (`docs/contract/<ID>/contract.md`,
`review.md`, `response.md`). docs/workflow-lifecycle.md defines the
contract statuses and what happens when one is CLOSED, and
docs/finding-severity.md covers how review findings are classified
(P0-P3) and numbered (P<n>-<NNN>).

## Important Directories

    agents/            Agent implementations (runtime + dev_time)
    api/               LLM client layer
    definitions/       Shared domain data models
    executable/        Crew orchestration + entry point
    workflow/          Verification / constraints / goal-oriented agent
    web/               Phaser 3 client
    output/crew/       Generated game content + manifest.json
    docs/              Project documentation
    src/               (placeholder) application source
    tests/             (placeholder) automated tests
    docs/              Project documentation
    docs/architecture/ Architecture docs
    docs/contract/     Per-ID contract dirs (docs/contract/<ID>/contract.md, review.md, response.md)

## Development

See:
- docs/development.md

Install dependencies before making changes. All commands run from
`GachoBadi/`.

    python3 executable/main.py                  # full game run
    python3 workflow/generic/demo_verify.py     # verification demo (smoke test)

There are no automated test suites; the verification demo is the project's
test harness.

## Coding Rules

- Follow existing coding conventions.
- Prefer small changes over broad rewrites.
- Do not modify unrelated files.
- Do not introduce dependencies without justification (project runs
  stdlib-only).
- Add verification for bug fixes (the constraint/guardrail layer is the
  test harness).
- Preserve public API compatibility.
- Agents must never invent verbs or outcomes outside what the Item
  Interaction Agent registered.
- Keep `workflow/generic/` agent-agnostic; domain-specific gap detection
  goes in `workflow/constraints/<agent>/`.
- Values in `constraints.yaml`, logic in `constraints.py`.
- Do not overwrite `constraints.yaml.orig` backups.
- Every agent call supplies a `fallback` string; the crew must never
  crash without producing output.

## Git Rules

- Do not commit directly to main.
- Work on a feature branch (e.g. `ollama`, `goal_oriented_agent`).
- Do not force push.
- Do not rewrite existing commit history.

## Before Completing a Task

1. Run the verification demo: `python3 workflow/generic/demo_verify.py --agents all` (and the affected agent's goal loop if you touched `workflow/`).
2. Run the full game: `python3 executable/main.py`.
3. Review git diff (restore regenerated `workflow/logs/*.jsonl` if the run wasn't the point of the change).
4. Report tests that failed.
5. Do not claim tests passed unless they were actually run.

## Governance

AGENTS.md defines repository-wide agent policy.

Agents must not modify AGENTS.md unless explicitly instructed
by the human repository owner.

If an agent believes AGENTS.md should change, it must report
the proposed change separately.

Task-specific findings belong in review or planning documents,
not AGENTS.md.

## Reviewer-Implementer Specific Tasks
Reviewer owns:
  docs/contract/<ID>/review.md

Implementer owns:
  source changes
  test changes
  implementation commits
  docs/contract/<ID>/response.md

Human owns:
  AGENTS.md / governance