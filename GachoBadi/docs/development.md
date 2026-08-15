# Development

All commands run from `GachoBadi/`. The project is Python 3 stdlib-only;
there are no automated test suites, no lint configuration, and no build
step — the verification demo and the full game run are the smoke tests.

## Install dependencies before making changes

Base install is zero — no `requirements.txt`, no mandatory packages.
Optional dependencies are only needed for live LLM calls (the default
`mock` provider needs none):

```
pip install anthropic    # only if ANTHROPIC_API_KEY is set
pip install openai       # only if OPENAI_API_KEY is set
```

Provider selection (`api/llm_client.py`): Anthropic → OpenAI → mock,
unless `LLM_PROVIDER=mock|anthropic|openai` forces one. Model names are
configurable via `ANTHROPIC_MODEL` / `OPENAI_MODEL`. PyYAML is used by
`config_loader.py` if installed; a hand-rolled parser covers the flat
config subset otherwise.

## Verify changes

Smoke test the harness and the agents you touched:

```
python3 workflow/generic/demo_verify.py --agents none                 # harness loads
python3 workflow/generic/demo_verify.py --agents all                  # full verification demo
python3 workflow/generic/demo_verify.py --agents <agent>,<agent>      # subset
```

Then run the full game to confirm the crew still completes a playthrough
and regenerates `output/crew/`:

```
python3 executable/main.py
```

If you changed `workflow/` constraints, also run the goal loop for the
affected agent:

```
python3 workflow/goal_oriented/run_goal.py --agent <name> --list
```

## Known, intentional failure

`goose_solution_planner` never clears `no_unregistered_verb` (its
fallback uses the unregistered verb `"carries"`), and the goal loop stops
after 2 cycles with `stopped_reason='stagnant'`. This is a real
mock-provider ceiling, reproduced live during full playthroughs — do not
loosen constraints to hide it.

## Side effects to watch

- `executable/main.py` clears and rewrites `output/crew/`.
- Both CLIs append to `workflow/logs/changelog.jsonl` /
  `workflow/logs/goal_log.jsonl` (tracked files) and `run_goal.py` may
  edit `workflow/constraints/<agent>/constraints.yaml` (backing up the
  original as `.orig`). Restore these after smoke runs if the change was
  not the point of the run.
