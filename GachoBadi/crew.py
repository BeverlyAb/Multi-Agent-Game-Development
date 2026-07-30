"""The Crew: coordinates all eleven agents through a personality pass, a
relationship pass, a dev-time pass, and one runtime game-loop tick (tasks
-> screenplay + verb plan -> staging -> news bulletin), matching the data
flow in DIAGRAM.md.
"""
from __future__ import annotations

from dataclasses import asdict
from typing import List

from agents import (
    CharacterPersonalityAgent,
    DirectorAgent,
    GooseSolutionPlannerAgent,
    NewscasterAgent,
    RelationshipAgent,
    SceneOrchestratorAgent,
    TaskCreatorAgent,
    WriterAgent,
)
from llm_client import LLMClient
from models import Building, Resident


class GachoBadiCrew:
    """Orchestrates the Gacho Badi AI agents for one island 'tick'."""

    def __init__(self, seed: int = 7):
        self.llm = LLMClient(seed=seed)
        self.personality_agent = CharacterPersonalityAgent(self.llm)
        self.relationship_agent = RelationshipAgent(self.llm)
        self.task_creator = TaskCreatorAgent(self.llm)
        self.writer = WriterAgent(self.llm)
        self.goose_planner = GooseSolutionPlannerAgent(self.llm)
        self.director = DirectorAgent(self.llm)
        self.newscaster = NewscasterAgent(self.llm)
        self.scene_orchestrator = SceneOrchestratorAgent(self.llm)

    def run_personality_pass(self, residents: List[Resident]) -> List[Resident]:
        """Enriches raw resident requests (name/role/sliders) with traits + a summary."""
        print("\n=== PERSONALITY PASS: Character Personality Agent ===")
        return [self.personality_agent.run(r.name, r.role, r.sliders) for r in residents]

    def run_relationship_pass(self, residents: List[Resident]) -> List[Resident]:
        """Maps how every pair of residents feels about each other. Requires .traits."""
        print("\n=== RELATIONSHIP PASS: Relationship Agent ===")
        return self.relationship_agent.run(residents)

    def run_dev_time_pass(self, residents: List[Resident], buildings: List[Building]) -> dict:
        """Simulates a programmer asking the Scene Orchestrator for new content.

        Expects `residents` to already carry personality traits (see
        run_personality_pass). Order matters here: IslandLayoutAgent must
        assign building.location before BuildingDesignerAgent/Writer read
        it, and CharacterAppearanceAgent needs resident.traits, which is
        why layout runs first and appearance runs last.
        """
        print("\n=== DEV-TIME PASS: Scene Orchestrator ===")
        layout = self.scene_orchestrator.run("layout", buildings)
        building_specs = [self.scene_orchestrator.run("building", b) for b in buildings]
        appearances = [self.scene_orchestrator.run("appearance", r) for r in residents]
        return {"layout": layout, "building_specs": building_specs, "appearances": appearances}

    def run_game_tick(self, residents: List[Resident], buildings: List[Building]) -> dict:
        """One pass of the runtime loop: tasks -> screenplay + verb plan -> staging -> news.

        Expects `residents` to already carry personality traits +
        relationships + an appearance spec, and `buildings` to already
        carry an assigned location + design (see run_personality_pass,
        run_relationship_pass, and run_dev_time_pass) -- TaskCreatorAgent,
        WriterAgent, GooseSolutionPlannerAgent, DirectorAgent, and
        NewscasterAgent all validate this and raise if a prior agent was
        skipped.
        """
        print("\n=== RUNTIME GAME LOOP TICK ===")

        tasks = self.task_creator.run(residents, buildings)
        if not tasks:
            return {
                "personalities": residents,
                "tasks": [],
                "screenplay": None,
                "verb_plan": None,
                "staged_actions": [],
                "news": None,
            }

        active_task = tasks[0]
        screenplay = self.writer.run(active_task, residents, buildings)
        verb_plan = self.goose_planner.run(active_task, buildings)
        staged_actions = self.director.run(screenplay, verb_plan, active_task, buildings)
        news = self.newscaster.run(staged_actions, active_task)

        return {
            "personalities": residents,
            "tasks": tasks,
            "screenplay": screenplay,
            "verb_plan": verb_plan,
            "staged_actions": staged_actions,
            "news": news,
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
