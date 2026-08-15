# Contract: auth-refactor

**ID:** AUTH-001
**Status:** READY FOR REVIEW



## Problem

There have been significant changes to the code that might not be captured in the MultiAgentGame/MultiAgent-Game-Development/gdd-review-kit/gdd.txt and its .md version in MultiAgent-Game-Development/README.md. 

Update both gdd.txt and README.md and run through the MultiAgent-Game-Development/gdd-review-kit from rounds 1-5. 

## Desired Outcome

By the end, gdd.txt, README.md, and MultiAgent-Game-Development/gdd-review-kit/review-board.html should be updated.

## Requirements


1. Go through the files within GachoBadi.
2. Update MultiAgentGame/MultiAgent-Game-Development/gdd-review-kit/gdd.txt and  MultiAgent-Game-Development/README.md to reflect the changes.
3. Run the 5 rounds of testing using MultiAgent-Game-Development/gdd-review-kit/.

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
