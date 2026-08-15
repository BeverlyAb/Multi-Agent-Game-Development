# Review: auth-refactor

**Contract reviewed:** `docs/contract/AUTH-002/contract.md` (AUTH-002)
**Date:** 2026-08-15

## Scope reviewed

- The AUTH-002 contract (`docs/contract/AUTH-002/contract.md`)
- `README.md` (workspace root, Draft #11) vs `gdd-review-kit/gdd.txt`
  (Draft #10) vs `GachoBadi/design_review/gdd.txt` (Draft #11)
- `gdd-review-kit/review-board.html` (Draft #9 board: 2 BLOCKING, 29
  findings, 2 unresolved disagreements) — the board the Problem cites
- `gdd-review-kit/` orchestration (5 rounds), git state, `.gitignore`
- Claude Code feasibility (`claude` CLI presence and auth state)
- GachoBadi code behind the Draft #11 changes (Chain Reaction Agent,
  item affordance schema)

## Summary

The contract is structurally sound: Requirements 1-3 now line up with
the kit's 5-round orchestration, the scope is constrained, and the
acceptance criteria include a normalized-diff check on
`gdd-review-kit/gdd.txt` vs `README.md`.

Two issues block the desired outcome as written:

- The **Desired Outcome requires updating `README.md`**, but no
  requirement covers how README should change. Requirement 1 only
  *verifies* GDD sections match the code (no remediation instruction),
  and Requirement 2 only syncs `gdd.txt` to README. If verification
  finds a divergence, there is no instruction for which document is the
  source of truth or who fixes it (P1-001).
- **"No blockers" is not backed by an actionable loop or a severity
  mapping.** The kit emits BLOCKING/MAJOR/MINOR; the acceptance criteria
  use the workflow's P0/P1 vocabulary, which the kit never produces. The
  contract also never says what to do if the re-run board still reports
  BLOCKING findings. And the board the Problem cites (Draft #9, 2
  BLOCKING) is already claimed closed in README Draft #11's revision
  note, so the premise may be stale (P1-002).

Findings below: 2 × P1, 2 × P2, 2 × P3.

## Findings

### P1 — Serious (blocks completion)

| ID | Finding |
|---|---|
| P1-001 | Desired Outcome says "Update ... `README.md` and ... `gdd.txt`", but no requirement instructs updating README; Requirement 1 verifies only, and Requirement 2 syncs `gdd.txt` to README. No source-of-truth or remediation path if README diverges from code. |
| P1-002 | "So that there are no blockers" is undefined: kit severities (BLOCKING/MAJOR/MINOR) don't map to the acceptance criterion's P0/P1, and the contract has no loop for what to do if the regenerated board still reports BLOCKING findings. The cited Draft #9 board's blockers are already claimed closed in README Draft #11's revision note — stale premise. |

#### P1-001 — No requirement covers updating `README.md`

- **Evidence:** Desired Outcome: "Update the ...`README.md` and
  ...`gdd-review-kit/gdd.txt` so they are in sync and so that there are
  no blockers." Requirements: (1) "Verify these GDD sections match the
  code" — verification with no remediation; (2) "Update
  ...`gdd-review-kit/gdd.txt` to reflect the changes of the
  ...`README.md`"; (3) run the 5 rounds. Nothing says what to change in
  README, or which document wins when README and code disagree.
- **Why it matters:** The deliverable (updated README) has no
  requirement or acceptance check of its own. The implementer cannot
  tell whether a README-vs-code divergence should be fixed in README, in
  the code, or reported.
- **Suggestion:** Add a requirement: "If any section in Requirement 1
  does not match the code, update `README.md` (the GDD source) to match
  the code, then sync `gdd.txt` to README." State README → `gdd.txt` →
  board as the chain, with the code as ground truth for Requirement 1.

#### P1-002 — "No blockers" has no severity mapping and no remediation loop

- **Evidence:** Desired Outcome: "so that there are no blockers."
  Acceptance criteria: "No P0 or P1 review findings remain open."
  `gdd-review-kit` agents grade BLOCKING/MAJOR/MINOR (e.g.
  `.claude/agents/feasibility-lead.md`: "severity: BLOCKING / MAJOR /
  MINOR"); P0/P1 is the workflow's own vocabulary and never appears in
  kit output. README.md (Draft #11) revision note for Draft #10 already
  states it "closes both BLOCKING findings from the Draft #9 design
  review board (2 blocking, down from 12; `review-board.html`)", yet the
  contract's Problem presents those Draft #9 blockers as still open.
- **Why it matters:** The core deliverable — "no blockers" — is
  uncheckable as written, and the implementer has no defined response if
  the re-run board reports BLOCKING findings (edit the GDD and re-run?
  escalate to the human?).
- **Suggestion:** Define a blocker as "a BLOCKING finding in the
  regenerated `review-board.html`", replace the P0/P1 acceptance
  criterion with "no BLOCKING findings in the regenerated board", and
  state the loop: if the board reports BLOCKING findings, update the GDD
  sections in README + `gdd.txt` and re-run, or escalate to the human.

### P2 — Moderate

| ID | Finding |
|---|---|
| P2-001 | Requirement 3 still contains editorial guidance ("Enumerate round outputs (or state only `review-board.html` is required...)") instead of a decided scope; the kit's `.gitignore` excludes every kit output, so "required" is ambiguous even once stated. |
| P2-002 | Running Rounds 1-5 requires an authenticated `claude` CLI; no credentials file was found under `~/.claude`, and the kit forbids reading `gdd.txt` into the orchestrator's own context during Rounds 1-2. Requirement 3 may be unimplementable by the implementer alone. |

#### P2-001 — Round-output scope still not decided

- **Evidence:** Requirement 3 reads "...and make sure it produces an
  updated ...`review-board.html`. Enumerate round outputs (or state only
  `review-board.html` is required and others may be discarded)." That is
  guidance *about* the requirement, not a decision. The kit also
  produces `reviews/SYNTHESIS.md`, `reviews/viz-*.json`,
  `reviews/viz-spec.md`, `reviews/viz-audit.md`, and `review-viz.html`,
  and its `.gitignore` excludes all of them.
- **Why it matters:** The implementer cannot tell which outputs count as
  deliverables, and none of them would be tracked anyway.
- **Suggestion:** Make it a decision, e.g. "Run Rounds 1-5; only
  `review-board.html` is required — `SYNTHESIS.md`, `review-viz.html`,
  and `reviews/viz-*.json` may be discarded."

#### P2-002 — Running rounds requires authenticated Claude Code

- **Evidence:** The kit runs interactively through the `claude` CLI
  (`/opt/homebrew/bin/claude`, v2.1.206). No credentials file was found
  under `~/.claude` (only daemon/settings JSON), so auth status is
  unconfirmed. CLAUDE.md also forbids reading `gdd.txt` into the
  orchestrator's own context during Rounds 1-2.
- **Why it matters:** Requirement 3 may be unimplementable by the
  implementer alone; an agent executor could also violate the kit's
  context rule.
- **Suggestion:** State explicitly whether the implementer runs the
  rounds (after confirming `claude` is authenticated) or the human runs
  them, and require honoring the kit's context rules.

### P3 — Improvement

| ID | Finding |
|---|---|
| P3-001 | Path prefixes inconsistent: Problem/Req 3 use `MultiAgent-Game-Development/...`, Requirement 2 uses `MultiAgentGame/MultiAgent-Game-Development/...`. Both resolve to the same tree. |
| P3-002 | Editorial artifacts: unbalanced quote in the acceptance criterion (`matches \`README.md\` (Draft #11)" — e.g. a diff...`), template boilerplate left in Constraints ("Define what must not change...", "- ..."), and non-canonical status casing "Ready for review" vs `READY FOR REVIEW`. |

#### P3-001 — Path style inconsistency

- **Evidence:** Problem: `MultiAgent-Game-Development/gdd-review-kit/review-board.html`;
  Requirement 2: `MultiAgentGame/MultiAgent-Game-Development/gdd-review-kit/gdd.txt`.
- **Suggestion:** Use root-relative paths consistently
  (`gdd-review-kit/gdd.txt`, `README.md`).

#### P3-002 — Editorial artifacts in contract text

- **Evidence:** Acceptance criterion has a trailing unbalanced quote;
  Constraints section retains template boilerplate and a dangling "- ..."
  placeholder; Status value "Ready for review" is mixed case.
- **Suggestion:** Clean the wording and use the canonical `READY FOR
  REVIEW` token (or `NEEDS HUMAN INPUT` once this review lands).

## Report

Reported to the implementer. No source code was modified. Per
`docs/workflow-lifecycle.md`, the reviewer sets the contract status as a
direct consequence of the review; findings are open, so the status is
set to `NEEDS HUMAN INPUT`.
