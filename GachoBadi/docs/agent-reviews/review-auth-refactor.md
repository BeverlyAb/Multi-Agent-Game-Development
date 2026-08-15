# Review: auth-refactor

**Contract reviewed:** `docs/contract/auth-refactor.md` (AUTH-001)
**Status:** Review complete — findings below. The reviewer did not modify source code.
**Date:** 2026-08-15

## Scope reviewed

- The contract (`docs/contract/auth-refactor.md`)
- `README.md` (workspace root) vs `gdd-review-kit/gdd.txt` vs `gdd-review-kit/gdd.md` vs `GachoBadi/design_review/gdd.txt`
- `gdd-review-kit/` (CLAUDE.md orchestration rules, README.md, reviews/, review-board.html)
- Git history and status of both the workspace repo and the nested `gdd-review-kit` repo
- GachoBadi code reflecting the "significant changes" (Chain Reaction Agent, items)

## Summary

The contract's intent — sync the review kit's GDD with the current code and
re-run the review — is sound, but three of its requirements rest on stale
or ambiguous premises and its acceptance criteria do not verify the actual
deliverable. The most important facts found during review:

1. **`README.md` is already current (Draft #11).** It contains the Chain
   Reaction revision note and seven Chain Reaction references. The
   contract says "Update both gdd.txt and README.md" — the stale file is
   `gdd-review-kit/gdd.txt` (Draft #10, zero Chain Reaction mentions),
   not `README.md`.
2. **There are two Draft #11 sources and two Draft #10 kit files.**
   `README.md` and `GachoBadi/design_review/gdd.txt` are both Draft #11;
   `gdd-review-kit/gdd.txt` and `gdd-review-kit/gdd.md` are both Draft #10
   and already differ from each other. The contract names only one target
   and no source of truth.
3. **Requirement 3 is not an automatable test.** Running "rounds 1-5" is an
   interactive Claude Code process (`claude` CLI, per kit CLAUDE.md) that
   overwrites `reviews/*`, `SYNTHESIS.md`, `review-board.html`, and
   `review-viz.html` — the last three of which the contract never lists.
4. **The acceptance criteria are copy-paste boilerplate.** "No P0 or P1
   review findings remain open" maps to nothing (the kit classifies as
   BLOCKING/MAJOR/MINOR), and the `demo_verify.py` criterion verifies the
   agent-workflow smoke test, not a documentation sync.

No P0 findings. Findings below: 3 × P1, 4 × P2, 2 × P3.

## Findings

### P1 — Serious

| ID | Finding |
|---|---|
| P1-001 | Requirement 2's premise is stale: `README.md` is already Draft #11 and current. |
| P1-002 | No source of truth is specified for the GDD update; two Draft #11 copies already diverge in formatting. |
| P1-003 | Requirement 3 is not executable as written: it is an interactive Claude Code run, not a test, and its outputs are partly unspecified. |

#### P1-001 — "Update README.md" is based on a false premise

- **Evidence:** `README.md` header reads "GDD Draft #11" and contains the
  Draft #11 revision note plus 7 mentions of "Chain Reaction".
  `gdd-review-kit/gdd.txt` reads "GDD Draft #10" with zero Chain Reaction
  mentions.
- **Why it matters:** Implementing requirement 2 literally means editing an
  already-current file, which either churns an up-to-date document or
  creates a completed-looking contract whose real target (`gdd-review-kit/gdd.txt`)
  is under-specified relative to it.
- **Human decision needed:** Confirm the intended target set. Recommendation:
  requirement 2 should target `gdd-review-kit/gdd.txt` (and `gdd.md`, see
  P2-003), and treat `README.md` as the already-current reference, not a file
  to update.

#### P1-002 — No source of truth for the GDD update

- **Evidence:** Two current copies exist: `README.md` (markdown, 47 KB) and
  `GachoBadi/design_review/gdd.txt` (plain text, 46 KB). Both are Draft #11
  but differ in formatting (headings, bold, bullet markers). The contract
  names neither as the canonical source.
- **Why it matters:** The implementer cannot know which file to sync the kit's
  GDD from, and formatting-only differences make "reflect the code" ambiguous.
- **Human decision needed:** Pick the canonical current GDD (suggestion:
  `README.md` is the human-facing one; `GachoBadi/design_review/gdd.txt` is
  the one GachoBadi's own workflow actually reads) and state the sync
  direction explicitly.

#### P1-003 — Requirement 3 is not an automatable test, and its outputs are under-specified

- **Evidence:** The kit's `CLAUDE.md` defines rounds 1-5 as interactive
  orchestrator prompts ("Run Round 1." etc.) driven through the `claude`
  CLI; round 3 writes `reviews/SYNTHESIS.md`; round 4 writes
  `review-board.html`; round 5 writes `review-viz.html` plus
  `reviews/viz-data.json`, `reviews/viz-spec.md`, `reviews/viz-audit.md`.
  Running rounds 1-5 will also **overwrite the existing Draft #9 artifacts**
  (`reviews/*.md` are Draft #9; `review-board.html` is titled Draft #9).
- **Why it matters:** As written, the requirement reads like a deterministic
  verification step. It is a human-supervised, interactive LLM process with
  side effects (deleting the prior board) that the Desired Outcome section
  does not enumerate.
- **Human decision needed:** Confirm who runs the rounds (human + `claude`
  CLI), that overwriting the Draft #9 artifacts is acceptable, and whether
  `review-viz.html` and `reviews/` outputs are part of the deliverable.

### P2 — Moderate

| ID | Finding |
|---|---|
| P2-001 | Requirement 1 ("Go through the files within GachoBadi") is not checkable — no list of changes to capture. |
| P2-002 | Acceptance criteria are template boilerplate and do not verify the deliverable. |
| P2-003 | `gdd-review-kit` is a nested, separate git repo; `gdd.md` is untracked there and already diverges from `gdd.txt`. |
| P2-004 | Desired outcome omits artifacts the rounds actually produce (SYNTHESIS.md, review-viz.html, reviews/). |

#### P2-001 — Requirement 1 is unverifiable

- **Evidence:** The requirement lists no specific changes or files.
- **Why it matters:** There is no way to tell whether "go through the files"
  was done, and no definition of which code changes must be reflected.
- **Suggestion:** Replace with a checklist (e.g. "verify the following GDD
  sections match the code: Chain Reaction Agent, Item Interaction affordance
  schema, agent roster, token budgets").

#### P2-002 — Acceptance criteria do not test the deliverable

- **Evidence:** Criteria reference `demo_verify.py --agents all` and
  `executable/main.py` (game-run smoke tests, unrelated to a doc sync) and
  "No P0 or P1 review findings remain open" — but the kit classifies as
  BLOCKING/MAJOR/MINOR, so the P0/P1 threshold cannot be evaluated.
- **Why it matters:** The criteria would all pass while the GDD was still
  stale, or fail for reasons unrelated to the task.
- **Suggestion:** Replace with: "gdd-review-kit/gdd.txt is Draft #11 and
  matches the canonical source's content; gdd.md matches gdd.txt; rounds 1-5
  completed; review-board.html regenerated; git diff reviewed."

#### P2-003 — Nested repo and untracked gdd.md

- **Evidence:** `gdd-review-kit/` has its own `.git`; the workspace repo does
  not track it (`?? gdd-review-kit`). `gdd-review-kit/gdd.md` is untracked in
  the kit repo and already differs from `gdd.txt` (48,801 vs 48,229 bytes).
- **Why it matters:** A completed contract could leave changes in the wrong
  repo, and `gdd.md` would silently go stale even if `gdd.txt` is fixed.
- **Suggestion:** State explicitly that kit changes commit inside
  `gdd-review-kit/`, and add `gdd.md` to the update scope.

#### P2-004 — Desired Outcome is incomplete

- **Evidence:** Rounds 3/5 produce `SYNTHESIS.md` and `review-viz.html`;
  Desired Outcome lists only gdd.txt, README.md, review-board.html.
- **Why it matters:** Success criteria and produced artifacts diverge; the
  implementer cannot tell if extra files are bugs or expected.
- **Suggestion:** Enumerate all round outputs in Desired Outcome (or state
  that only review-board.html is required).

### P3 — Improvement

| ID | Finding |
|---|---|
| P3-001 | Contract path references are inconsistent (`MultiAgentGame/MultiAgent-Game-Development/...` vs `MultiAgent-Game-Development/...`). |
| P3-002 | Pin the target Draft version (#11) explicitly in the contract header/requirements. |

#### P3-001 — Path style inconsistency

- **Evidence:** Problem section writes
  `MultiAgentGame/MultiAgent-Game-Development/gdd-review-kit/gdd.txt` but
  `MultiAgent-Game-Development/README.md`; both resolve to the same tree.
- **Suggestion:** Use repo-root-relative paths (`gdd-review-kit/gdd.txt`,
  `README.md`) consistently.

#### P3-002 — Pin the draft version

- **Evidence:** Nothing in the contract names Draft #11, so "reflect the
  changes" depends on reading the files.
- **Suggestion:** Add "GDD is currently Draft #11; kit files are Draft #10"
  to the Problem section.

## Report

Reported to the implementer. No source code was modified. Contract status
(`READY FOR REVIEW`) is unchanged — per `docs/workflow-lifecycle.md`, only
the human owner changes status. The P1 items (especially P1-001 and P1-002)
likely warrant `NEEDS HUMAN INPUT` before implementation starts.
