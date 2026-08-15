# Review: auth-refactor

**Contract reviewed:** `docs/contract/auth-refactor.md` (AUTH-001, revision 2)
**Status:** Re-review complete — findings below. The reviewer did not modify source code.
**Date:** 2026-08-15

## Scope reviewed

- The revised contract (`docs/contract/auth-refactor.md`)
- `README.md` (workspace root) vs `gdd-review-kit/gdd.txt` vs `gdd-review-kit/gdd.md` vs `GachoBadi/design_review/gdd.txt`
- `gdd-review-kit/` orchestration (CLAUDE.md, README.md), git state of the nested kit repo, and `.gitignore`
- GachoBadi code behind the Draft #11 changes (Chain Reaction Agent, item affordance schema)

## Summary

The revision resolves the two core P1s from the previous review: requirement 2
now says *update `gdd-review-kit/gdd.txt` to reflect `README.md`* (no longer
asks to update the already-current `README.md`), and `README.md` is named as
the reference, pinning Draft #11. The draft version is also stated explicitly.

One serious finding remains, on a detail the revision did not touch: **running
rounds 1-5 permanently overwrites the existing Draft #9 artifacts
(`reviews/*.md`, `review-board.html`), and all of those files are gitignored
inside the kit repo — nothing is committed, so the Draft #9 review is lost
with no way back.** The contract neither acknowledges nor preserves it.

Verified current state (unchanged since the previous review):
`README.md` = Draft #11, `gdd-review-kit/gdd.txt` = Draft #10,
`gdd-review-kit/gdd.md` = Draft #10 (untracked, diverging from `gdd.txt`),
`GachoBadi/design_review/gdd.txt` = Draft #11, `reviews/` = Draft #9,
`review-board.html` = Draft #9, no `review-viz.html` (Round 5 never run).

No P0 findings. Findings below: 1 × P1, 4 × P2, 2 × P3.

## Resolved since previous review

| Previous | Disposition |
|---|---|
| P1-001 (stale "update README.md" premise) | **Resolved** — requirement 2 now updates `gdd.txt` from `README.md`. |
| P1-002 (no source of truth) | **Resolved** — `README.md` is the named reference. |
| P3-002 (pin draft version) | **Resolved** — "its 11th version" is now stated. |

## Findings

### P1 — Serious

| ID | Finding |
|---|---|
| P1-001 | Running rounds 1-5 permanently overwrites unversioned Draft #9 artifacts (`reviews/*.md`, `review-board.html` are gitignored in the kit repo). |

#### P1-001 — Draft #9 review artifacts are lost on rerun

- **Evidence:** `gdd-review-kit/.gitignore` excludes `reviews/*.md`,
  `reviews/*.json`, `review-board.html`, and `review-viz.html`. The kit repo
  has no commits containing them, and the workspace repo does not track
  `gdd-review-kit/` at all (`?? gdd-review-kit`). The revision's requirement 3
  says "Run the 5 rounds ... make sure it produces an updated
  review-board.html" — rounds 1-4 rewrite `reviews/*` and
  `review-board.html` in place.
- **Why it matters:** The Draft #9 board's findings exist only on disk. A
  rerun overwrites them, and the findings are not reproducible by re-running
  (real-LLM output differs every run). This is unrecoverable loss unless
  preserved first. The contract also never says whether overwriting is
  acceptable.
- **Suggestion:** Before running rounds, snapshot the Draft #9 artifacts
  (e.g. commit them in the kit repo, or copy to a `reviews/draft-9/`
  backup), and state in the contract that the Draft #9 artifacts will be
  superseded. Note: running the rounds also requires authenticated Claude
  Code (`claude` CLI is present at `/opt/homebrew/bin/claude`; no credentials
  file found under `~/.claude`).

### P2 — Moderate

| ID | Finding |
|---|---|
| P2-001 | Requirement 1 ("Go through the files within GachoBadi") is still uncheckable. |
| P2-002 | Acceptance criteria are still boilerplate and do not verify the deliverable. |
| P2-003 | `gdd-review-kit/gdd.md` (Draft #10, untracked, divergent) is still not in scope. |
| P2-004 | Round outputs beyond `review-board.html` (SYNTHESIS.md, review-viz.html, viz-*.json) are still unlisted. |

#### P2-001 — Requirement 1 is unverifiable

- **Evidence:** Requirement 1 lists no specific changes or files to compare.
- **Why it matters:** There is no way to tell whether the survey was done or
  which code changes must be reflected in `gdd.txt`.
- **Suggestion:** Replace with a checklist, e.g. "verify these GDD sections
  match the code: Chain Reaction Agent; Item Interaction `resident_actions`/
  `chain_effect` schema; agent roster; token budgets."

#### P2-002 — Acceptance criteria do not test the deliverable

- **Evidence:** Criteria still cite `demo_verify.py` and `executable/main.py`
  (game-run smoke tests, unrelated to a doc sync) and "No P0 or P1 review
  findings remain open" — but the kit classifies as BLOCKING/MAJOR/MINOR, so
  the P0/P1 threshold cannot be evaluated from kit output.
- **Why it matters:** The criteria can pass while `gdd.txt` is still Draft #10.
- **Suggestion:** Add a concrete check: "`gdd-review-kit/gdd.txt` content
  matches `README.md` (Draft #11)" — e.g. a diff on normalized text.

#### P2-003 — Untracked, divergent `gdd.md` left out of scope

- **Evidence:** `gdd-review-kit/gdd.md` is untracked in the kit repo
  (`git -C gdd-review-kit status` shows `?? gdd.md`) and already differs from
  `gdd.txt` (48,801 vs 48,229 bytes). The contract updates only `gdd.txt`.
- **Why it matters:** The kit ships two GDD files; fixing one silently leaves
  the other stale.
- **Suggestion:** Add `gdd.md` to requirement 2, or state explicitly that it
  is intentionally out of scope and will be deleted/ignored.

#### P2-004 — Desired Outcome omits artifacts rounds actually produce

- **Evidence:** Round 3 writes `reviews/SYNTHESIS.md`; round 5 writes
  `review-viz.html` plus `reviews/viz-data.json`, `viz-spec.md`,
  `viz-audit.md`. Desired Outcome lists only gdd.txt, README.md,
  review-board.html.
- **Why it matters:** The implementer cannot tell whether extra files are
  expected deliverables or accidental byproducts.
- **Suggestion:** Enumerate round outputs (or state only `review-board.html`
  is required and others may be discarded).

### P3 — Improvement

| ID | Finding |
|---|---|
| P3-001 | Path prefixes remain inconsistent between Problem and Requirements. |
| P3-002 | Consider a content-diff check between `gdd.txt` and `README.md` as an acceptance step. |

#### P3-001 — Path style inconsistency

- **Evidence:** Problem writes `MultiAgent-Game-Development/gdd-review-kit/gdd.txt`;
  requirements write `MultiAgentGame/MultiAgent-Game-Development/...`. Both
  resolve to the same tree but the prefix differs.
- **Suggestion:** Use root-relative paths (`gdd-review-kit/gdd.txt`,
  `README.md`) consistently.

#### P3-002 — Add a diff acceptance step

- **Evidence:** Nothing mechanically checks that `gdd.txt` "reflects"
  `README.md`.
- **Suggestion:** Add an acceptance criterion that runs a whitespace/punctuation
  -normalized diff of `gdd.txt` against `README.md` and requires no content
  drift beyond the two files' intentional format differences.

## Report

Reported to the implementer. No source code was modified. Contract status
(`READY FOR REVIEW`) is unchanged — per `docs/workflow-lifecycle.md`, only
the human owner changes status. The single remaining P1 (Draft #9 artifact
loss on rerun) and P1-001's Claude Code authentication precondition should
be acknowledged by the human before implementation starts.
