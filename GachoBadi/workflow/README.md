# Agent Verification Workflow

A generic guardrail / verify / feedback loop that works on **any** agent
in this crew, added without changing a single line in `agents/`,
`crew.py`, or `main.py`.

## Two entry points, one core

Not every agent produces its "work" the same way, so there are two ways
in -- but both feed the exact same downstream machinery (guardrails,
gap-detection, priority scoring, changelog logging).

- **`generic/guarded_llm_client.py` (`GuardedLLMClient`)** -- for agents that
  call `self.llm.generate(system, prompt, fallback=...)`, the one
  interface `agents/base.py`'s `BaseAgent` gives every text-generating
  agent. Wraps that call: check → (if blocking issues) retry with
  feedback appended to the prompt → log → repeat up to `max_retries`.
  Drop-in: pass a `GuardedLLMClient` wherever an agent's constructor
  currently takes a raw `LLMClient`, and that agent's own file never
  needs to change.
- **`generic/guarded_output.py` (`verify_output`)** -- for agents whose work is a
  structured return value with no `generate()` call to intercept, e.g.
  `ChainReactionAgent` (its only randomness is
  `self.llm.choice(building.possible_outcomes)`). The caller runs the
  agent normally, flattens whatever it returned into plain text (the
  caller decides the format), and hands that text to `verify_output()`.
  One-shot only -- there's no prompt to inject retry feedback into.

```python
# input side (agent calls generate())
guarded = GuardedLLMClient(LLMClient(seed=7), constraints=SOME_CONSTRAINTS, context={...})
some_agent = SomeAgent(guarded)          # <- the only line that changes
some_agent.run(...)                       # agent's own code: untouched
guarded.result().accepted_all

# output side (agent doesn't call generate())
some_agent = SomeAgent(LLMClient(seed=7)) # agent's own code: untouched
output = some_agent.run(...)
result = verify_output(flatten(output), constraints=SOME_CONSTRAINTS, context={...})
result.accepted_all
```

## What's generic vs. what's per-agent

| Lives in | Knows about |
|---|---|
| `generic/guardrails.py` | Nothing agent-specific — only raw strings every call has (system/prompt/output, or just output for `verify_output`). Token-budget overrun, empty output, leaked `{template}` markers, leaked exception text. |
| `definitions/models_verification.py` | The shared vocabulary (`Finding`, `GuardrailViolation`, `CallRecord`, `ReviewResult`) every other file speaks — this workflow's own bookkeeping model, distinct from the project's top-level `definitions/models.py` (the actual game's Resident/Building/Task domain). Deliberately a separate file, not merged: merging would pollute the game's domain model with verification plumbing, and would break this package's portability to another project. |
| `generic/guarded_llm_client.py`, `generic/guarded_output.py` | The two loops themselves. Agent-agnostic — both only ever call `constraints.evaluate()`, never inspect a domain object directly. |
| `generic/changelog.py` | Append-only JSONL log of every attempt, with a plain-English justification for why it was accepted or retried. Agent-agnostic. |
| `constraints/<agent>_constraints.{py,yaml}` | Everything domain-specific, split in two: the `.yaml` holds **declarative values** (token budget, priority weights, `max_retries`); the `.py` holds **gap-detection logic** (regex extraction, word-overlap checks, whatever actually needs code) and imports the `.yaml`'s values in. See "Why the YAML/Python split" below. |

Constraint file **and YAML config names always end in `_constraints`**
(`goose_solution_planner_constraints.py`, not
`goose_solution_planner.py`) specifically so they can never be mistaken
for the agent module they constrain (`agents/runtime/goose_solution_planner_agent.py`)
when scanning file lists or import lines.

## Constraint files that exist today

- **`goose_solution_planner_constraints`** (input side) — 4 gap
  detectors: `no_unregistered_verb` (BLOCKING, priority `1000` — every
  `Goose: <verb>` line must use a verb from the building's registered
  `goose_actions`, the one rule this agent exists to enforce),
  `no_dialogue_leak` (BLOCKING — the goose never speaks),
  `has_at_least_one_verb_step` (BLOCKING — non-empty output with zero
  actionable verb steps leaves `DirectorAgent` nothing real to stage),
  `mentions_task_context` (ADVISORY — flags likely generic boilerplate).
- **`task_creator_constraints`** (input side) — 4 gap detectors:
  `mentions_both_residents` (BLOCKING), `no_mischief_tone` (BLOCKING,
  priority `950` — re-creates, in a properly-scoped place, a capability
  this project used to get from the now-removed Assignment #4
  Consistency Critic Agent), `mentions_building` (ADVISORY),
  `not_too_short` (ADVISORY).
- **`chain_reaction_constraints`** (output side, via `verify_output`) —
  4 gap detectors: `outcome_is_registered` (BLOCKING, priority `1000` —
  this agent's equivalent of `no_unregistered_verb`: the staged outcome
  must match one of `building.possible_outcomes` verbatim),
  `chain_effect_requires_other_resident` (BLOCKING), `max_two_steps`
  (BLOCKING — this agent's own documented cap), `step_actor_is_task_participant`
  (BLOCKING — every named actor must be the task's target or other
  resident, never an invented third name).

## Why the YAML/Python split

Early version of this package put everything — token budgets, priority
weights, *and* gap-detection logic — in one Python file per agent. Some
of that really is just data (two numbers for a token budget; a
rule-name → int mapping for priority weights), and forcing someone to
edit Python to change a threshold is unnecessary friction. But the gap
detectors themselves are genuine logic — regex-extracting the verb out
of a `"Goose: <verb> ..."` line, word-overlap between a backstory and a
screenplay, walking a dynamic list of chain-reaction actor names — none
of that reduces to a declarative `must_contain`/`must_not_contain` rule
without inventing a second, weaker programming language to express it
in. So: **values in YAML, logic in Python**, joined by
`constraints/config_loader.py`, which uses PyYAML if installed and falls
back to a small hand-rolled parser for the flat/one-level-nested subset
this project's configs actually use (so the package still runs with
zero setup, same philosophy as `api/llm_client.py`'s own provider
fallback).

Because of this split, most agents don't need a `priority_score()`
override at all — `AgentConstraints.priority_score()` already looks a
finding's rule name up in `priority_weights` (loaded straight from
YAML) before falling back to the plain BLOCKING/ADVISORY default. Only
override it in Python if an agent needs ranking logic a flat table
can't express.

## Adding a new agent

1. Does it call `self.llm.generate()`? If yes, use `GuardedLLMClient`
   (input side). If no (like `ChainReactionAgent`), use
   `guarded_output.verify_output()` (output side) and decide a plain-text
   flattening for whatever it returns.
2. Copy `constraints/goose_solution_planner_constraints.{py,yaml}` (input
   side) or `constraints/chain_reaction_constraints.{py,yaml}` (output
   side) as a template. **Name both files `<agent>_constraints.{py,yaml}`.**
3. In the `.yaml`: set `token_budget` from `gdd.txt`'s Technical Strategy
   table row for that agent (or a placeholder + comment if the agent
   makes no `generate()` call, like `chain_reaction_constraints.yaml`
   does), and any `priority_weights` that need to outrank the default.
4. In the `.py`: write `gap_detectors` — each is `(output_text: str,
   context: dict) -> List[Finding]`. Only check things genuinely true for
   that agent's own contract; don't duplicate what `generic/guardrails.py`
   already covers generically.
5. Wherever that agent is constructed, either wrap its `LLMClient` in a
   `GuardedLLMClient`, or call `verify_output()` on its return value
   after running it normally.

## Running the demo

```bash
cd GachoBadi
python3 workflow/generic/demo_verify.py                                       # all registered agents (default)
python3 workflow/generic/demo_verify.py --agents none                         # zero -- just checks the harness loads
python3 workflow/generic/demo_verify.py --agents goose_solution_planner       # exactly one
python3 workflow/generic/demo_verify.py --agents task_creator,chain_reaction  # a chosen set
python3 workflow/generic/demo_verify.py --list                                # print available agent keys and exit
```

`--agents` accepts `all` (default), `none`/`''` (a deliberately valid,
distinct choice, not an error), or a comma-separated subset of the keys
`--list` prints. An unknown key exits with status 1 and lists the valid
ones rather than silently running nothing or everything. Adding a new
agent's demo to `AGENT_DEMOS` in `generic/demo_verify.py` (alongside a new
constraint spec, per "Adding a new agent" above) makes it immediately
selectable by name — nothing else about `--agents` changes.

Wraps whichever agents you select against hand-built fixtures and prints
the changelog. With `--agents all` (or no flag):

- **Goose Solution Planner** (input side) — on a fresh checkout with no
  `ANTHROPIC_API_KEY`/`OPENAI_API_KEY` set (the default "mock"
  provider), this **fails to clear after all retries**. This is a real,
  reproducible finding, not a bug in the workflow: that agent's own
  deterministic fallback text includes a `"Goose: carries it toward
  {resident}."` line, and `"carries"` isn't a registered `goose_action`
  for the demo's fixture building. The retry loop can't fix it because
  the mock provider ignores the prompt/feedback entirely and always
  returns the same fixed fallback string — the feedback-driven retry
  only has teeth once a real LLM provider is configured, since only then
  does the appended feedback actually influence the next attempt's
  output. Whether to change the agent's own fallback template is a
  separate decision outside this workflow's scope — this package's job
  is to surface the finding, not silently patch around it.
- **Task Creator** (input side) — accepts cleanly; its fallback template
  already names both residents and the building by construction.
- **Chain Reaction** (output side) — accepts cleanly; whichever outcome
  the seeded random draw picks, it's always one of the two registered on
  the fixture's "Garden Hose Stand" building.

## Design decisions worth knowing about

- **Why wrap `LLMClient`, not each agent's `.run()`?** Wrapping `.run()`
  would need every agent's method signature to accept a "feedback" hint,
  which means touching every agent file — the opposite of generic.
  Wrapping the shared `generate()` seam means zero agent files change
  for the agents that have one; `verify_output()` covers the rest.
- **Why retry by appending feedback to the prompt, not changing
  `fallback`?** `fallback` is meant to be the deterministic,
  always-correct-by-construction backup a real LLM call falls back to on
  failure — mutating it on retry would make the "safe default" not
  actually safe. Feedback only ever changes the `prompt` sent to a real
  provider.
- **Why token budgets only flag *over*-use?** Using fewer tokens than
  budgeted is never a problem this workflow cares about; `gdd.txt`
  itself calls its budgets "rough, unvalidated planning estimates," so a
  moderate overrun (within `TokenBudget.tolerance`, default 1.5x) isn't
  flagged either — only a clear, order-of-magnitude-ish overrun is.
- **Why `call_id` separate from `attempt`?** So `ReviewResult` can tell
  "this logical call eventually succeeded after 2 retries" (fine) apart
  from "this logical call never succeeded" (the thing worth surfacing to
  a human) — without a shared id, every retry attempt looks like an
  independent, still-failing call.
- **Why is `definitions/models_verification.py` a separate file from
  the project's own top-level `definitions/models.py`?** See the table
  above — different domains, and merging would hurt this package's
  portability. (Named `models_verification.py`, and in a `definitions/`
  folder of its own inside `workflow/`, specifically so neither name nor
  path is ever confused with the game's own `definitions/models.py`.)
