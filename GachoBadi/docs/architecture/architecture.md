# Architecture

Gachō Badi is a direct-execution pipeline, not a server: a Python 3 crew
orchestrates 13 agents that generate game content, a verification layer
checks that output against the game design doc, and a Phaser 3 client
renders the result. No framework, no mandatory third-party packages, no
database — the project runs on the Python 3 standard library only.

```
design_review/gdd.txt (source of truth)
        │  read by
        ▼
workflow/ (verification + goal-oriented outer loop)
        │  reads/writes constraint configs, guards agents
        ▼
executable/main.py → executable/crew.py (GachoBadiCrew)
        │  orchestrates
        ▼
agents/runtime/ + agents/dev_time/ (13 agents, all BaseAgent)
        │  call
        ▼
api/llm_client.py (Anthropic → OpenAI → deterministic mock fallback)
        │  produce
        ▼
definitions/models.py (shared data models)
        │  serialized by
        ▼
output/crew/ (one JSON per piece + manifest.json)
        │  fetched by
        ▼
web/ (Phaser 3 client: index.html + game.js)
```

## Layers

- **`agents/`** — the game's agent implementations, all extending
  `agents/base.py`'s `BaseAgent` (role/goal/backstory/run, plus a shared
  `self.llm`). `agents/runtime/` runs live during playthroughs;
  `agents/dev_time/` produces authored content.
- **`api/`** — `llm_client.py`, the shared LLM layer. Providers are
  tried in order: Anthropic, OpenAI, then the deterministic `mock`
  fallback (default; zero setup). Every `generate()` call takes a
  `fallback` string so the crew always produces output even with no API
  key and no SDK installed. `LLM_PROVIDER` forces a provider;
  `ANTHROPIC_MODEL` / `OPENAI_MODEL` pick the model.
- **`definitions/`** — shared domain data models (the crew's
  "blackboard"), passed between agents. See `docs/domain-models.md`.
- **`executable/`** — `crew.py` defines `GachoBadiCrew`, which runs the
  personality, relationship, dev-time, and item-interaction passes and
  then the full playthrough loop (task sets → 75% threshold → backlog
  mop-up → game completion). `main.py` is the entry point; it runs the
  crew and writes one JSON file per generated piece into `output/crew/`
  plus a `manifest.json`.
- **`workflow/`** — the verification layer, added as a wrapper without
  touching `agents/`, `crew.py`, or `main.py`:
  - `generic/` — the guardrail / verify / feedback loop.
    `GuardedLLMClient` wraps the `generate()` seam for agents that call
    it; `verify_output()` checks structured return values for agents that
    don't. Both feed the same downstream machinery (guardrails,
    gap-detection, priority scoring, append-only JSONL changelog).
  - `constraints/<agent>/` — per-agent gap detectors split into
    `constraints.yaml` (declarative values: token budgets, priority
    weights, `max_retries`) and `constraints.py` (regex/logic), joined
    by `constraints/config_loader.py`.
  - `goal_oriented/` — the outer loop: repeatedly runs an agent against
    the fixed demo fixture, checks a goal, and edits that agent's
    `constraints.yaml` on disk until the goal is met, a cycle cap is
    hit, or it detects stagnation.
  - `definitions/models_verification.py` — this layer's own bookkeeping
    model (`Finding`, `GuardrailViolation`, `CallRecord`,
    `ReviewResult`), deliberately separate from the game's domain model.
- **`web/`** — Phaser 3 client that fetches `output/crew/manifest.json`
  plus every file it lists and reassembles them into one scene per
  resolved task. DOM-overlay HUD pattern shared with the sibling game
  projects. Must be served from `GachoBadi/` (not `web/`) so the
  `../output/` fetch resolves.

## Verification design (the part most architectural changes affect)

Two entry points, one core:

- **Input side** — agents that call `self.llm.generate(system, prompt,
  fallback=...)`. Pass a `GuardedLLMClient` to the agent's constructor
  instead of a raw `LLMClient`; the agent's own file never changes. It
  checks the output, retries with feedback appended to the prompt up to
  `max_retries`, and logs every attempt.
- **Output side** — agents that return a structured value with no
  `generate()` call (e.g. `ChainReactionAgent`, whose only randomness is
  `self.llm.choice(...)`). The caller runs the agent normally, flattens
  the return into plain text, and hands it to `verify_output()`.

Per-agent constraint folders live under `workflow/constraints/<agent>/`
so the import path (`workflow.constraints.<agent>.constraints`) can never
be confused with the agent module it constrains.

Why the YAML/Python split: token budgets and priority weights are plain
data (edit YAML); gap detection is real logic — regex verb extraction,
tone-word scanning, outcome matching — that a declarative
`must_contain`/`must_not_contain` table can't express without inventing a
weaker language. `config_loader.py` uses PyYAML if installed and falls
back to a small hand-rolled parser for the flat subset the configs use.

Why the goal loop gives up: constraint tuning has a ceiling. The mock
LLM provider returns its `fallback` verbatim regardless of the prompt, so
tuning only affects a real provider's attempts. When a cycle's unresolved
rules come back byte-for-byte identical, the loop stops rather than
burning its budget.

## Deep dives

- `workflow/README.md` — the full design document for the workflow
  package (inner loop, YAML/Python split, goal-oriented outer loop).
- `Readme.md` — project overview, real-run transcripts, and screenshots.
- `design_review/gdd.txt` — the game design doc every constraint is
  traced back to.

Read the relevant document before making architectural changes.
