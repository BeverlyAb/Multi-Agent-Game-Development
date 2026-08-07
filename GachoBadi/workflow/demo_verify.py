"""Runnable proof that the workflow is generic across agents: wraps
THREE real agents from this crew -- deliberately spanning both of the
workflow's entry points:

  - GooseSolutionPlannerAgent and TaskCreatorAgent both call
    self.llm.generate() -- guarded via GuardedLLMClient (input side).
  - ChainReactionAgent calls self.llm.choice(), never generate() -- there
    is no generate() call to intercept, so it's guarded via
    guarded_output.verify_output() instead (output side).

Does not touch crew.py, main.py, or any agents/*.py file -- this is
purely additive, run on its own fixtures.

Usage (from GachoBadi/, matching executable/main.py's own convention):
    python3 workflow/demo_verify.py
"""
from __future__ import annotations

import os
import sys

# Same sys.path bootstrap as executable/main.py and executable/crew.py --
# this file lives one level below the project root too.
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
PARENT_DIR = os.path.dirname(ROOT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from api.llm_client import LLMClient
from agents.runtime.chain_reaction_agent import ChainReactionAgent
from agents.runtime.goose_solution_planner_agent import GooseSolutionPlannerAgent
from agents.runtime.task_creator_agent import TaskCreatorAgent
from definitions.models import Building, ChainReaction, Resident, Sliders, Task, VerbOutcome
from workflow.changelog import clear_changelog, read_changelog, LOG_PATH
from workflow.constraints.chain_reaction_constraints import CHAIN_REACTION_CONSTRAINTS
from workflow.constraints.goose_solution_planner_constraints import GOOSE_SOLUTION_PLANNER_CONSTRAINTS
from workflow.constraints.task_creator_constraints import TASK_CREATOR_CONSTRAINTS
from workflow.guarded_llm_client import GuardedLLMClient
from workflow.guarded_output import verify_output


def build_fixtures():
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
    return hazel, otto, bakery, hose_stand, task


def report(label: str, result) -> None:
    print(f"  accepted_all: {result.accepted_all}  retried_count: {result.retried_count}")
    for finding in result.unresolved():
        print(f"  UNRESOLVED [{label}]: [{finding.rule}] {finding.message}")


def run_goose_planner_demo(base_llm: LLMClient, bakery: Building, task: Task) -> None:
    print("\n=== Guarding Goose Solution Planner Agent (input side: GuardedLLMClient) ===")
    guarded = GuardedLLMClient(
        base_llm,
        constraints=GOOSE_SOLUTION_PLANNER_CONSTRAINTS,
        context={"legal_verbs": bakery.goose_actions, "task_description": task.description},
    )
    planner = GooseSolutionPlannerAgent(guarded)  # agent's own code: untouched
    plan = planner.run(task, [bakery])
    print(f"  plan lines: {len(plan.lines) if plan else 0}")
    report("Goose Solution Planner", guarded.result())


def run_task_creator_demo(base_llm: LLMClient, hazel: Resident, otto: Resident, bakery: Building) -> None:
    print("\n=== Guarding Task Creator Agent (input side: GuardedLLMClient) ===")
    guarded = GuardedLLMClient(
        base_llm,
        constraints=TASK_CREATOR_CONSTRAINTS,
        context={"resident_name": hazel.name, "other_name": otto.name, "building_name": bakery.name},
    )
    creator = TaskCreatorAgent(guarded)  # agent's own code: untouched
    catalog = [(hazel.name, otto.name, bakery.name)]  # one-entry catalog -> one generate() call
    tasks = creator.generate_set(catalog, offset=0, set_id=1, residents=[hazel, otto], buildings=[bakery])
    print(f"  generated task: {tasks[0].description!r}" if tasks else "  no task generated")
    report("Task Creator", guarded.result())


def flatten_chain(chain: ChainReaction) -> str:
    """The text projection constraints/chain_reaction_constraints.py's
    detectors expect: one 'actor: action' line per staged step."""
    return "\n".join(f"{s.actor}: {s.action}" for s in chain.steps)


def run_chain_reaction_demo(base_llm: LLMClient, hazel: Resident, otto: Resident, hose_stand: Building, task: Task) -> None:
    print("\n=== Guarding Chain Reaction Agent (output side: verify_output) ===")
    chain_agent = ChainReactionAgent(base_llm)  # agent's own code: untouched; no generate() to wrap anyway
    chain = chain_agent.run(task, hose_stand, [hazel, otto])
    output_text = flatten_chain(chain)
    print(f"  staged {len(chain.steps)} step(s): {output_text!r}")
    result = verify_output(
        output_text,
        constraints=CHAIN_REACTION_CONSTRAINTS,
        context={
            "building": hose_stand,
            "target_resident": task.target_resident,
            "other_resident": task.other_resident,
        },
    )
    report("Chain Reaction", result)


def main() -> int:
    print("Workflow demo -- guarding three real agents across both entry points")
    print("=" * 72)
    clear_changelog()  # fresh log for this demo run

    base_llm = LLMClient(seed=7)
    hazel, otto, bakery, hose_stand, task = build_fixtures()

    run_goose_planner_demo(base_llm, bakery, task)
    run_task_creator_demo(base_llm, hazel, otto, bakery)
    run_chain_reaction_demo(base_llm, hazel, otto, hose_stand, task)

    entries = read_changelog()
    print(f"\n=== Changelog: {len(entries)} entr(y/ies) written to {LOG_PATH} ===")
    for entry in entries:
        print(f"  [{entry['agent']}] call#{entry['call_id']} attempt {entry['attempt']} "
              f"accepted={entry['accepted']} -- {entry['justification']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
