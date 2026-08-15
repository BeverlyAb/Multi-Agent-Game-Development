# Contract: auth-refactor

> **Template.** Copy this file for a new piece of work: give it a unique
> `Contract ID` and replace every `...` placeholder. The human owner
> writes the contract; the reviewer and implementer consume it (see
> [Ownership](#ownership)).

**ID:** AUTH-001
**Status:** READY FOR REVIEW

## Problem

Describe what is wrong, missing, or needs improvement. Be concrete: name
the behavior, the code path, or the user-visible symptom. If this traces
back to a `design_review/gdd.txt` requirement, cite it.

## Desired Outcome

Describe what should be true after the work is complete — the observable
state, not the implementation.

## Requirements

Numbered, checkable requirements. Each should be verifiable on its own.

1. ...
2. ...
3. ...

## Constraints

Define what must not change or what boundaries the implementation must
respect.

- **Scope:** do not modify files outside the stated areas.
- **Dependencies:** no new mandatory dependencies (project is stdlib-only).
- **API compatibility:** preserve existing public interfaces.
- **Behavioral rules:** the project's coding rules in `AGENTS.md` apply,
  including the Item Interaction / registered-verb contract.
- ...

## Acceptance Criteria

A checklist the implementer uses to prove the work is done. Add any
contract-specific checks on top of these:

- [ ] All Requirements above are satisfied.
- [ ] Relevant verification passes: `python3 workflow/generic/demo_verify.py --agents all` (and the affected agent's goal loop if `workflow/` changed).
- [ ] The full game runs: `python3 executable/main.py`.
- [ ] New behavior is covered by verification/tests where applicable.
- [ ] No unintended changes are present (`git diff` reviewed).
- [ ] No P0 or P1 review findings remain open.
- [ ] `AGENTS.md` "Before Completing a Task" steps are satisfied.

## Ownership

- **Human:** owns and modifies this contract. Assigns the `Contract ID`
  and sets `Status`.
- **Reviewer:** reads the contract and owns
  `docs/agent-reviews/review-auth-refactor.md`. Findings are numbered
  `P0-001`, `P1-001`, `P2-001`, ... per `docs/finding-severity.md`; only
  the reviewer assigns severities.
- **Implementer:** reads the contract and the review, modifies source
  code and tests, and owns
  `docs/agent-responses/response-auth-refactor.md`, disposing of each
  review finding by id.
- **AGENTS.md:** defines repository-wide rules; modified only with human
  approval (see `AGENTS.md` Governance).
