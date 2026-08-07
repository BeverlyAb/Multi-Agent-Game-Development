"""Agent verification workflow -- generic guardrail/verify/feedback loop
with two entry points, covering every agent in this crew regardless of
how it produces its work:

  - guarded_llm_client.GuardedLLMClient wraps the ONE interface every
    text-generating agent shares: BaseAgent.llm.generate(system, prompt,
    fallback=...) (see agents/base.py). Loops: call -> check -> (if
    blocking issues) retry with feedback appended to the prompt -> log.
  - guarded_output.verify_output() covers agents with no generate() call
    at all (e.g. ChainReactionAgent, whose only randomness is
    self.llm.choice()) -- a one-shot check against a flattened text
    projection of whatever the agent returned.

Both feed the same downstream machinery (guardrails.py,
constraints/base.py's AgentConstraints, changelog.py), so "generic
across all the agents" holds regardless of which entry point a given
agent needs -- no agent's own code has to change either way.

This package is entirely additive: it does not modify agents/, crew.py,
or main.py. Wiring it into the live crew (passing a GuardedLLMClient
instead of a raw LLMClient into an agent's constructor, or calling
verify_output() after an agent runs) is left for whoever decides to do
it -- see demo_verify.py for a worked example against three real agents
from this crew, and README.md for the full design writeup.
"""
