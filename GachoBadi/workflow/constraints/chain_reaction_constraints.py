"""Gap-detection LOGIC for agents/runtime/chain_reaction_agent.py --
pairs with chain_reaction_constraints.yaml.

Unlike every other constraint file in this package, this agent makes NO
self.llm.generate() call at all -- its only randomness is
self.llm.choice(building.possible_outcomes) (see that agent's own
docstring: "the one random draw in the whole crew that isn't just flavor
text"). guarded_llm_client.GuardedLLMClient can't guard this agent: there
is no generate() call to intercept. Use guarded_output.verify_output()
instead, against a flattened text projection of the ChainReaction it
returns. The expected flattening (one line per step, "{actor}: {action}")
is exactly what these detectors parse -- see generic/demo_verify.py's
flatten_chain() for the reference implementation.

context dict this file's detectors expect:
  {
    "building": Building,              # the task's building, for its possible_outcomes
    "target_resident": str,            # task.target_resident
    "other_resident": Optional[str],   # task.other_resident
  }
"""
from __future__ import annotations

import os
from typing import Dict, List

from ..generic.guardrails import TokenBudget
from ..definitions.models_verification import Finding, Severity
from .base import AgentConstraints
from .config_loader import load_constraint_config

_CONFIG = load_constraint_config(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "chain_reaction_constraints.yaml")
)
TOKEN_BUDGET = TokenBudget(**_CONFIG["token_budget"])


def outcome_is_registered(output: str, context: Dict) -> List[Finding]:
    """The core guarantee this agent's own docstring claims. Checks that
    the staged resident_action text actually matches one of
    building.possible_outcomes verbatim -- if this ever fires, something
    downstream (or a future edit to this agent) picked or fabricated an
    outcome the Item Interaction Agent never certified, the same failure
    mode the Goose Solution Planner's no_unregistered_verb check exists
    to prevent on the goose's own side."""
    building = context.get("building")
    outcomes = getattr(building, "possible_outcomes", None) if building is not None else None
    if not outcomes:
        return []
    registered = {o.resident_action for o in outcomes}
    if not any(action in output for action in registered):
        return [
            Finding(
                rule="outcome_is_registered",
                message=f"staged output matches none of the registered possible_outcomes {sorted(registered)}",
                severity=Severity.BLOCKING,
            )
        ]
    return []


def chain_effect_requires_other_resident(output: str, context: Dict) -> List[Finding]:
    """This agent's own docstring: a second step only ever appears 'only
    when both a chain_effect and a second resident are present.' If the
    flattened output shows two staged actor lines but the task has no
    other_resident, that invariant broke."""
    other = context.get("other_resident")
    lines = [l for l in output.split("\n") if l.strip()]
    if len(lines) > 1 and not other:
        return [
            Finding(
                rule="chain_effect_requires_other_resident",
                message="a second chain step is staged but this task has no other_resident to draw in",
                severity=Severity.BLOCKING,
            )
        ]
    return []


def max_two_steps(output: str, context: Dict) -> List[Finding]:
    """This agent's own docstring caps a chain at 'at most two staged
    steps' -- a third step would mean the chain compounded beyond what
    DirectorAgent/WriterAgent were ever built to stage or narrate."""
    lines = [l for l in output.split("\n") if l.strip()]
    if len(lines) > 2:
        return [
            Finding(
                rule="max_two_steps",
                message=f"chain has {len(lines)} steps, more than the documented maximum of 2",
                severity=Severity.BLOCKING,
            )
        ]
    return []


def step_actor_is_task_participant(output: str, context: Dict) -> List[Finding]:
    """Every actor a chain step names should be someone this task is
    actually about -- the target resident or the other resident -- never
    a third, unrelated name this agent has no basis to invent."""
    target = context.get("target_resident")
    other = context.get("other_resident")
    valid = {n for n in (target, other) if n}
    if not valid:
        return []
    findings = []
    for line in output.split("\n"):
        line = line.strip()
        if not line:
            continue
        actor = line.split(":", 1)[0].strip()
        if actor and actor not in valid:
            findings.append(
                Finding(
                    rule="step_actor_is_task_participant",
                    message=f"chain step actor '{actor}' is neither this task's target_resident nor other_resident",
                    severity=Severity.BLOCKING,
                )
            )
    return findings


CHAIN_REACTION_CONSTRAINTS = AgentConstraints(
    agent_name="Chain Reaction Agent",
    token_budget=TOKEN_BUDGET,
    gap_detectors=[
        outcome_is_registered,
        chain_effect_requires_other_resident,
        max_two_steps,
        step_actor_is_task_participant,
    ],
    priority_weights=_CONFIG.get("priority_weights", {}),
    max_retries=_CONFIG.get("max_retries", 0),
)
