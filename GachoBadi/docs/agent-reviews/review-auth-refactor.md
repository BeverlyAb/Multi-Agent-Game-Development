# Review: auth-refactor

**Contract reviewed:** `docs/contract/auth-refactor.md` (AUTH-001, revision 3)
**Status:** Re-review complete — findings below. The reviewer did not modify source code.
**Date:** 2026-08-15

## Scope reviewed

- The revised contract (`docs/contract/auth-refactor.md`)
- `README.md` (workspace root) vs `gdd-review-kit/gdd.txt` vs `gdd-review-kit/gdd.md` vs `GachoBadi/design_review/gdd.txt`
- `gdd-review-kit/` orchestration and git state, `gdd-review-kit/.gitignore`
- Claude Code feasibility (`claude` CLI presence and auth state)
- GachoBadi code behind the Draft #11 changes (Chain Reaction Agent, item affordance schema)

## Summary

This revision resolves the previous review's P1 and nearly all P2s:

- **P1-001 (Draft #9 artifact loss) — resolved.** The Constraints now state
  "Do not worry about untracked version (e.g. Draft #9 artifacts)", which
  explicitly authorizes overwriting them.
- **P2-001 (uncheckable requirement 1) — resolved.** Requirement 1 is now a
  concrete checklist: Chain Reaction Agent, Item Interaction
  `resident_actions`/`chain_effect` schema, agent roster, token budgets.
- **P2-002 (boilerplate acceptance criteria) — largely resolved.** A new
  criterion requires `gdd-review-kit/gdd.txt` content to match `README.md`
  (Draft #11) via a normalized diff. One sub-item remains (see P2-001 below).
- **P2-003 (gdd.md out of scope) — resolved.** "Ignore `gdd.md`" is now
  explicit.
- **P3-002 (diff acceptance step) — resolved.** Incorporated as the new
  acceptance criterion.

Verified current state (unchanged): `README.md` = Draft #11,
`gdd-review-kit/gdd.txt` = Draft #10, `gdd-review-kit/gdd.md` = Draft #10
(untracked), `GachoBadi/design_review/gdd.txt` = Draft #11,
`reviews/` and `review-board.html` = Draft #9.

No P0 or P1 findings. Findings below: 2 × P2, 2 × P3.

## Resolved since previous review

| Previous | Disposition |
|---|---|
| P1-001 (Draft #9 loss on rerun) | **Resolved** — "Do not worry about untracked version (e.g. Draft #9 artifacts)". |
| P2-001 (requirement 1 uncheckable) | **Resolved** — requirement 1 is now a specific checklist. |
| P2-002 (criteria don't test deliverable) | **Resolved** — normalized-diff criterion added. |
| P2-003 (gdd.md out of scope) | **Resolved** — "Ignore `gdd.md`". |
| P2-004 (round outputs unlisted) | **Resolved** — requirement 3 now directs enumerating/limiting round outputs. |
| P3-002 (diff acceptance step) | **Resolved** — added as an acceptance criterion. |

## Findings

### P2 — Moderate

| ID | Finding |
|---|---|
| P2-001 | Requirement 3 contains editorial guidance instead of a decided scope, and the P0/P1 acceptance criterion still does not map to the kit's BLOCKING/MAJOR/MINOR vocabulary. |
| P2-002 | Requirement 3 asks the implementer to run rounds 1-5, but no Claude Code credentials were found; execution may need to stay with the human. |

#### P2-001 — Round-output scope is still not decided; P0/P1 criterion remains unmappable

- **Evidence:** Requirement 3 reads "Run the 5 rounds ... make sure it
  produces an updated `review-board.html`. Enumerate round outputs (or state
  only `review-board.html` is required and others may be discarded)" — that
  is guidance *about* the requirement, not the requirement itself. The
  contract still does not state whether `SYNTHESIS.md`, `review-viz.html`,
  and `reviews/viz-*.json` count as deliverables. Separately, acceptance
  criterion "No P0 or P1 review findings remain open" still cannot be
  evaluated: the kit produces BLOCKING/MAJOR/MINOR, not P0/P1.
- **Why it matters:** The implementer is told to decide scope that the human
  should own, and one criterion remains uncheckable.
- **Suggestion:** Reword requirement 3 to a decision, e.g. "Run rounds 1-5;
  only `review-board.html` is required — `SYNTHESIS.md` and `review-viz.html`
  may be discarded." Replace the P0/P1 criterion with "no BLOCKING findings
  remain in the kit's synthesis" (or drop it, since the human reviews).

#### P2-002 — Running rounds requires authenticated Claude Code

- **Evidence:** The kit runs interactively through the `claude` CLI
  (`/opt/homebrew/bin/claude`, v2.1.206). No credentials file was found under
  `~/.claude` (only daemon/settings JSON), so auth status is unconfirmed.
  Rounds 1-2 also must not read `gdd.txt` into the orchestrator's own
  context — an agent executor could violate the kit's own rule.
- **Why it matters:** Requirement 3 may be unimplementable by the
  implementer alone; the human-review clause suggests the human will run it,
  but the requirement still assigns it to the implementer.
- **Suggestion:** State explicitly that the implementer prepares inputs and
  the human runs the 5 rounds (or confirm `claude` is authenticated and the
  implementer may run it, honoring the kit's context rules).

### P3 — Improvement

| ID | Finding |
|---|---|
| P3-001 | Path prefixes remain inconsistent between Problem and Requirements. |
| P3-002 | Editorial artifacts in the contract text: unclosed quote in the acceptance criterion and guidance pasted into requirement 3. |

#### P3-001 — Path style inconsistency

- **Evidence:** Problem writes `MultiAgent-Game-Development/gdd-review-kit/gdd.txt`;
  requirements write `MultiAgentGame/MultiAgent-Game-Development/...`. Both
  resolve to the same tree.
- **Suggestion:** Use root-relative paths (`gdd-review-kit/gdd.txt`,
  `README.md`) consistently.

#### P3-002 — Editorial artifacts in contract text

- **Evidence:** Acceptance criterion has a trailing unbalanced quote
  (`matches \`README.md\` (Draft #11)" — e.g. a diff...`), and requirement 3
  embeds review guidance mid-sentence.
- **Suggestion:** Clean the wording; the substance of both is fine.

## Report

Reported to the implementer. No source code was modified. Contract status
(`READY FOR REVIEW`) is unchanged — per `docs/workflow-lifecycle.md`, only
the human owner changes status. The contract is in good shape to proceed; the
two remaining P2s are about deciding round-output scope and confirming how the
Claude Code rounds will be executed.
