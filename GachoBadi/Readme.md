# Gachō Badi — GER Pipeline and Style Guide Agent (Assignment #6 + #7)

**What this is.** A multi-agent neighborhood game (Gachō Badi) where agents produce quests, dialog, and scene events for the player. Assignment #6 builds a **GER pipeline** — Generator → Evaluator → Refiner — with a **Circuit Breaker** — to automatically catch rule-breaking content before it reaches players. Assignment #7 adds a **Style Guide Agent** that enforces aesthetic and narrative rules, ensuring all generated content matches the game's specific tone, vocabulary, and formatting conventions.

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
                         │
                    ┌────▼──────────────────────────┐
                    │   Style Guide Agent (Assignment #7) │
                    │  (checks tone, vocabulary,   │
                    │   formatting, fixes violations)   │
                    └───────────────────────────────┘
```

- **Generator** — produces quest content (task prompts, verb actions) from the agent crew's output.
- **Evaluator** — checks every verb in the task against the building's registered `possible_verbs` from `constraints.yaml`. The rule is traceable to the GDD's "no invented behavior" contract.
- **Refiner** — retries with corrective feedback when the evaluator flags a violation.
- **Circuit Breaker** — stops the loop after `max_retries` and escalates when the pipeline can't self-correct.
- **Style Guide Agent** (Assignment #7) — enforces GDD-style rules on all generated content: tone consistency, vocabulary accuracy, and formatting conventions. Ensures content matches the cozy, community-building tone where the goose is a quiet helper rather than mischief-maker.

## Highlighted components

### `/workflow` — The pipeline and verification engine

Everything lives in `workflow/`. The GER pipeline sits alongside the existing constraint/gap-detection system.

```
workflow/
├── constraints/            ← per-agent rule definitions
│   ├── chain_reaction/     # BLOCKING: outcome must be registered
│   ├── task_creator/       # BLOCKING: mentions both residents, no mischief tone
│   ├── goose_solution_planner/ # BLOCKING: no_unregistered_verb (weight 1000)
│   └── style_guide_agent/  # Assignment #7: enforces tone, vocabulary, formatting
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
- **Style Guide Agent (Assignment #7) must enforce specific aesthetic and narrative rules:**
  - Content must maintain the game's community-oriented, cozy tone
  - No mischief or chaotic behavior (goose is a quiet community-builder, not a "untitled goose game")
  - Dialogue must be dry and understated, not overly enthusiastic
  - Use specific GDD terminology for relationships (e.g., "drifted apart" not "estranged")
  - Reference specific building types, item functionality, and role terminology
  - Task descriptions must be concise and action-oriented
  - Content must follow GDD formatting conventions for dialogue and narrative
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

### Assignment #7: Style Guide Agent

The Style Guide Agent adds a new layer of automated quality control that enforces GDD-style rules on all generated content. It ensures that every piece of game content matches the specific aesthetic and narrative conventions of Gachō Badi — a cozy, community-building game where the goose helps residents reconnect rather than cause mischief.

**What it checks:**
- **Tone:** Is the content community-oriented and cozy? Does it avoid excessive enthusiasm?
- **Vocabulary:** Are specific GDD terms used correctly? Are there any "generic" phrases that could apply to any game?
- **Formatting:** Does it follow GDD conventions for dialogue, narrative, and task descriptions?

**How it works:**
- An Evaluator Agent analyzes content against style guide rules and outputs a SCORE (1-10) and REASON for any violations
- A Refiner Agent takes the Evaluator's feedback and automatically rewrites content to score 10/10
- The agents work independently without human intervention, as required by the assignment
- Demonstrations show real before/after content transformations for tone, vocabulary, and formatting violations

**File structure:**
- `workflow/constraints/style_guide_agent/evaluator_agent.py` — Evaluator Agent implementation
- `workflow/constraints/style_guide_agent/refiner_agent.py` — Refiner Agent implementation
- `workflow/constraints/style_guide_agent/style_guide_rules.py` — Style guide rules and GDD references
- `workflow/constraints/style_guide_agent/demo.py` — Demonstration of style guide in action
- `workflow/constraints/style_guide_agent/integration_demo.py` — Pipeline integration example

**Why it matters:**
Without the Style Guide Agent, generated content might drift into overly enthusiastic dialogue, generic vocabulary, or improper formatting — breaking the cozy, low-stakes tone that defines Gachō Badi. The agent ensures consistency across all generated quests, dialogue, and scenes.

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
- `docs/gdd.txt` — the game design document (Draft #11)
