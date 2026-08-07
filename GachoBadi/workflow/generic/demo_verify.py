"""Runnable proof that the workflow is generic across agents: wraps real
agents from this crew, spanning both of the workflow's entry points --

  - GooseSolutionPlannerAgent and TaskCreatorAgent both call
    self.llm.generate() -- guarded via GuardedLLMClient (input side).
  - ChainReactionAgent calls self.llm.choice(), never generate() -- there
    is no generate() call to intercept, so it's guarded via
    guarded_output.verify_output() instead (output side).

-- and lets you choose WHICH of them to actually run, via --agents. Does
not touch crew.py, main.py, or any agents/*.py file -- this is purely
additive, run on its own fixtures.

Usage (from GachoBadi/, matching executable/main.py's own convention):
    python3 workflow/generic/demo_verify.py                                  # all registered agents (default)
    python3 workflow/generic/demo_verify.py --agents none                    # zero agents -- just checks the harness loads
    python3 workflow/generic/demo_verify.py --agents goose_solution_planner   # exactly one
    python3 workflow/generic/demo_verify.py --agents task_creator,chain_reaction  # a chosen set
    python3 workflow/generic/demo_verify.py --list                           # print available agent keys and exit
"""
from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

# Same reasoning as executable/main.py's own bootstrap -- but this file
# lives TWO levels below the project root (workflow/generic/), not one,
# so api/, definitions/, agents/, and workflow/ itself need the actual
# root added to sys.path, not workflow/ (which dirname(__file__) twice
# would incorrectly land on).
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from api.llm_client import LLMClient
from agents.runtime.chain_reaction_agent import ChainReactionAgent
from agents.runtime.goose_solution_planner_agent import GooseSolutionPlannerAgent
from agents.runtime.task_creator_agent import TaskCreatorAgent
from definitions.models import Building, ChainReaction, Resident, Sliders, Task, VerbOutcome
from workflow.generic.changelog import clear_changelog, read_changelog, LOG_PATH
from workflow.constraints.chain_reaction_constraints import CHAIN_REACTION_CONSTRAINTS
from workflow.constraints.goose_solution_planner_constraints import GOOSE_SOLUTION_PLANNER_CONSTRAINTS
from workflow.constraints.task_creator_constraints import TASK_CREATOR_CONSTRAINTS
from workflow.generic.guarded_llm_client import GuardedLLMClient
from workflow.generic.guarded_output import verify_output
from workflow.definitions.models_verification import ReviewResult


@dataclass
class DemoContext:
    """Everything a demo function might need, built once in main() and
    handed to whichever demo functions --agents actually selects -- so
    picking a subset never has to re-derive fixtures a skipped agent
    would have needed anyway."""

    base_llm: LLMClient
    hazel: Resident
    otto: Resident
    bakery: Building
    hose_stand: Building
    task: Task


def build_context() -> DemoContext:
    """Minimal, directly-constructed fixtures -- deliberately bypasses
    the real crew's personality/relationship/dev-time/item-interaction
    passes, since this demo is about the verification workflow, not
    re-deriving the crew."""
    hazel = Resident(
        name="Hazel",
        role="baker",
        sliders=Sliders(movement=30, speech=70, energy=60, intelligence=55),
        traits=["candid", "excitable"],
        appearance="Hazel: a baker with flour-dusted sleeves and a quick smile.",
    )
    otto = Resident(
        name="Otto",
        role="teacher",
        sliders=Sliders(movement=20, speech=40, energy=35, intelligence=90),
        traits=["reserved", "astute"],
        appearance="Otto: a teacher who always seems to be mid-thought.",
    )
    hazel.relationships["Otto"] = "drifted apart"
    otto.relationships["Hazel"] = "drifted apart"
    hazel.relationship_backstories["Otto"] = "drifted apart after a missed birthday"
    otto.relationship_backstories["Hazel"] = "drifted apart after a missed birthday"

    bakery = Building(
        name="Hazel's Bakery",
        kind="shop",
        interactive_feature="oven that can overheat and puff flour",
        location="town square",
        designed=True,
        goose_actions=["Grab", "Drop"],
    )

    # A second building, matching the real Item Interaction Agent's own
    # "prop" registration (see agents/runtime/item_interaction_agent.py's
    # BUILDING_POSSIBLE_OUTCOMES), hand-populated here rather than run
    # through that agent -- gives ChainReactionAgent a building whose
    # first outcome actually has a chain_effect, so the demo can show a
    # real 2-step chain, not just a 1-step dead end.
    hose_stand = Building(
        name="Garden Hose Stand",
        kind="prop",
        interactive_feature="hose that can spout water",
        location="east meadow",
        designed=True,
        goose_actions=["Grab", "Dash"],
        possible_outcomes=[
            VerbOutcome(
                "picks it up and puts it to careful, deliberate use",
                "the calm result draws a second resident over to see what's going on",
            ),
            VerbOutcome("just resets it where it belongs with a shrug", ""),
        ],
    )

    task = Task(
        task_id=1,
        set_id=1,
        description="Get Hazel to reconnect with Otto, who she's drifted apart from, near Hazel's Bakery.",
        target_resident="Hazel",
        other_resident="Otto",
        involves_building="Hazel's Bakery",
        goal_state="Hazel and Otto are both present at Hazel's Bakery with a positive reaction flag set",
    )
    return DemoContext(
        base_llm=LLMClient(seed=7), hazel=hazel, otto=otto, bakery=bakery, hose_stand=hose_stand, task=task
    )


def run_goose_planner_demo(ctx: DemoContext) -> ReviewResult:
    guarded = GuardedLLMClient(
        ctx.base_llm,
        constraints=GOOSE_SOLUTION_PLANNER_CONSTRAINTS,
        context={"legal_verbs": ctx.bakery.goose_actions, "task_description": ctx.task.description},
    )
    planner = GooseSolutionPlannerAgent(guarded)  # agent's own code: untouched
    plan = planner.run(ctx.task, [ctx.bakery])
    print(f"  plan lines: {len(plan.lines) if plan else 0}")
    return guarded.result()


def run_task_creator_demo(ctx: DemoContext) -> ReviewResult:
    guarded = GuardedLLMClient(
        ctx.base_llm,
        constraints=TASK_CREATOR_CONSTRAINTS,
        context={"resident_name": ctx.hazel.name, "other_name": ctx.otto.name, "building_name": ctx.bakery.name},
    )
    creator = TaskCreatorAgent(guarded)  # agent's own code: untouched
    catalog = [(ctx.hazel.name, ctx.otto.name, ctx.bakery.name)]  # one entry -> one generate() call
    tasks = creator.generate_set(catalog, offset=0, set_id=1, residents=[ctx.hazel, ctx.otto], buildings=[ctx.bakery])
    print(f"  generated task: {tasks[0].description!r}" if tasks else "  no task generated")
    return guarded.result()


def flatten_chain(chain: ChainReaction) -> str:
    """The text projection constraints/chain_reaction_constraints.py's
    detectors expect: one 'actor: action' line per staged step."""
    return "\n".join(f"{s.actor}: {s.action}" for s in chain.steps)


def run_chain_reaction_demo(ctx: DemoContext) -> ReviewResult:
    chain_agent = ChainReactionAgent(ctx.base_llm)  # agent's own code: untouched; no generate() to wrap anyway
    chain = chain_agent.run(ctx.task, ctx.hose_stand, [ctx.hazel, ctx.otto])
    output_text = flatten_chain(chain)
    print(f"  staged {len(chain.steps)} step(s): {output_text!r}")
    return verify_output(
        output_text,
        constraints=CHAIN_REACTION_CONSTRAINTS,
        context={
            "building": ctx.hose_stand,
            "target_resident": ctx.task.target_resident,
            "other_resident": ctx.task.other_resident,
        },
    )


# The registry --agents selects from. Add a new agent's demo here (and to
# workflow/constraints/, per README.md's "Adding a new agent") and it's
# immediately selectable by name -- nothing else in this file changes.
AGENT_DEMOS: Dict[str, Callable[[DemoContext], ReviewResult]] = {
    "goose_solution_planner": run_goose_planner_demo,
    "task_creator": run_task_creator_demo,
    "chain_reaction": run_chain_reaction_demo,
}


def resolve_agent_keys(spec: str) -> List[str]:
    """Turns --agents' raw string into an ordered list of registry keys.
    Accepts 'all' (every registered agent), 'none'/'' (zero agents -- a
    deliberately valid, distinct choice, not an error), or a
    comma-separated subset. Preserves AGENT_DEMOS' own declaration order
    rather than the order the user typed keys in, so output order is
    always predictable regardless of --agents phrasing."""
    normalized = spec.strip().lower()
    if normalized in ("", "none"):
        return []
    if normalized == "all":
        return list(AGENT_DEMOS.keys())
    requested = {k.strip() for k in normalized.split(",") if k.strip()}
    unknown = requested - AGENT_DEMOS.keys()
    if unknown:
        raise SystemExit(
            f"Unknown agent key(s): {sorted(unknown)}. Available: {', '.join(AGENT_DEMOS)} (or 'all'/'none')."
        )
    return [k for k in AGENT_DEMOS if k in requested]


def report(label: str, result: ReviewResult) -> None:
    print(f"  accepted_all: {result.accepted_all}  retried_count: {result.retried_count}")
    for finding in result.unresolved():
        print(f"  UNRESOLVED [{label}]: [{finding.rule}] {finding.message}")


def parse_args(argv: Optional[List[str]]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--agents",
        default="all",
        metavar="SPEC",
        help=(
            "Which agents to verify: 'all' (default), 'none' for zero, or a "
            f"comma-separated subset of: {', '.join(AGENT_DEMOS)}"
        ),
    )
    parser.add_argument("--list", action="store_true", help="Print available agent keys and exit.")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    if args.list:
        for key in AGENT_DEMOS:
            print(key)
        return 0

    keys = resolve_agent_keys(args.agents)

    print(f"Workflow demo -- guarding {len(keys)} agent(s): {keys if keys else '(none)'}")
    print("=" * 72)

    if not keys:
        print("\nNo agents selected -- nothing to verify. Pass --agents <name[,name...]|all|none>.")
        return 0

    clear_changelog()  # fresh log for this run
    ctx = build_context()

    for key in keys:
        print(f"\n=== Guarding {key} ===")
        result = AGENT_DEMOS[key](ctx)
        report(key, result)

    entries = read_changelog()
    print(f"\n=== Changelog: {len(entries)} entr(y/ies) written to {LOG_PATH} ===")
    for entry in entries:
        print(f"  [{entry['agent']}] call#{entry['call_id']} attempt {entry['attempt']} "
              f"accepted={entry['accepted']} -- {entry['justification']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
