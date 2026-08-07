"""The 'goal oriented' meta-agent: an OUTER loop wrapped around the two
existing entry points (generic.guarded_llm_client.GuardedLLMClient,
generic.guarded_output.verify_output). Those already do run -> check ->
retry-with-feedback for ONE call; this package adds the layer above
that: run -> check the goal -> retune that agent's own constraints.yaml
-> run again, across full CYCLES, until the goal is met, capped out, or
found un-reachable by constraint-tuning alone.

Three files:
  - goal.py       the Goal/GoalResult/CycleLog data shapes -- what "the
                   outcome I want" means as data, not prose.
  - registry.py   maps each of the three already-guarded agents' keys to
                   what this package needs to re-run them: the demo
                   runner, the original AgentConstraints (for its
                   agent_name/gap_detectors, which never change), and its
                   constraints.yaml path.
  - agent.py      GoalOrientedAgent -- the loop itself, and the only
                   thing in this workflow package that ever writes to a
                   constraints.yaml file rather than just reading it.
  - goal_log.py   append-only audit trail for this OUTER loop, parallel
                   to generic/changelog.py's own trail for the INNER
                   (per-call) loop.
  - run_goal.py   the CLI -- "an interface I can prompt and start the
                   cycle."

See workflow/README.md's "Goal-oriented agent" section for the full
design writeup, including why goals are a small structured spec rather
than free-form natural language, and what constraint-tuning can and
cannot fix (the mock-provider ceiling already documented for the
demo agents).
"""
