"""The user-specified target agent.py's loop tries to reach: 'I want
agent X's output to satisfy Y' as data, not prose.

Deliberately NO free-form natural-language goal parsing here -- the same
"don't invent a second, weaker programming language" reasoning
workflow/README.md gives for the YAML/Python constraint split applies:
max_unresolved/forbidden_rules already say precisely what "good enough"
means, in terms this workflow's own ReviewResult.unresolved() already
produces (a list of Findings, each with a `rule` name). `description` is
kept purely as a free-text label for logging/display -- it is never
parsed or matched against anything.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class Goal:
    agent_key: str  # one of registry.AGENT_REGISTRY's keys
    description: str = ""  # free text, logging only -- never parsed
    # Unresolved BLOCKING findings tolerated once max_cycles is reached
    # without the goal being met earlier. 0 (default) means "fully clean."
    max_unresolved: int = 0
    # Rule names that must NEVER appear unresolved, regardless of
    # max_unresolved -- e.g. ["no_unregistered_verb"] to say "I don't
    # care about anything else, but this one is non-negotiable."
    forbidden_rules: List[str] = field(default_factory=list)
    # How many run/verify/adjust cycles to attempt before giving up.
    max_cycles: int = 5

    def is_met(self, unresolved) -> bool:
        if any(f.rule in self.forbidden_rules for f in unresolved):
            return False
        return len(unresolved) <= self.max_unresolved


@dataclass
class CycleLog:
    cycle: int
    unresolved_rules: List[str]
    adjustment: str  # human-readable description of what changed this cycle, "" if nothing did
    goal_met: bool


@dataclass
class GoalResult:
    goal: Goal
    achieved: bool
    cycles: List[CycleLog] = field(default_factory=list)
    # "goal_met" | "max_cycles" | "stagnant" | "no_further_adjustment_possible"
    stopped_reason: str = ""
