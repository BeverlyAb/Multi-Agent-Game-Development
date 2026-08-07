"""Shared data structures for the verification workflow -- this
package's own equivalent of definitions/models.py: the blackboard passed
between guardrails.py, constraints/base.py, and guarded_llm_client.py.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List


class Severity(str, Enum):
    # A BLOCKING finding/violation must be fixed before the output is
    # accepted -- it triggers a retry (with feedback) if any remain.
    BLOCKING = "blocking"
    # An ADVISORY finding is logged and surfaced but never blocks
    # acceptance -- useful for style/quality notes a human should see
    # without stalling the pipeline over them.
    ADVISORY = "advisory"


@dataclass
class GuardrailViolation:
    """A violation of a GENERIC, agent-agnostic rule (guardrails.py) --
    e.g. a token-budget overrun or an empty response. Distinct from
    Finding (below), which is agent-SPECIFIC and comes from a constraint
    file's gap_detectors."""

    guardrail: str  # short id, e.g. "token_budget_output"
    message: str
    severity: Severity = Severity.BLOCKING


@dataclass
class Finding:
    """One issue a constraint file's gap-detection pass found in a
    specific agent's output. `priority` is filled in by that agent's
    AgentConstraints.priority_score() -- two agents can (and should)
    weigh the same rule name differently."""

    rule: str  # short id, e.g. "no_unregistered_verb"
    message: str
    severity: Severity = Severity.ADVISORY
    priority: int = 0


@dataclass
class CallRecord:
    """One attempt at one generate() call -- the unit both the changelog
    and ReviewResult are built from. `call_id` is shared by every retry
    attempt of the SAME logical generate() invocation (so they can be
    grouped back together); `attempt` starts at 1 within a call_id, and a
    value > 1 means an earlier attempt on this same call_id was rejected
    and retried with feedback appended to the prompt."""

    agent_name: str
    call_id: int
    attempt: int
    system: str
    prompt: str
    output: str
    input_tokens_est: int
    output_tokens_est: int
    guardrail_violations: List[GuardrailViolation] = field(default_factory=list)
    findings: List[Finding] = field(default_factory=list)
    accepted: bool = False

    def blocking_issues(self) -> List[str]:
        issues = [v.message for v in self.guardrail_violations if v.severity == Severity.BLOCKING]
        issues += [f.message for f in self.findings if f.severity == Severity.BLOCKING]
        return issues


@dataclass
class ReviewResult:
    """The GuardedLLMClient's running summary across every generate()
    call it has guarded so far -- what main.py-style callers read to
    decide whether an agent's overall output for a run is trustworthy."""

    agent_name: str
    calls: List[CallRecord] = field(default_factory=list)

    @property
    def accepted_all(self) -> bool:
        """True only if every logical call_id's FINAL attempt was
        accepted -- a call_id with retries still counts as accepted here
        as long as it eventually cleared, since retrying-then-succeeding
        is the workflow working as intended, not a failure."""
        if not self.calls:
            return False
        last_by_call: Dict[int, CallRecord] = {}
        for c in self.calls:
            last_by_call[c.call_id] = c  # later attempts overwrite earlier ones
        return all(c.accepted for c in last_by_call.values())

    @property
    def retried_count(self) -> int:
        return sum(1 for c in self.calls if c.attempt > 1)

    def unresolved(self) -> List[Finding]:
        """Blocking findings still present on the LAST attempt of any
        call_id that was never accepted -- i.e. max_retries was exhausted
        without clearing them. Findings from earlier, already-superseded
        attempts of the same call_id are deliberately excluded."""
        last_by_call: Dict[int, CallRecord] = {}
        for c in self.calls:
            last_by_call[c.call_id] = c
        out: List[Finding] = []
        for c in last_by_call.values():
            if not c.accepted:
                out.extend(f for f in c.findings if f.severity == Severity.BLOCKING)
        return out
