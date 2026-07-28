"""The Crew: coordinates all eight agents through one prep pass (villager/
prop/layout design) and one mischief-tick pass (checklist -> verb plan ->
staged gag), matching the data flow in DIAGRAM.md.
"""
from __future__ import annotations

from dataclasses import asdict
from typing import List

from agents import (
    AreaOrchestrator,
    ChecklistCreatorAgent,
    GooseVerbPlannerAgent,
    ReactionDirectorAgent,
    VillagerRoutineAgent,
)
from llm_client import LLMClient
from models import Prop, Villager


class UntitledGooseGameCrew:
    """Orchestrates the Untitled-Goose-Game-style village agents for one mischief tick."""

    def __init__(self, seed: int = 7):
        self.llm = LLMClient(seed=seed)
        self.routine_agent = VillagerRoutineAgent(self.llm)
        self.checklist_creator = ChecklistCreatorAgent(self.llm)
        self.verb_planner = GooseVerbPlannerAgent(self.llm)
        self.reaction_director = ReactionDirectorAgent(self.llm)
        self.area_orchestrator = AreaOrchestrator(self.llm)

    def run_routine_pass(self, villagers: List[Villager]) -> List[Villager]:
        """Enriches raw villager requests (name/role/dials) with traits + a routine summary."""
        print("\n=== ROUTINE PASS: Villager Routine Agent ===")
        return [self.routine_agent.run(v.name, v.role, v.dials) for v in villagers]

    def run_prep_pass(self, villagers: List[Villager], props: List[Prop]) -> dict:
        """Simulates a designer asking the Area Orchestrator for new content.

        Expects `villagers` to already carry routine traits (see
        run_routine_pass). Order matters here: AreaLayoutAgent must
        assign prop.location before PropDesignerAgent/GooseVerbPlanner
        read it, and VillagerDesignerAgent needs villager.traits, which
        is why layout runs first and villager design runs last.
        """
        print("\n=== PREP PASS: Area Orchestrator ===")
        layout = self.area_orchestrator.run("layout", props)
        prop_specs = [self.area_orchestrator.run("prop", p) for p in props]
        appearances = [self.area_orchestrator.run("villager", v) for v in villagers]
        return {"layout": layout, "prop_specs": prop_specs, "appearances": appearances}

    def run_mischief_tick(self, villagers: List[Villager], props: List[Prop]) -> dict:
        """One pass of the mischief loop: checklist -> verb plan -> staged gag.

        Expects `villagers` to already carry routine traits + a designed
        appearance, and `props` to already carry an assigned location +
        design (see run_routine_pass and run_prep_pass) --
        ChecklistCreator, GooseVerbPlanner, and ReactionDirector all
        validate this and raise if a prior agent was skipped.
        """
        print("\n=== MISCHIEF TICK ===")

        checklist = self.checklist_creator.run(villagers, props)
        if not checklist:
            return {"villagers": villagers, "checklist": [], "verb_plan": None, "staged_gags": []}

        active_item = checklist[0]
        verb_plan = self.verb_planner.run(active_item, villagers, props)
        staged_gags = self.reaction_director.run(verb_plan, active_item, props)

        return {
            "villagers": villagers,
            "checklist": checklist,
            "verb_plan": verb_plan,
            "staged_gags": staged_gags,
        }

    @staticmethod
    def to_jsonable(result: dict) -> dict:
        def conv(value):
            if hasattr(value, "__dataclass_fields__"):
                return asdict(value)
            if isinstance(value, list):
                return [conv(v) for v in value]
            return value

        return {k: conv(v) for k, v in result.items()}
