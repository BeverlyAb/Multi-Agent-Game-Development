# Contract: auth-refactor

**ID:** AUTH-001
**Status:** READY FOR REVIEW



## Problem
Critics from the gdd-review-kit's moderated synthesis found significant blockers with the GDD (see MultiAgent-Game-Development/gdd-review-kit/reviews/SYNTHESIS.md and its tracked copy at GachoBadi/design_review/SYNTHESIS.md). Update MultiAgent-Game-Development/gdd-review-kit/gdd.txt to reflect the changes of the MultiAgent-Game-Development/README.md, which is its 11th version, and run through the MultiAgent-Game-Development/gdd-review-kit from rounds 1-5 to confirm the blockers are gone.

## Desired Outcome

By the end, gdd.txt, README.md, and the gdd-review-kit's SYNTHESIS.md (tracked copy at GachoBadi/design_review/SYNTHESIS.md) should be at the latest version. The human will review the results from the gdd-review-kit.

## Requirements


1. Verify these GDD sections
  match the code: Chain Reaction Agent; Item Interaction `resident_actions`/
  `chain_effect` schema; agent roster; token budgets
2. Update MultiAgentGame/MultiAgent-Game-Development/gdd-review-kit/gdd.txt to reflect the changes of the MultiAgent-Game-Development/README.md. 
3. Run the 5 rounds of testing using MultiAgent-Game-Development/gdd-review-kit/ and make sure it produces an updated MultiAgent-Game-Development/gdd-review-kit/reviews/SYNTHESIS.md. Enumerate round outputs (or state only `SYNTHESIS.md` is required and others may be discarded)
4. If any Requirement 1 section does not match the
  code, update `README.md` to match the code, then sync `gdd.txt` to
  README." State the chain code → README → `gdd.txt` → synthesis.
5. The authoritative source is the tracked Draft
  #11 copy, name the blockers to confirm gone (its Issue 1 is the
  chain-reaction softlock — which is also Requirement 1's first section),
  and define the loop: if the regenerated synthesis still reports
  BLOCKING findings, update the GDD sections and re-run, or escalate to
  the human.

6. Make the decision ("only `SYNTHESIS.md` is required —
  `review-board.html`, `review-viz.html`, and `reviews/viz-*.json` may be
  discarded"), add an acceptance criterion that the tracked
  `GachoBadi/design_review/SYNTHESIS.md` is refreshed to match the kit's,
  and replace the P0/P1 criterion with "no BLOCKING findings in the
  regenerated synthesis" (or drop it, since the human reviews).

  6. Implementer runs the
  rounds (after confirming `codex` is authenticated) or the human runs
  them, and require honoring the kit's context rules.
## Constraints

Define what must not change or what boundaries the implementation must
respect.

- **Scope:** do not modify files outside the stated areas. Do not worry about untracked version (e.g. Draft #9 artifacts). Ignore gdd.md
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
- [ ] `gdd-review-kit/gdd.txt` content
  matches `README.md` (Draft #11)" — e.g. a diff on normalized text.
## Ownership

- **Human:** owns and modifies this contract. Assigns the `Contract ID`
  and sets `Status`.
- **Reviewer:** reads the contract and owns this contract directory's
  `review.md`. Findings are numbered
  `P0-001`, `P1-001`, `P2-001`, ... per `docs/finding-severity.md`; only
  the reviewer assigns severities.
- **Implementer:** reads the contract and the review, modifies source
  code and tests, and owns this contract directory's
  `response.md`, disposing of each review finding by id.
- **AGENTS.md:** defines repository-wide rules; modified only with human
  approval (see `AGENTS.md` Governance).
