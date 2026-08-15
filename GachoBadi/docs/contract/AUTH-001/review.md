# Review: auth-refactor

**Contract reviewed:** `docs/contract/AUTH-001/contract.md` (AUTH-001, revision 4)
**Date:** 2026-08-15

## Scope reviewed

- The AUTH-001 contract, revision 4 (AUTH-002 merged in; deliverable
  re-pointed at `SYNTHESIS.md`)
- `README.md` (workspace root, Draft #11) vs `gdd-review-kit/gdd.txt`
  (Draft #10) vs `gdd-review-kit/gdd.md` (Draft #10, untracked) vs
  `GachoBadi/design_review/gdd.txt` (Draft #11)
- The two SYNTHESIS.md sources the Problem cites:
  `gdd-review-kit/reviews/SYNTHESIS.md` (Draft #9) and the tracked copy
  `GachoBadi/design_review/SYNTHESIS.md` (Draft #11)
- `gdd-review-kit/` orchestration (5 rounds), git state, `.gitignore`
- Claude Code feasibility (`claude` CLI presence and auth state)
- GachoBadi code behind the Draft #11 changes (Chain Reaction Agent,
  `resident_actions`/`chain_effect` schema, roster, token budgets)

## Summary

Revision 4 correctly merges AUTH-002 into AUTH-001 and re-points the kit
deliverable from `review-board.html` to the moderated `SYNTHESIS.md`. The
merged Problem leads with the blockers found by the synthesis, and the
Desired Outcome keeps the human-review framing — the right choice given
the "no blockers" acceptance gap.

Two P1s from the AUTH-002 contract carry into the merge and block
completion as written:

- **P1-001** — the Problem cites *two* divergent SYNTHESIS.md sources
  (kit Draft #9: 2 BLOCKING; tracked copy Draft #11: 10 BLOCKING / 16
  MAJOR / 4 MINOR) without stating which is authoritative or which
  blockers must be confirmed gone, and there is no loop for what to do if
  the re-run synthesis still reports BLOCKING findings.
- **P1-002** — the Desired Outcome requires `README.md` to be "at the
  latest version", but no requirement covers updating it; Requirement 1
  verifies only, so a README-vs-code divergence has no remediation path.

Findings below: 2 × P1, 2 × P2, 2 × P3.

## Findings

### P1 — Serious (blocks completion)

| ID | Finding |
|---|---|
| P1-001 | Problem cites two divergent SYNTHESIS.md sources (Draft #9: 2 BLOCKING vs Draft #11: 10 BLOCKING / 16 MAJOR / 4 MINOR) with no authoritative source, no target blocker list, and no remediation loop if the re-run still reports BLOCKING. |
| P1-002 | Desired Outcome requires `README.md` at the latest version, but no requirement covers updating it; Requirement 1 verifies GDD sections against code with no remediation instruction when they diverge. |

#### P1-001 — Premise sources diverge; target and loop for "blockers gone" undefined

- **Evidence:** Problem: "Critics from the gdd-review-kit's moderated
  synthesis found significant blockers with the GDD (see
  `gdd-review-kit/reviews/SYNTHESIS.md` and its tracked copy at
  `GachoBadi/design_review/SYNTHESIS.md`)". The kit copy is Draft #9
  (2 BLOCKING, its revision note claims Draft #9 closed all 12 Draft #8
  blockers); the tracked copy is Draft #11 (30 findings after
  cross-examination: 10 BLOCKING / 16 MAJOR / 4 MINOR, 3 unresolved
  disagreements). Desired Outcome: "run ... rounds 1-5 to confirm the
  blockers are gone"; the human reviews the results.
- **Why it matters:** The two sources disagree by 8 BLOCKING findings, so
  the implementer cannot tell which findings "the critics" are. Running
  the 5 rounds on the updated `gdd.txt` may produce a third, different
  tally; nothing defines the loop if BLOCKING findings remain (edit GDD
  and re-run? escalate to the human?).
- **Suggestion:** State the authoritative source (e.g. the tracked Draft
  #11 copy), name the blockers to confirm gone (its Issue 1 is the
  chain-reaction softlock — which is also Requirement 1's first section),
  and define the loop: if the regenerated synthesis still reports
  BLOCKING findings, update the GDD sections and re-run, or escalate to
  the human.

#### P1-002 — No requirement covers updating `README.md`

- **Evidence:** Desired Outcome: "gdd.txt, README.md, and ... SYNTHESIS.md
  ... should be at the latest version." Requirements: (1) "Verify these
  GDD sections match the code" — verification with no remediation;
  (2) update `gdd.txt` to reflect README changes; (3) run rounds 1-5.
  Nothing instructs changing README, or which document wins when README
  and code disagree.
- **Why it matters:** The merged Desired Outcome carries AUTH-002's
  README-update intent, but no requirement backs it. A divergence found
  by Requirement 1 has no defined fix.
- **Suggestion:** Add: "If any Requirement 1 section does not match the
  code, update `README.md` to match the code, then sync `gdd.txt` to
  README." State the chain code → README → `gdd.txt` → synthesis.

### P2 — Moderate

| ID | Finding |
|---|---|
| P2-001 | Requirement 3 still contains editorial guidance ("Enumerate round outputs (or state only `SYNTHESIS.md` is required...)") instead of a decision; the acceptance criterion "No P0 or P1 review findings remain open" still cannot be evaluated against the kit's BLOCKING/MAJOR/MINOR vocabulary. |
| P2-002 | Running rounds 1-5 requires an authenticated `claude` CLI; no credentials file was found under `~/.claude`, and the kit forbids reading `gdd.txt` into the orchestrator's own context during Rounds 1-2. |

#### P2-001 — Round-output scope and severity vocabulary still unresolved

- **Evidence:** Requirement 3: "...make sure it produces an updated
  `gdd-review-kit/reviews/SYNTHESIS.md`. Enumerate round outputs (or
  state only `SYNTHESIS.md` is required and others may be discarded)".
  The kit also produces `review-board.html`, `review-viz.html`,
  `reviews/viz-*.json`, `reviews/viz-spec.md`, `reviews/viz-audit.md`,
  and its `.gitignore` ignores `reviews/*.md` — so `SYNTHESIS.md` is
  deliverable only via the tracked copy at
  `GachoBadi/design_review/SYNTHESIS.md`, which the acceptance criteria
  never check. Separately, "No P0 or P1 review findings remain open"
  still maps to nothing the kit emits.
- **Why it matters:** The deliverable's only trackable path is unmentioned
  in the acceptance criteria, and one criterion remains uncheckable.
- **Suggestion:** Make the decision ("only `SYNTHESIS.md` is required —
  `review-board.html`, `review-viz.html`, and `reviews/viz-*.json` may be
  discarded"), add an acceptance criterion that the tracked
  `GachoBadi/design_review/SYNTHESIS.md` is refreshed to match the kit's,
  and replace the P0/P1 criterion with "no BLOCKING findings in the
  regenerated synthesis" (or drop it, since the human reviews).

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
| P3-001 | Path prefixes inconsistent: Problem/Desired Outcome use `MultiAgent-Game-Development/...`, Requirement 2 uses `MultiAgentGame/MultiAgent-Game-Development/...`. |
| P3-002 | Editorial artifacts: unbalanced quote in the acceptance criterion, template boilerplate and a dangling "- ..." left in Constraints, and round-output guidance pasted inside Requirement 3. |

#### P3-001 — Path style inconsistency

- **Evidence:** Problem/Desired Outcome write
  `MultiAgent-Game-Development/gdd-review-kit/...`; Requirement 2 writes
  `MultiAgentGame/MultiAgent-Game-Development/gdd-review-kit/gdd.txt`.
  Both resolve to the same tree.
- **Suggestion:** Use root-relative paths (`gdd-review-kit/gdd.txt`,
  `README.md`) consistently.

#### P3-002 — Editorial artifacts in contract text

- **Evidence:** Acceptance criterion has a trailing unbalanced quote
  (`matches \`README.md\` (Draft #11)" — e.g. a diff...`); the Constraints
  section retains template boilerplate ("Define what must not change...")
  and a dangling "- ..." placeholder; Requirement 3 embeds review guidance
  mid-sentence.
- **Suggestion:** Clean the wording; the substance of each is fine.

## Report

Reported to the implementer. No source code was modified. Per
`docs/workflow-lifecycle.md`, the reviewer sets the contract status as a
direct consequence of the review; P1 and P2 findings are open, so the
status is `NEEDS HUMAN INPUT`. The two P1s need human decisions (pick the
authoritative synthesis + its target blockers; define the README
remediation path); the two P2s need a decision on round-output scope and
how the Claude Code rounds are executed.
