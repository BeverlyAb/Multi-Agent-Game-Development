# CLI / Entry Points

All commands run from `GachoBadi/`. The scripts resolve the project root
onto `sys.path` themselves, so imports like `definitions.models` and
`api.llm_client` work regardless of the caller's directory. Exit status
is 0 on success, 1 on failure (e.g. an unknown `--agents` key or an
unmet goal).

## Run the full game

```
python3 executable/main.py
```

Runs `GachoBadiCrew` end to end — personality, relationships, dev-time
content, item interaction, and a full 18-task playthrough through game
completion — with verification on (the default). Regenerates
`output/crew/` (clears it first), writes `manifest.json`, and prints a
summary including the LLM provider in use and any unresolved verification
findings. Guaranteed to finish and produce output; a last-resort
try/except prints a `[FATAL]` line instead of crashing.

## Verification demo (`workflow/generic/demo_verify.py`)

The project's de-facto smoke test (no pytest tests exist). Wraps the
chosen agents against hand-built fixtures and prints the changelog.

```
python3 workflow/generic/demo_verify.py --list                        # print agent keys, exit
python3 workflow/generic/demo_verify.py                               # --agents all (default)
python3 workflow/generic/demo_verify.py --agents none                 # harness-load check only
python3 workflow/generic/demo_verify.py --agents goose_solution_planner
python3 workflow/generic/demo_verify.py --agents task_creator,chain_reaction
```

- `--agents` accepts `all` (default), `none`/`''` (a deliberately valid
  choice, not an error), or a comma-separated subset of the keys `--list`
  prints. An unknown key exits with status 1 and lists the valid ones.
- Known, intentional failure: `goose_solution_planner` does not clear
  `no_unregistered_verb` — its fallback text uses `"carries"`, which no
  fixture building registers. Do not "fix" it by loosening constraints.
- Every attempt is logged to `workflow/logs/changelog.jsonl` (append-only;
  this file is tracked, so restore it after smoke runs).

## Goal-oriented outer loop (`workflow/goal_oriented/run_goal.py`)

Drives one registered agent toward a goal by repeatedly running it and
tuning its `constraints.yaml` on disk.

```
python3 workflow/goal_oriented/run_goal.py --list
python3 workflow/goal_oriented/run_goal.py --agent chain_reaction
python3 workflow/goal_oriented/run_goal.py --agent task_creator --max-cycles 3
python3 workflow/goal_oriented/run_goal.py --agent goose_solution_planner \
    --forbidden-rules no_unregistered_verb --description "never invent a goose verb"
```

- `--agent` (required, unless `--list`), `--description` (free-text log
  label, never parsed), `--max-unresolved` (default 0 — fully clean),
  `--forbidden-rules` (comma-separated rule names that must never go
  unresolved), `--max-cycles` (default 5).
- Each cycle loads the agent's `constraints.yaml` fresh, runs it against
  the same fixture `demo_verify.py` uses, and if the goal is unmet bumps
  the worst offending rule's `priority_weights` and `max_retries`
  (capped) and writes the file back. The hand-authored original is
  preserved as `constraints.yaml.orig` on first touch, never overwritten.
- Every run starts from a fresh `workflow/logs/goal_log.jsonl`.
- The `goose_solution_planner` default goal stalls after 2 cycles
  (`stopped_reason='stagnant'`, exit 1) — a real mock-provider ceiling,
  not a bug.

## Web client

```
python3 -m http.server 8000
# open http://localhost:8000/web/index.html
```

Serve from `GachoBadi/` itself, never from `web/` (the browser normalizes
`../output/...` outside the server root and 404s). The client needs
`output/crew/` to exist first — run `python3 executable/main.py` once.

Controls: WASD/arrows to move; Honk (Space), Grab (E), Pick up (R),
Duck (Q), Dash (Shift). The Task panel shows which verbs the plan still
needs; the Lore panel shows the per-scene agent trail plus the workflow
verification block.
