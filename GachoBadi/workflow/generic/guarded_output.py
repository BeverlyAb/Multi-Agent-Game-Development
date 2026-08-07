"""The second generic entry point, for agents whose "work" isn't raw LLM
text but a structured return value -- e.g. ChainReactionAgent, whose only
randomness is self.llm.choice(building.possible_outcomes), never a
generate() call. GuardedLLMClient (guarded_llm_client.py) can't guard
such an agent: there is no generate() call to intercept, so there is
nothing to wrap around the agent's constructor.

Instead, the caller runs the agent normally, flattens whatever it
returned into a plain text projection (the caller decides the format --
see constraints/chain_reaction/constraints.py for the convention it
expects), and hands that text to verify_output() here. Everything below
that point -- GENERIC_OUTPUT_GUARDRAILS, gap_detectors, priority scoring,
changelog logging -- is the exact same machinery guarded_llm_client.py
uses, just entered from the output side instead of wrapping the input
side. See workflow/README.md's "Two entry points, one core" section.

Deliberately NO retry-with-feedback loop here: there's no prompt to
inject corrections into. An agent like ChainReactionAgent would need to
be re-invoked entirely (a fresh random draw from self.llm.choice()) to
possibly get a different, passing answer -- whether to do that, and how
many times, is the caller's decision, not this function's.
"""
from __future__ import annotations

import itertools
from typing import Any, Dict, Optional

from .changelog import append_changelog
from ..constraints.base import AgentConstraints
from .guardrails import GENERIC_OUTPUT_GUARDRAILS, est_tokens
from ..definitions.models_verification import CallRecord, ReviewResult

_call_id_counter = itertools.count(1)


def verify_output(
    output_text: str,
    constraints: AgentConstraints,
    context: Optional[Dict[str, Any]] = None,
    result: Optional[ReviewResult] = None,
    log_path: Optional[str] = None,
) -> ReviewResult:
    """One-shot verification pass. Appends a single CallRecord (attempt
    1, always -- there is no retry loop) to `result` (or a fresh
    ReviewResult if none was passed in, so repeated calls can share one
    running result the same way GuardedLLMClient.result() does), logs
    it to the changelog, and returns the ReviewResult for the caller to
    inspect via .accepted_all / .unresolved()."""
    result = result if result is not None else ReviewResult(agent_name=constraints.agent_name)
    call_id = next(_call_id_counter)

    record = CallRecord(
        agent_name=constraints.agent_name,
        call_id=call_id,
        attempt=1,
        system="",
        prompt="",
        output=output_text,
        input_tokens_est=0,  # no prompt exists for a structured-output agent
        output_tokens_est=est_tokens(output_text),
    )
    record.guardrail_violations = [v for check in GENERIC_OUTPUT_GUARDRAILS for v in check(output_text)]
    record.findings = constraints.evaluate(output_text, context or {})
    record.accepted = not record.blocking_issues()

    result.calls.append(record)
    append_changelog(record, **({} if log_path is None else {"log_path": log_path}))
    return result
