"""Agent verification workflow -- generic guardrail/verify/feedback loop
with two entry points, covering every agent in this crew regardless of
how it produces its work:

  - generic.guarded_llm_client.GuardedLLMClient wraps the ONE interface
    every text-generating agent shares: BaseAgent.llm.generate(system,
    prompt, fallback=...) (see agents/base.py). Loops: call -> check ->
    (if blocking issues) retry with feedback appended to the prompt ->
    log.
  - generic.guarded_output.verify_output() covers agents with no
    generate() call at all (e.g. ChainReactionAgent, whose only
    randomness is self.llm.choice()) -- a one-shot check against a
    flattened text projection of whatever the agent returned.

Both feed the same downstream machinery (generic/guardrails.py,
constraints/base.py's AgentConstraints, generic/changelog.py, and the
shared vocabulary in definitions/models_verification.py), so "generic
across all the agents" holds regardless of which entry point a given
agent needs -- no agent's own code has to change either way.

Three subpackages:
  - generic/       the agent-AGNOSTIC engine (see generic/__init__.py)
  - constraints/    one <agent>_constraints.{py,yaml} pair per guarded agent
  - definitions/    models_verification.py, this workflow's own shared
                    data model -- distinct from the game's own
                    definitions/models.py one level up

Wired into the live crew: executable/crew.py's GachoBadiCrew(verify=True)
(the default) wraps GooseSolutionPlannerAgent and TaskCreatorAgent in a
GuardedLLMClient and checks ChainReactionAgent via verify_output() on
every real playthrough, not just the demo -- see that file's
_resolve_or_retire and run_playthrough. See generic/demo_verify.py for a
standalone worked example against hand-built fixtures, and README.md for
the full design writeup.
"""