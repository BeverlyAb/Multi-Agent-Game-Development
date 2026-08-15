# Workflow Lifecycle

How a task contract moves through the contract -> review -> response
workflow, from `DRAFT` to `CLOSED`. The full status list lives here;
`docs/contract/auth-refactor.md` just points at it.

## Statuses

Only the human owner sets a contract's `Status`. Agents never change it.

| Status             | Meaning                                               | Human action                                |
| ------------------ | ----------------------------------------------------- | ------------------------------------------- |
| `DRAFT`            | Task is still being defined                           | Edit requirements/criteria                  |
| `READY FOR REVIEW` | Task definition is complete                           | Send to Reviewer                            |
| `NEEDS HUMAN INPUT`| Reviewer/Implementer found an ambiguity or decision   | Resolve it and update task                  |
| `READY FOR APPROVAL`| Implementation and AI review are complete            | Perform final human review                  |
| `CLOSED`           | Human accepted the implementation                     | Merge/finish                                |

## The flow

1. **DRAFT** — the human edits the contract (Problem, Desired Outcome,
   Requirements, Constraints, Acceptance Criteria) until the task is
   well-defined.
2. **READY FOR REVIEW** — the human sends the contract to the Reviewer.
   The Reviewer writes `docs/agent-reviews/review-<name>.md`, classifying
   findings per `docs/finding-severity.md`.
3. **NEEDS HUMAN INPUT** — either the Reviewer or the Implementer found
   an ambiguity or a decision only the human can make. The human resolves
   it, updates the contract, and moves it back to `READY FOR REVIEW`.
4. **READY FOR APPROVAL** — the Implementer finished the work (source +
   tests) and the AI review is complete, with no P0/P1 findings left
   open. The human performs the final review.
5. **CLOSED** — the human accepted the implementation.

## What happens when a contract is CLOSED

`CLOSED` is a terminal state. When the human sets it:

- **The implementation is accepted.** No further reviewer or implementer
  work happens on this contract — it is done.
- **The human merges/finishes the work** per the repo's Git Rules in
  `AGENTS.md`: merge the feature branch into `main`; do not force push or
  rewrite history. "Finish" may also include tagging or deleting the
  branch.
- **The audit trail stays on record.** The contract, its review
  (`docs/agent-reviews/review-<name>.md`), and its response
  (`docs/agent-responses/response-<name>.md`) remain in the repo as the
  permanent record of what was agreed, found, and resolved.
- **A new piece of work starts a new contract** with a new `Contract ID`
  and its own status — it does not reopen the closed one.

Closed contracts are never reopened. If the same area needs more work
later, that is a new contract.
