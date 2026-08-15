# Domain Models ("database")

Gachō Badi has no database. The "database" is the shared data model layer
in `definitions/models.py` — the crew's blackboard that agents pass
between each other — plus the serialized output written to `output/crew/`
and the verification layer's own bookkeeping model.

## `definitions/models.py` (the game's domain model)

All dataclasses; every agent validates that a prior agent enriched its
inputs and raises if one was skipped.

- **`Sliders`** — the player-tuned inputs (movement/speech/energy/
  intelligence, 0–100) the GDD's Character Personality Agent reads.
- **`Resident`** — name, role, `sliders`, plus `traits` and
  `personality_summary` (Character Personality Agent), `appearance`
  (Character Appearance Agent), and `relationships` / `relationship_backstories`
  (Relationship Agent). A label alone is never sufficient content for a
  task — the Writer must reference the backstory too.
- **`VerbOutcome`** — one possible resident follow-up on an object
  (`resident_action`, optional `chain_effect`). Which ONE happens for a
  task is picked at random by `ChainReactionAgent` — the goose's exact
  motion isn't fully predictable even when its action was legal.
- **`Item`** — a movable prop. Enriched by ItemInteractionAgent:
  `affordance`, `goose_actions`, `reset_rule` (the no-permanent-loss
  guarantee), `designed`, and `possible_outcomes` (an empty list is
  common and not an error).
- **`Building`** — fixed world feature. `location` (Island Layout
  Agent), `designed` (Building Designer Agent), and — kept separate
  because different agents own them — `goose_actions` and
  `possible_outcomes` (Item Interaction Agent).
- **`Task`** — the lifecycle record: `task_id`, `set_id`, description,
  `target_resident`, `other_resident`, `involves_building`,
  `involves_item`, an explicit checkable `goal_state`, and
  `status` (`open` | `resolved` | `retired`) with `retire_reason`.
- **`Screenplay`** — writer output (dialogue + directional cues).
- **`VerbPlan`** — goose-verb-only stage directions; no dialogue, ever.
- **`StagedAction`** — actor + action + location.
- **`ChainReaction`** — at most two follow-on beats after the goose's
  own action; zero steps is the common case and is not an error.
- **`NewsBulletin`** — headline, one per resolved/retired task.

### Enrichment order (who writes what)

Residents need personality traits before relationships; buildings need
`location` before designers/Writer read it; the Goose Solution Planner
and Chain Reaction Agent require Item Interaction Agent's registered
`goose_actions`/`possible_outcomes`. `GachoBadiCrew` enforces this order
in `executable/crew.py` (`run_personality_pass` → `run_relationship_pass`
→ `run_dev_time_pass` → `run_item_interaction_pass` → `run_playthrough`).

## `workflow/definitions/models_verification.py` (the verification model)

The workflow package's own vocabulary, deliberately separate from the
game's domain model (merging would pollute the game model with plumbing
and break portability):

- `Finding` — a single gap detected by a constraint.
- `GuardrailViolation` — a generic guardrail hit (token overrun, empty
  output, leaked template markers, leaked exception text).
- `CallRecord` / `ReviewResult` — attempt/verification bookkeeping.
  `call_id` is separate from `attempt` so "this call succeeded after N
  retries" is distinguishable from "this call never succeeded."

## Serialized output

`output/crew/` is the materialized form: one JSON file per generated
piece (personality, relationship, building design, appearance, item
interaction, task set, per-task tick, completion, verification summary),
indexed in order by `output/crew/manifest.json`. `executable/main.py`'s
`OutputWriter` names files `<nn>_<content_type>_<slug>.json` and clears
the directory at the start of each run, so the manifest is always
self-consistent with what is on disk.
