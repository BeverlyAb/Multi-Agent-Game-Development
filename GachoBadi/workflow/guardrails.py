"""GENERIC guardrails -- checks that apply to every agent's generate()
call regardless of that agent's domain (personality, tasks, dialogue,
whatever). Nothing in this file knows what a "Resident" or a "Task" is;
anything that does belongs in a constraint file's gap_detectors instead
(see constraints/base.py). This is what "generic enough to work on all
the agents" actually means in code: these functions take only the raw
strings every generate() call already has (system/prompt/output), never
a domain object.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

from .verification_models import GuardrailViolation, Severity

# Rough chars-per-token heuristic (no tokenizer dependency, same spirit as
# gdd.txt's own "Token budgets below are rough, unvalidated planning
# estimates, not measured data" -- this workflow doesn't pretend to be
# more precise than the budgets it's checking against).
_CHARS_PER_TOKEN = 4


def est_tokens(text: str) -> int:
    return max(1, len(text) // _CHARS_PER_TOKEN)


@dataclass
class TokenBudget:
    """Mirrors one row of gdd.txt's Technical Strategy budget table --
    construct one of these per agent from that table's Input/Output
    Budget columns."""

    input_max: int
    output_max: int
    # How far over input_max/output_max is tolerated before flagging --
    # the GDD's own budgets are stated as rough estimates, not hard caps,
    # so a small overrun isn't a real problem; a 2x overrun usually is.
    tolerance: float = 1.5


def check_token_budget(
    system: str, prompt: str, output: str, budget: TokenBudget
) -> List[GuardrailViolation]:
    """Only flags OVER-budget usage -- using fewer tokens than budgeted
    is never a problem this workflow cares about, only cost/latency
    overruns are."""
    violations: List[GuardrailViolation] = []
    input_tokens = est_tokens(system) + est_tokens(prompt)
    output_tokens = est_tokens(output)
    if input_tokens > budget.input_max * budget.tolerance:
        violations.append(
            GuardrailViolation(
                guardrail="token_budget_input",
                message=(
                    f"input ~{input_tokens} tokens exceeds budget {budget.input_max} "
                    f"by more than {budget.tolerance}x"
                ),
            )
        )
    if output_tokens > budget.output_max * budget.tolerance:
        violations.append(
            GuardrailViolation(
                guardrail="token_budget_output",
                message=(
                    f"output ~{output_tokens} tokens exceeds budget {budget.output_max} "
                    f"by more than {budget.tolerance}x"
                ),
            )
        )
    return violations


def check_non_empty(output: str) -> List[GuardrailViolation]:
    if not output or not output.strip():
        return [
            GuardrailViolation(
                guardrail="non_empty_output",
                message="generate() returned empty or whitespace-only text",
            )
        ]
    return []


def check_no_placeholder_leak(output: str) -> List[GuardrailViolation]:
    """Catches an agent (or its fallback f-string) accidentally leaving a
    template marker uninterpolated -- e.g. a stray '{resident}' that was
    supposed to be filled in. This is agent-agnostic: every agent in this
    crew builds its fallback from an f-string or .format() call, so a
    literal brace pair surviving into the final text is always a bug,
    never legitimate content."""
    if re.search(r"\{[a-zA-Z_][a-zA-Z0-9_]*\}", output):
        return [
            GuardrailViolation(
                guardrail="uninterpolated_placeholder",
                message="output contains an apparently-uninterpolated '{...}' template marker",
            )
        ]
    return []


def check_no_exception_leak(output: str) -> List[GuardrailViolation]:
    """Catches a raw Python exception/traceback ending up embedded in
    generated text -- e.g. a bug elsewhere stringifying an exception
    object into a fallback instead of raising it. A real agent output
    should never contain the literal word 'Traceback' or a
    '<...Error: ...>' repr."""
    if "Traceback (most recent call last)" in output or re.search(r"\b\w*Error\b:", output):
        return [
            GuardrailViolation(
                guardrail="exception_leak",
                message="output appears to contain a raw exception/traceback instead of generated content",
            )
        ]
    return []


# Guardrails that only need `output` -- run for every agent, every call,
# with no per-agent configuration. check_token_budget is run separately
# by GuardedLLMClient since it additionally needs each agent's own
# TokenBudget.
GENERIC_OUTPUT_GUARDRAILS = [check_non_empty, check_no_placeholder_leak, check_no_exception_leak]
