"""The 'goal oriented' meta-agent: an OUTER loop around the existing
generic/guarded_llm_client.py + generic/guarded_output.py inner loop.
You specify a Goal (goal.py) -- an outcome for one of registry.py's
three registered agents -- and GoalOrientedAgent.run() repeatedly:

  1. Loads that agent's constraints.yaml fresh off disk.
  2. Runs the agent (via registry.py's runner) against the SAME fixed
     demo fixture every cycle (workflow/generic/demo_verify.py's
     build_context(), built once and reused) -- so only the CONSTRAINTS
     vary between cycles, never the input, isolating what a constraint
     change actually did.
  3. Checks whether the goal is met.
  4. If not, tunes that agent's own constraints.yaml (priority_weights /
     max_retries) and writes it back to disk, then tries again.

This does NOT re-implement run/verify/retry -- that machinery already
exists (per-call retry-with-feedback in guarded_llm_client.py, one-shot
check in guarded_output.py). This is the interface layer on top of it:
point it at an agent + a goal, and it drives that existing loop across
CYCLES (full re-runs), escalating constraint weight until the goal is
met, capped out, or found to be unreachable by constraint-tuning alone.

Constraint-tuning has a real ceiling, and this loop is built to notice
it rather than burn cycles pretending otherwise: this project's mock LLM
provider (api/llm_client.py) returns its `fallback` string VERBATIM
regardless of the prompt, so retry feedback -- and by extension, this
agent's priority_weight/max_retries adjustments -- can only ever change
which attempt a REAL LLM call favors, never a mock-provider agent's
actual output. See _run_cycle's stagnation check below: if the exact
same unresolved rule set survives an adjusted cycle unchanged, that is
this agent correctly detecting that ceiling and stopping -- see
workflow/README.md's "Running the demo" section for the concrete,
already-known case this surfaces (goose_solution_planner's 'carries'
fallback verb, which no amount of retuning can fix without a real LLM
provider or a code change to that agent's own fallback text).
"""
from __future__ import annotations

import copy
import os
from typing import Dict, List, Optional, Tuple

from .goal import CycleLog, Goal, GoalResult
from .goal_log import append_goal_log
from .registry import AGENT_REGISTRY
from ..constraints.base import AgentConstraints
from ..constraints.config_loader import load_constraint_config, save_constraint_config
from ..generic.demo_verify import build_context
from ..generic.guardrails import TokenBudget

# Bounds on how far this agent will tune a constraint before concluding
# "no further adjustment possible" -- matches this crew's own "never loop
# forever" philosophy (AgentConstraints.max_retries' own docstring) at
# the cycle level instead of the per-call level.
_PRIORITY_BUMP = 200
_PRIORITY_CAP = 2000
_MAX_RETRIES_CAP = 5


def _backup_once(yaml_path: str) -> None:
    """Preserves the hand-authored original the FIRST time this agent
    ever touches a given constraints.yaml -- every later cycle overwrites
    the working file, but the .orig always holds what a human wrote."""
    backup_path = yaml_path + ".orig"
    if not os.path.exists(backup_path):
        with open(yaml_path) as src, open(backup_path, "w") as dst:
            dst.write(src.read())


def _tally_rules(findings) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for f in findings:
        counts[f.rule] = counts.get(f.rule, 0) + 1
    return counts


def _pick_target_rule(unresolved, forbidden_rules: List[str]) -> Optional[str]:
    """Forbidden rules take priority over mere frequency -- the user
    named them non-negotiable. Within either pool, the most frequently
    unresolved rule is tuned first, on the theory that it's either the
    easiest single win or the one blocking the most other progress."""
    counts = _tally_rules(unresolved)
    if not counts:
        return None
    forbidden_hits = {r: c for r, c in counts.items() if r in forbidden_rules}
    pool = forbidden_hits or counts
    return max(pool, key=pool.get)


def _propose_adjustment(cfg: dict, unresolved, forbidden_rules: List[str]) -> Tuple[Optional[dict], str]:
    """Returns (new_cfg, description), or (None, reason) if the most
    promising rule to target is already at every knob's cap -- the
    signal to the caller that this loop has nothing left to try."""
    target_rule = _pick_target_rule(unresolved, forbidden_rules)
    if target_rule is None:
        return None, "no unresolved findings to target"

    new_cfg = copy.deepcopy(cfg)
    changes = []

    weights = new_cfg.setdefault("priority_weights", {})
    current_weight = weights.get(target_rule, 0)
    if current_weight < _PRIORITY_CAP:
        new_weight = min(_PRIORITY_CAP, max(current_weight, 100) + _PRIORITY_BUMP)
        weights[target_rule] = new_weight
        changes.append(f"priority_weights['{target_rule}']: {current_weight} -> {new_weight}")

    current_retries = new_cfg.get("max_retries", 2)
    if current_retries < _MAX_RETRIES_CAP:
        new_cfg["max_retries"] = current_retries + 1
        changes.append(f"max_retries: {current_retries} -> {current_retries + 1}")

    if not changes:
        return None, f"'{target_rule}' is already at its priority_weight and max_retries caps -- no further tuning possible"
    return new_cfg, "; ".join(changes)


def _build_constraints(agent_key: str, cfg: dict) -> AgentConstraints:
    """Rebuilds a fresh AgentConstraints straight from a freshly-loaded
    config dict rather than mutating/reloading the module-level singleton
    -- gap_detectors and agent_name are pulled from that singleton (they
    never change), everything else comes off disk fresh every cycle."""
    original = AGENT_REGISTRY[agent_key]["original"]
    return AgentConstraints(
        agent_name=original.agent_name,
        token_budget=TokenBudget(**cfg["token_budget"]),
        gap_detectors=original.gap_detectors,
        priority_weights=cfg.get("priority_weights", {}),
        max_retries=cfg.get("max_retries", original.max_retries),
    )


class GoalOrientedAgent:
    """The interface the user prompts: construct one, call run(goal).
    Everything about HOW an agent is run/verified is already registered
    per-key in registry.py; this class only owns the outer cycle."""

    def __init__(self) -> None:
        self._ctx = None  # built lazily, once, shared across every cycle/goal this instance runs

    def _context(self):
        if self._ctx is None:
            self._ctx = build_context()
        return self._ctx

    def run(self, goal: Goal) -> GoalResult:
        if goal.agent_key not in AGENT_REGISTRY:
            raise ValueError(f"Unknown agent key {goal.agent_key!r}. Available: {', '.join(AGENT_REGISTRY)}")

        entry = AGENT_REGISTRY[goal.agent_key]
        yaml_path = entry["yaml_path"]
        runner = entry["runner"]
        ctx = self._context()

        result = GoalResult(goal=goal, achieved=False)
        previous_rule_set: Optional[Tuple[str, ...]] = None

        for cycle in range(1, goal.max_cycles + 1):
            cfg = load_constraint_config(yaml_path)
            constraints = _build_constraints(goal.agent_key, cfg)
            review = runner(ctx, constraints)
            unresolved = review.unresolved()
            unresolved_rules = sorted({f.rule for f in unresolved})
            goal_met = goal.is_met(unresolved)

            if goal_met:
                result.cycles.append(
                    CycleLog(cycle=cycle, unresolved_rules=unresolved_rules, adjustment="", goal_met=True)
                )
                append_goal_log(
                    {
                        "agent": goal.agent_key,
                        "cycle": cycle,
                        "unresolved_rules": unresolved_rules,
                        "adjustment": "",
                        "goal_met": True,
                        "note": "goal met -- stopping",
                    }
                )
                result.achieved = True
                result.stopped_reason = "goal_met"
                return result

            rule_set = tuple(unresolved_rules)
            if rule_set == previous_rule_set:
                result.cycles.append(
                    CycleLog(cycle=cycle, unresolved_rules=unresolved_rules, adjustment="", goal_met=False)
                )
                append_goal_log(
                    {
                        "agent": goal.agent_key,
                        "cycle": cycle,
                        "unresolved_rules": unresolved_rules,
                        "adjustment": "",
                        "goal_met": False,
                        "note": (
                            "unresolved findings identical to the previous adjusted cycle -- constraint "
                            "tuning is having no effect, most likely because this agent's underlying output "
                            "is deterministic (e.g. the mock LLM provider ignores retry feedback entirely). "
                            "Stopping rather than burning remaining cycles; fixing this needs a change to "
                            "the agent's own code/fallback text, or a real LLM provider configured -- not a "
                            "constraint adjustment."
                        ),
                    }
                )
                result.stopped_reason = "stagnant"
                return result
            previous_rule_set = rule_set

            new_cfg, description = _propose_adjustment(cfg, unresolved, goal.forbidden_rules)
            result.cycles.append(
                CycleLog(cycle=cycle, unresolved_rules=unresolved_rules, adjustment=description, goal_met=False)
            )

            if new_cfg is None:
                append_goal_log(
                    {
                        "agent": goal.agent_key,
                        "cycle": cycle,
                        "unresolved_rules": unresolved_rules,
                        "adjustment": "",
                        "goal_met": False,
                        "note": description,
                    }
                )
                result.stopped_reason = "no_further_adjustment_possible"
                return result

            _backup_once(yaml_path)
            save_constraint_config(
                yaml_path,
                new_cfg,
                header=(
                    f"Auto-tuned by workflow/goal_oriented on cycle {cycle} toward goal "
                    f"{goal.description or goal.agent_key!r}. Hand-authored original saved "
                    f"alongside as constraints.yaml.orig."
                ),
            )
            append_goal_log(
                {
                    "agent": goal.agent_key,
                    "cycle": cycle,
                    "unresolved_rules": unresolved_rules,
                    "adjustment": description,
                    "goal_met": False,
                    "note": f"wrote {yaml_path}",
                }
            )

        result.stopped_reason = "max_cycles"
        return result
