# Workflow Lifecycle

How a task contract moves through the contract -> review -> response
workflow, from `DRAFT` to `CLOSED`. The full status list lives here.
Each contract has its own directory under `docs/contract/<ID>/` holding
`contract.md`, `review.md`, and `response.md`, so multiple contracts
(e.g. AUTH-001, AUTH-002) can run in parallel. New work starts from
`docs/contract/template.md`.

## Who determines each status

Every status has exactly **one determiner** — the actor who decides the
contract is in that state and sets the `Status` field. No status is ever
"recommended"; whoever owns it applies it directly.

| Status              | Determined & set by | Meaning                                              |
| ------------------- | ------------------- | ---------------------------------------------------- |
| `DRAFT`             | Human               | Task is still being defined                          |
| `READY FOR REVIEW`  | Human               | Task definition is complete                          |
| `NEEDS HUMAN INPUT` | Agent (generic)     | Open P0/P1/P2 findings, or a human decision is required |
| `READY FOR APPROVAL`| Agent (generic)     | Work + tests complete; most or all severities addressed |
| `CLOSED`            | Human               | Human accepted the implementation                    |

- The **human** owns `DRAFT`, `READY FOR REVIEW`, and `CLOSED`.
- The two middle statuses are **agent-owned** and generic — any acting
  agent (reviewer or implementer) sets them depending on the situation:
  - **NEEDS HUMAN INPUT** — the reviewer sets it when a review leaves
    open P0/P1/P2 findings; the implementer sets it when it hits an
    ambiguity or decision only the human can make.
  - **READY FOR APPROVAL** — the implementer sets it once the work and
    tests are complete; the reviewer sets it when a re-review confirms
    most or all severities are addressed (no open P0/P1; P2s resolved
    or consciously waived).

## The flow

1. **DRAFT** — the human edits the contract (Problem, Desired Outcome,
   Requirements, Constraints, Acceptance Criteria) until the task is
   well-defined.
2. **READY FOR REVIEW** — the human sends the contract to the Reviewer.
3. **NEEDS HUMAN INPUT** — the Reviewer writes
   `docs/contract/<ID>/review.md` and sets the contract to this
   status whenever any P0/P1/P2 findings are open or a human decision is
   required (the normal outcome of a review with unresolved findings).
   The human resolves the decisions and updates the contract.
4. **READY FOR APPROVAL** — the Implementer addresses the findings and
   completes the work and tests, and the Reviewer re-runs the review.
   Once most or all severities are addressed, the acting agent sets this
   status. The human performs the final review.
5. **CLOSED** — the human accepted the implementation and sets the
   terminal status.

An agent cannot leave a contract in `READY FOR REVIEW`; after a review
the contract must move to `NEEDS HUMAN INPUT` (if findings remain) or on
to `READY FOR APPROVAL` (if they are addressed).

## What happens when a contract is CLOSED

`CLOSED` is a terminal state. When the human sets it:

- **The implementation is accepted.** No further reviewer or implementer
  work happens on this contract — it is done.
- **The human merges/finishes the work** per the repo's Git Rules in
  `AGENTS.md`: merge the feature branch into `main`; do not force push or
  rewrite history. "Finish" may also include tagging or deleting the
  branch.
- **The audit trail stays on record.** The contract, its review
  (`docs/contract/<ID>/contract.md`), review (`review.md`), and response
  (`response.md`) remain in the repo as the permanent record of what was
  agreed, found, and resolved.
- **A new piece of work starts a new contract** with a new `Contract ID`
  and its own status — it does not reopen the closed one.

Closed contracts are never reopened. If the same area needs more work
later, that is a new contract.
