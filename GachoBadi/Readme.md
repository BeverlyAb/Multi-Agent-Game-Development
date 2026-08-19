# Gachō Badi — GER Pipeline (Assignment #6)

**What this is.** A multi-agent neighborhood game (Gachō Badi) where 13 agents produce quests, dialog, and scene events for the player. Assignment #6 asks us to build a **GER pipeline** — Generator → Evaluator → Refiner — with a **Circuit Breaker** — to automatically catch rule-breaking content before it reaches players.

**The problem.** Some generated content is broken (e.g. an agent uses a verb that no building registered — "carries it toward the cottage" when the building only knows `dash`, `drop`, `grab`). Manually reviewing every piece is slower than writing the content yourself.

**The fix.** The pipeline catches those violations automatically and either fixes them or escalates when it can't.

## Pre-Build Declaration

1. **What content type does the game generate?**
   Quest tasks — conversation prompts and verb actions that tell the player what to do at each building (e.g. "Grab a bundle of old letters from the counter").

2. **What specific rule must every piece satisfy?**
   Every verb in a task must be one the building actually registered in its Item Interaction schema. The GDD forbids inventing behavior: agents must never use a verb outside the `possible_verbs` set declared by the building.

3. **What does a failure look like?**
   A task says "Carries it toward the cottage" but the building only registered `['dash', 'drop', 'grab']`. The player tries to perform an action the game doesn't support — the scene breaks, the goose can't interact, the quest is stuck.

## How the pipeline works

```text
┌────────────┐    ┌────────────┐    ┌────────────┐    ┌────────────────┐
│  Generator │ →  │  Evaluator │ →  │  Refiner   │ →  │  Output        │
│  (task     │    │  (checks   │    │  (retries  │    │  (clean task)  │
│  content)  │    │  GDD rule) │    │  with fix) │    │                │
└────────────┘    └─────┬──────┘    └────────────┘    └────────────────┘
                        │
                   ┌────▼─────┐
                   │  Circuit  │  ← loop can't self-correct?
                   │  Breaker  │    escalates to human review
                   └──────────┘
```

- **Generator** — produces quest content (task prompts, verb actions) from the agent crew's output.
- **Evaluator** — checks every verb in the task against the building's registered `possible_verbs` from `constraints.yaml`. The rule is traceable to the GDD's "no invented behavior" contract.
- **Refiner** — retries with corrective feedback when the evaluator flags a violation.
- **Circuit Breaker** — stops the loop after `max_retries` and escalates when the pipeline can't self-correct.

## Highlighted components

### `/workflow` — The pipeline and verification engine

Everything lives in `workflow/`. The GER pipeline sits alongside the existing constraint/gap-detection system.

```
workflow/
├── constraints/            ← per-agent rule definitions
│   ├── chain_reaction/     # BLOCKING: outcome must be registered
│   ├── task_creator/       # BLOCKING: mentions both residents, no mischief tone
│   └── goose_solution_planner/ # BLOCKING: no_unregistered_verb (weight 1000)
├── goal_oriented/          ← Assignment #5: goal-oriented agent loop
├── generic/                ← agent-agnostic verification
├── definitions/            ← shared workflow data models
└── logs/                   ← changelog.jsonl, goal_log.jsonl
```

**Key design:** Values live in `constraints.yaml` (declarative — weights, token budgets, retry limits), logic lives in `constraints.py` (regex verb extraction, tone scanning, outcome matching). The GDD's own risk ranking drives the priority weights — the pipeline enforces exactly what the design doc says, no more, no less.

**How the existing system feeds in:** The constraint folder from Assignment #5 already contains the Evaluator's rule logic — each agent's `constraints.py` already knows how to detect the violations the GER Evaluator checks. The GER pipeline wraps this into the Generator → Evaluator → Refiner loop with a Circuit Breaker.

### `AGENTS.md` — The rules the pipeline can't break

AGENTS.md defines the coding and behavioral rules every change must follow. For the GER pipeline, the relevant rules are:

- **Agents must never invent verbs or outcomes outside what the Item Interaction Agent registered.** This is the Evaluator's core check — it's not invented for the assignment; it's already a hard rule in AGENTS.md.
- **Values in `constraints.yaml`, logic in `constraints.py`.** The pipeline respects this split: the Evaluator reads rules from YAML, executes checks in Python.
- **Keep `workflow/generic/` agent-agnostic; domain-specific gap detection goes in `workflow/constraints/<agent>/`.** The GER pipeline follows this structure.
- **Every agent call supplies a `fallback` string; the crew must never crash without producing output.** The Circuit Breaker embodies this — it doesn't crash; it escalates gracefully.
- **Before completing a task:** run `python3 workflow/generic/demo_verify.py --agents all` and `python3 executable/main.py`.

### `/contract` — How changes get reviewed

The contract directory is where human↔agent collaboration happens for any change. When modifying the GER pipeline, the process is:

```
docs/contract/
├── template.md          ← reusable contract skeleton
└── <ID>/
    ├── contract.md      ← what to do, constraints, acceptance criteria
    ├── review.md        ← reviewer's findings (P0-P3 severity)
    └── response.md      ← implementer's disposition of each finding
```

1. The **human writes** a `contract.md` (or clones `template.md`) describing the problem, desired outcome, and constraints.
2. The **reviewer** reads it and writes a `review.md` with severity-rated findings.
3. The **implementer** fixes the findings, commits, and writes a `response.md` showing each finding is resolved.
4. The contract Status (`NEEDS HUMAN INPUT` / `READY FOR APPROVAL` / `CLOSED`) tracks where things stand.

This keeps changes scoped, reviewed, and auditable — no unreviewed code lands on main.

## What the system already finds in real runs

```
[Goose Solution Planner][VERIFY] task #9 unresolved: [no_unregistered_verb]
  line uses verb 'carries', which is not in the registered set
  ['dash', 'drop', 'grab']
```

That's a real GDD violation: the Goose Solution Planner's fallback text always includes `Goose: carries it toward {resident}.`, but `"carries"` is never a registered verb. The existing constraint system catches this automatically; without it, a human would have to read every generated task to find the same drift. The Task Creator and Chain Reaction agents pass clean — the system only flags what's actually wrong.

## Further reading

- `workflow/README.md` — deep design doc for the full `workflow/` package
- `AGENTS.md` — repo-wide rules and governance
- `docs/contract/` — per-ID contract workflow
- `design_review/gdd.txt` — the game design document (Draft #11)
