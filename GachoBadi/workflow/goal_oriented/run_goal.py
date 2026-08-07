"""The interface the goal-oriented agent was asked for: point this at one
of registry.AGENT_REGISTRY's keys, describe the outcome you want as a
small set of flags (see goal.py's docstring for why not free text), and
it drives GoalOrientedAgent.run() end to end, printing each cycle.

Usage (from GachoBadi/, matching the rest of workflow/'s own CLIs):
    python3 workflow/goal_oriented/run_goal.py --list
    python3 workflow/goal_oriented/run_goal.py --agent chain_reaction
    python3 workflow/goal_oriented/run_goal.py --agent task_creator --max-cycles 3
    python3 workflow/goal_oriented/run_goal.py --agent goose_solution_planner \
        --forbidden-rules no_unregistered_verb --description "never invent a goose verb"

Every run starts from a fresh workflow/logs/goal_log.jsonl. If any cycle
tunes a constraints.yaml, the hand-authored original is preserved
alongside it as constraints.yaml.orig (written once, on first touch --
never overwritten by a later cycle).
"""
from __future__ import annotations

import argparse
import os
import sys
from typing import List, Optional

# Same reasoning as generic/demo_verify.py's own bootstrap -- this file
# lives TWO levels below the project root (workflow/goal_oriented/), so
# the actual root needs adding to sys.path, not workflow/ itself.
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from workflow.goal_oriented.agent import GoalOrientedAgent
from workflow.goal_oriented.goal import Goal
from workflow.goal_oriented.goal_log import clear_goal_log
from workflow.goal_oriented.registry import AGENT_REGISTRY


def parse_args(argv: Optional[List[str]]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--agent", choices=sorted(AGENT_REGISTRY), help="Which agent to drive toward the goal.")
    parser.add_argument("--description", default="", help="Free-text note for the log -- not parsed.")
    parser.add_argument(
        "--max-unresolved",
        type=int,
        default=0,
        help="Unresolved BLOCKING findings tolerated once max-cycles is reached (default 0 -- fully clean).",
    )
    parser.add_argument(
        "--forbidden-rules",
        default="",
        help="Comma-separated rule names that must never be unresolved, regardless of --max-unresolved.",
    )
    parser.add_argument("--max-cycles", type=int, default=5, help="How many run/verify/adjust cycles to attempt (default 5).")
    parser.add_argument("--list", action="store_true", help="Print available agent keys and exit.")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    if args.list:
        for key in AGENT_REGISTRY:
            print(key)
        return 0

    if not args.agent:
        print("Pass --agent <name> (or --list to see available names).")
        return 1

    goal = Goal(
        agent_key=args.agent,
        description=args.description,
        max_unresolved=args.max_unresolved,
        forbidden_rules=[r.strip() for r in args.forbidden_rules.split(",") if r.strip()],
        max_cycles=args.max_cycles,
    )

    clear_goal_log()
    print(f"Goal-oriented agent -- driving '{goal.agent_key}' toward: {goal.description or '(fully clean, default)'}")
    print(f"  max_unresolved={goal.max_unresolved}  forbidden_rules={goal.forbidden_rules}  max_cycles={goal.max_cycles}")
    print("=" * 72)

    result = GoalOrientedAgent().run(goal)

    for c in result.cycles:
        status = "GOAL MET" if c.goal_met else "not yet"
        print(f"\n[cycle {c.cycle}] unresolved: {c.unresolved_rules or '(none)'} -- {status}")
        if c.adjustment:
            print(f"  adjusted: {c.adjustment}")

    print("\n" + "=" * 72)
    print(f"achieved={result.achieved}  stopped_reason={result.stopped_reason!r}  cycles_run={len(result.cycles)}")
    if not result.achieved and result.stopped_reason == "stagnant":
        print(
            "  Constraint tuning stalled: the same findings survived an adjustment unchanged -- likely a "
            "deterministic agent/mock-provider ceiling this loop cannot retune past. See "
            "workflow/logs/goal_log.jsonl for the full cycle history."
        )
    return 0 if result.achieved else 1


if __name__ == "__main__":
    raise SystemExit(main())
