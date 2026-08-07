"""Maps each already-guarded agent's key to what agent.py needs to run it
repeatedly under progressively retuned constraints: the demo runner
(workflow/generic/demo_verify.py, which every entry here now accepts an
optional `constraints` override for), the ORIGINAL AgentConstraints
singleton (its agent_name and gap_detectors never change between cycles
-- only the values loaded from constraints.yaml do), and that agent's own
constraints.yaml path (so a cycle's tuned values can be written back).

Reuses demo_verify.py's fixtures/runners rather than re-deriving them --
same reasoning demo_verify.py itself gives for reusing real agents/*.py
code instead of re-implementing it: one source of truth for "how to run
this agent," not two that can drift apart.
"""
from __future__ import annotations

import os
from typing import Dict

from ..constraints.chain_reaction.constraints import CHAIN_REACTION_CONSTRAINTS
from ..constraints.goose_solution_planner.constraints import GOOSE_SOLUTION_PLANNER_CONSTRAINTS
from ..constraints.task_creator.constraints import TASK_CREATOR_CONSTRAINTS
from ..generic.demo_verify import run_chain_reaction_demo, run_goose_planner_demo, run_task_creator_demo

_CONSTRAINTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "constraints")


def _yaml_path(agent_key: str) -> str:
    return os.path.join(_CONSTRAINTS_DIR, agent_key, "constraints.yaml")


AGENT_REGISTRY: Dict[str, dict] = {
    "goose_solution_planner": {
        "runner": run_goose_planner_demo,
        "original": GOOSE_SOLUTION_PLANNER_CONSTRAINTS,
        "yaml_path": _yaml_path("goose_solution_planner"),
    },
    "task_creator": {
        "runner": run_task_creator_demo,
        "original": TASK_CREATOR_CONSTRAINTS,
        "yaml_path": _yaml_path("task_creator"),
    },
    "chain_reaction": {
        "runner": run_chain_reaction_demo,
        "original": CHAIN_REACTION_CONSTRAINTS,
        "yaml_path": _yaml_path("chain_reaction"),
    },
}
