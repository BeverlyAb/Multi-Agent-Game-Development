"""The Crew: coordinates all eight agents through one prep pass (room/area/
ACT-menu design) and one battle-turn pass, matching the data flow in
DIAGRAM.md.
"""
from __future__ import annotations

from dataclasses import asdict
from typing import List

from agents import (
    AreaLayoutAgent,
    BattleDirectorAgent,
    BulletPatternDesignerAgent,
    DialogueWriterAgent,
    EncounterOrchestrator,
    MonsterPersonalityAgent,
)
from llm_client import LLMClient
from models import Monster, Room


class UndertaleCrew:
    """Orchestrates the Undertale encounter-generation agents for one battle turn."""

    def __init__(self, seed: int = 7):
        self.llm = LLMClient(seed=seed)
        self.personality_agent = MonsterPersonalityAgent(self.llm)
        self.bullet_pattern_agent = BulletPatternDesignerAgent(self.llm)
        self.dialogue_writer = DialogueWriterAgent(self.llm)
        self.battle_director = BattleDirectorAgent(self.llm)
        self.encounter_orchestrator = EncounterOrchestrator(self.llm)
        self.route = "Neutral"  # Pacifist | Neutral | Genocide -- flavors dialogue, not a hard dependency

    def record_outcome(self, spared: bool) -> None:
        """Nudge the current route the way Undertale tracks karma across encounters."""
        self.route = "Pacifist" if spared else ("Genocide" if self.route == "Genocide" else "Neutral")

    def run_personality_pass(self, monsters: List[Monster]) -> List[Monster]:
        """Enriches raw monster requests (name/role/dials) with traits + a battle-style summary."""
        print("\n=== PERSONALITY PASS: Monster Personality Agent ===")
        return [self.personality_agent.run(m.name, m.role, m.dials) for m in monsters]

    def run_prep_pass(self, monsters: List[Monster], rooms: List[Room]) -> dict:
        """Simulates a designer asking the Encounter Orchestrator for new content.

        Expects `monsters` to already carry battle-style traits (see
        run_personality_pass). Order matters here: AreaLayoutAgent must
        assign room.location before RoomDesignerAgent/DialogueWriter read
        it, and ActMenuDesignerAgent needs monster.traits, which is why
        layout runs first and ACT menus run last.
        """
        print("\n=== PREP PASS: Encounter Orchestrator ===")
        layout = self.encounter_orchestrator.run("layout", rooms)
        room_specs = [self.encounter_orchestrator.run("room", r) for r in rooms]
        act_menus = [self.encounter_orchestrator.run("act_menu", m) for m in monsters]
        return {"layout": layout, "room_specs": room_specs, "act_menus": act_menus}

    def run_battle_turn(self, monsters: List[Monster], rooms: List[Room]) -> dict:
        """One pass of the battle loop: attacks -> battle script -> turn staging.

        Expects `monsters` to already carry battle-style traits + ACT
        options, and `rooms` to already carry an assigned location (see
        run_personality_pass and run_prep_pass) -- BulletPatternDesigner,
        DialogueWriter, and BattleDirector all validate this and raise if
        a prior agent was skipped.
        """
        print("\n=== BATTLE TURN ===")

        attacks = self.bullet_pattern_agent.run(monsters, rooms)
        if not attacks:
            return {"monsters": monsters, "attacks": [], "battle_script": None, "turn_actions": []}

        active_attack = attacks[0]
        battle_script = self.dialogue_writer.run(active_attack, monsters, rooms, route=self.route)
        turn_actions = self.battle_director.run(battle_script, active_attack, rooms)

        return {
            "monsters": monsters,
            "attacks": attacks,
            "battle_script": battle_script,
            "turn_actions": turn_actions,
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
