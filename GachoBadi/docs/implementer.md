# Implementer Guide

This document defines the **implementer** role for the GachoBadi contract workflow. A separate device/session acts as the **reviewer**. The human owns governance (AGENTS.md) and final approval (CLOSED status).

## Role

The implementer:
1. Reads the contract (`docs/contract/<ID>/contract.md`) and the review (`docs/contract/<ID>/review.md`)
2. Addresses all review findings (P0–P3)
3. Makes source and test changes required by the contract
4. Writes the response (`docs/contract/<ID>/response.md`)
5. Runs verification and the full game before marking work complete
6. Sets contract status to `READY FOR APPROVAL` when work is done, or `NEEDS HUMAN INPUT` if blocked

## Workflow

### 1. Receive contract

The human sets status to `READY FOR REVIEW` and sends the contract directory to the reviewer. The reviewer writes `review.md`, then sets status to `NEEDS HUMAN INPUT` (with any open P0/P1/P2 findings or required human decisions). The implementer reads the review and begins work.

### 2. Read contract and review

- Read `docs/contract/<ID>/contract.md` — understand Problem, Desired Outcome, Requirements, Constraints, Acceptance Criteria.
- Read `docs/contract/<ID>/review.md` — understand every finding (P0–P3), its severity, and what must change.

### 3. Address findings

| Severity | Action |
|----------|--------|
| P0 | Must fix before anything else. Blocker. |
| P1 | Must fix. Blocker. |
| P2 | Fix unless there is a documented reason not to. |
| P3 | Fix at discretion. |

Do not renumber findings. Reference them by id (e.g. `P1-001`) in the response.

### 4. Implement changes

Follow AGENTS.md coding rules:
- Small, focused changes over broad rewrites.
- Do not modify unrelated files.
- No new dependencies (stdlib only).
- Preserve public API compatibility.
- Every agent call must supply a `fallback` string.

Work on the feature branch. Do not commit to main.

### 5. Verify

Run from `GachoBadi/`:

```
python3 workflow/generic/demo_verify.py --agents all
python3 executable/main.py
```

If `workflow/` changed, also run the affected agent's goal loop. Review `git diff`. Restore regenerated `workflow/logs/*.jsonl` if the run wasn't the point of the change.

### 6. Write response

Create or update `docs/contract/<ID>/response.md` with:

- **Findings addressed** table: each finding id, disposition (fixed / won't fix / needs discussion), and notes.
- **Execution log**: what was done per requirement.
- **Acceptance runs**: exact commands and exit codes.

### 7. Set status

- If all P0/P1 are resolved and work is complete → set status to `READY FOR APPROVAL`. The reviewer will then re-review. If the reviewer finds remaining issues, they set `NEEDS HUMAN INPUT` and the cycle repeats (steps 3–7).
- If blocked on a human decision → set status to `NEEDS HUMAN INPUT` and document what is needed.

## Communication with reviewer

The reviewer is on a separate device. Communication happens through the contract directory:

- The reviewer writes findings in `review.md`.
- The implementer writes the response in `response.md`.
- Either agent may update `contract.md` status within their authority (see Workflow Lifecycle below).
- If the reviewer re-reviews and finds remaining issues, the cycle repeats: review → response → re-review.

### Workflow Lifecycle (status authority)

Per `docs/workflow-lifecycle.md`, each status has exactly one determiner:

| Status              | Set by            | When                                              |
| ------------------- | ----------------- | ------------------------------------------------- |
| `DRAFT`             | Human             | Task is still being defined                       |
| `READY FOR REVIEW`  | Human             | Task definition is complete; sent to reviewer      |
| `NEEDS HUMAN INPUT` | Implementer       | Blocked on a human decision                       |
| `NEEDS HUMAN INPUT` | Reviewer          | Open P0/P1/P2 findings remain after review         |
| `READY FOR APPROVAL`| Implementer       | Work + tests complete; all findings addressed      |
| `READY FOR APPROVAL`| Reviewer          | Re-review confirms most/all severities addressed   |
| `CLOSED`            | Human             | Human accepted the implementation                  |

## Response format

See `docs/contract/AUTH-001/response.md` for a complete example.

```markdown
# Response: <contract-name>

## Findings addressed

| Finding | Disposition | Notes |
|---|---|---|
| P1-001 | fixed | ... |
| P2-001 | won't fix | Reason: ... |
| P3-001 | fixed | ... |

## Execution log

- **Requirement 1** — description of what was done.
- **Requirement 2** — description of what was done.

## Acceptance runs

- `python3 workflow/generic/demo_verify.py --agents all` → exit 0.
- `python3 executable/main.py` → exit 0.
```

## Rules

- Do not claim tests passed unless they were actually run.
- Do not modify AGENTS.md.
- Do not overwrite `constraints.yaml.orig` backups.
- Keep `workflow/generic/` agent-agnostic; domain-specific logic goes in `workflow/constraints/<agent>/`.
- Values in `constraints.yaml`, logic in `constraints.py`.
