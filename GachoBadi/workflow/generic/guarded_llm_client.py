"""The generic engine: a drop-in wrapper around api.llm_client.LLMClient
that guards, verifies, and gives feedback on every generate() call an
agent makes -- without that agent's own code changing at all.

Why this is the right seam: every agent in this crew (agents/base.py's
BaseAgent) only ever talks to its LLM through self.llm.generate(system,
prompt, fallback=...), plus RelationshipAgent's self.llm.choice(). That
is the ONE interface shared by every current and future agent regardless
of domain. Wrapping it here means "loop through calls to agents, ensure
guardrails, verify their work, provide feedback" is implemented exactly
once, generically, instead of once per agent.

Usage (see demo_verify.py for a full worked example):
    base = LLMClient(seed=7)
    guarded = GuardedLLMClient(base, constraints=GOOSE_SOLUTION_PLANNER_CONSTRAINTS,
                                context={"legal_verbs": building.goose_actions,
                                         "task_description": task.description})
    planner = GooseSolutionPlannerAgent(guarded)   # <- agent's own code is untouched
    plan = planner.run(task, [building])
    print(guarded.result().accepted_all)
"""
from __future__ import annotations

import itertools
from typing import Dict, List, Optional

from .changelog import append_changelog
from ..constraints.base import AgentConstraints
from .guardrails import GENERIC_OUTPUT_GUARDRAILS, check_token_budget, est_tokens
from ..definitions.models_verification import CallRecord, ReviewResult, Severity

_call_id_counter = itertools.count(1)


class GuardedLLMClient:
    """Duck-types api.llm_client.LLMClient's public surface (generate,
    choice, sample, provider) so any agent that accepts an LLMClient in
    its constructor accepts this instead, with no other change."""

    def __init__(self, base, constraints: AgentConstraints, context: Optional[Dict] = None, log_path: Optional[str] = None):
        self.base = base
        self.constraints = constraints
        self.context = context or {}
        self.log_path = log_path  # None -> changelog.py's default path
        self._result = ReviewResult(agent_name=constraints.agent_name)

    # -- passthroughs, so this is a true drop-in replacement --------
    @property
    def provider(self) -> str:
        return self.base.provider

    def choice(self, options):
        return self.base.choice(options)

    def sample(self, options, k):
        return self.base.sample(options, k)

    # -- the guarded path ---------------------------------------------
    def generate(self, system: str, prompt: str, *, fallback: str) -> str:
        call_id = next(_call_id_counter)
        feedback = ""
        output = fallback

        for attempt in range(1, self.constraints.max_retries + 2):  # +1 initial +N retries
            effective_prompt = prompt if not feedback else (
                f"{prompt}\n\n"
                f"Your previous attempt had these issues -- fix them in this attempt:\n{feedback}"
            )
            output = self.base.generate(system, effective_prompt, fallback=fallback)

            record = CallRecord(
                agent_name=self.constraints.agent_name,
                call_id=call_id,
                attempt=attempt,
                system=system,
                prompt=effective_prompt,
                output=output,
                input_tokens_est=est_tokens(system) + est_tokens(effective_prompt),
                output_tokens_est=est_tokens(output),
            )
            record.guardrail_violations = check_token_budget(
                system, effective_prompt, output, self.constraints.token_budget
            ) + [v for check in GENERIC_OUTPUT_GUARDRAILS for v in check(output)]
            record.findings = self.constraints.evaluate(output, self.context)

            blocking = record.blocking_issues()
            record.accepted = not blocking

            self._result.calls.append(record)
            log_kwargs = {} if self.log_path is None else {"log_path": self.log_path}
            append_changelog(record, **log_kwargs)

            if record.accepted or attempt > self.constraints.max_retries:
                break
            feedback = "\n".join(f"- {msg}" for msg in blocking)

        return output

    def result(self) -> ReviewResult:
        return self._result
