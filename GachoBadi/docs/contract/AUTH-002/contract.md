# Contract: NPC Reaction System

**ID:** AUTH-002
**Status:** READY FOR REVIEW

## Problem

NPC characters (Residents) don't react to completed tasks. The `goal_state` text on each task mentions "positive reaction flag" but no such flag exists on any data model. The Director's `check_goal_state()` only verifies that residents and buildings exist — it never evaluates reaction state. Reactions are purely text artifacts (ChainReaction → Screenplay → StagedAction), not persistent behavioral state. The relationship graph is write-once at initialization and never updates as tasks resolve. The Phaser client shows a one-shot sprite tween on resolution and forgets it happened. Players have no sense that their actions changed anything about the NPCs.

## Desired Outcome

By the end, each Resident tracks mood, satisfaction, and a reaction log. When a task resolves, the involved residents' states update. Subsequent tasks reference prior outcomes in their descriptions and goal states. The Director enforces real goal conditions (not just existence checks). The Phaser client displays persistent mood indicators and shows the reaction history in the Lore panel. The verification layer catches drift at each stage.

## Requirements

1. **Reaction state on Residents.** Add `mood` (str), `satisfaction` (int 0–100), `recent_task_outcome` (Optional[str]), and `reaction_log` (List[dict]) fields to `definitions/models.py` `Resident`. Default `mood` to `"neutral"`, `satisfaction` to `50`, `recent_task_outcome` to `None`, `reaction_log` to `[]`.

2. **Reaction determination at resolution.** After the Director mutates `task.status` to `"resolved"` in `crew.py`, determine a structured reaction for each involved resident: `{resident, mood_change, satisfaction_delta, reaction_text}`. Append the record to both residents' `reaction_log`; update `mood` and `satisfaction`. For retired tasks, set `recent_task_outcome` to `"retired"` with a deterministic negative mood shift. Implement this in a new `agents/runtime/reaction_agent.py` or extend the DirectorAgent — whichever fits the existing crew pattern.

3. **Task propagation.** Update `agents/runtime/task_creator_agent.py` so that the LLM prompt includes each resident's `recent_task_outcome`, `mood`, and `satisfaction` as context. Task descriptions should reference prior outcomes where natural (e.g. "Hazel is still annoyed about the bakery incident"). The `goal_state` string must reference trackable state fields (e.g. `"Hazel's mood is 'pleased' and satisfaction >= 60"`) instead of the current phantom "positive reaction flag".

4. **Director goal-state enforcement.** Update `agents/runtime/director_agent.py` `check_goal_state()` to parse and evaluate real conditions from `goal_state` — mood checks, satisfaction thresholds, building existence. If the goal state can't be met (NPC too annoyed, wrong mood), retire the task with a meaningful reason.

5. **Phaser visual persistence.** Update `web/game.js` to read resident mood/satisfaction from `output/crew/manifest.json`. After task resolution, persist a mood indicator on the resident's sprite (tint, icon, or label change). Show the `reaction_log` entries in the Lore panel alongside the agent trail. Optionally vary idle animation based on mood.

6. **Verification constraints.** Add a new `workflow/constraints/reaction/` folder with `constraints.yaml` and `constraints.py` enforcing: `mood_change_requires_prior_task` (can't set mood without a completed task), `satisfaction_bounds` (satisfaction stays 0–100), `goal_state_references_real_state` (goal_state strings must match trackable fields on Resident). Wire these into the GER pipeline's Evaluator.

## Constraints

- **Scope:** do not modify files outside the stated areas. Respect the existing agent architecture — reactions come from agents, not hardcoded logic.
- **Dependencies:** no new mandatory dependencies (project is stdlib-only).
- **API compatibility:** preserve existing public interfaces. `Resident` gains new optional fields with sensible defaults; existing code that constructs `Resident` without these fields must not break.
- **Behavioral rules:** the project's coding rules in `AGENTS.md` apply. Values in `constraints.yaml`, logic in `constraints.py`. Keep `workflow/generic/` agent-agnostic; domain-specific gap detection goes in `workflow/constraints/<agent>/`.
- **One-way-door:** once a task leaves "open," it never re-enter. Reactions append to history; nothing overwrites or deletes prior reaction records.
- **Mock LLM provider:** the deterministic fallback must handle all new agent calls gracefully — every new agent must supply a `fallback` string so the crew never crashes.

## Acceptance Criteria

- [ ] All Requirements above are satisfied.
- [ ] `definitions/models.py` `Resident` has `mood`, `satisfaction`, `recent_task_outcome`, `reaction_log` fields with correct defaults.
- [ ] After `python3 executable/main.py`, at least one resident's `reaction_log` is non-empty in `output/crew/manifest.json`.
- [ ] After `python3 executable/main.py`, the Director retires at least one task with a reaction-based reason (mood too low, goal state unreachable) — or all tasks pass cleanly and the reason is documented.
- [ ] `python3 workflow/generic/demo_verify.py --agents all` passes.
- [ ] `python3 executable/main.py` runs without crashes.
- [ ] New behavior is covered by verification where applicable.
- [ ] No unintended changes are present (`git diff` reviewed).
- [ ] No P0 or P1 review findings remain open.
- [ ] `AGENTS.md` "Before Completing a Task" steps are satisfied.

## Ownership

- **Human:** owns and modifies this contract. Assigns the `Contract ID` and sets `Status`.
- **Reviewer:** reads the contract and owns this contract directory's `review.md`. Findings are numbered `P0-001`, `P1-001`, `P2-001`, ... per `docs/finding-severity.md`; only the reviewer assigns severities.
- **Implementer:** reads the contract and the review, modifies source code and tests, and owns this contract directory's `response.md`, disposing of each review finding by id.
- **AGENTS.md:** defines repository-wide rules; modified only with human approval (see `AGENTS.md` Governance).
