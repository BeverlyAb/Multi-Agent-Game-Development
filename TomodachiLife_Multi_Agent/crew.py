"""The Crew: coordinates all eleven agents through a personality pass, a
relationship pass, a prep pass (voice/appearance/apartment/layout design),
and one event-tick pass (events -> skit -> staged moment -> news bulletin),
matching the data flow in DIAGRAM.md.
"""
from __future__ import annotations

from dataclasses import asdict
from typing import List

from agents import (
    DirectorAgent,
    EventCreatorAgent,
    IslandOrchestrator,
    MiiPersonalityAgent,
    NewscasterAgent,
    RelationshipAgent,
    SkitWriterAgent,
)
from llm_client import LLMClient
from models import Apartment, Mii


class TomodachiLifeCrew:
    """Orchestrates the Tomodachi-Life-style island agents for one daily event tick."""

    def __init__(self, seed: int = 7):
        self.llm = LLMClient(seed=seed)
        self.personality_agent = MiiPersonalityAgent(self.llm)
        self.relationship_agent = RelationshipAgent(self.llm)
        self.event_creator = EventCreatorAgent(self.llm)
        self.skit_writer = SkitWriterAgent(self.llm)
        self.director = DirectorAgent(self.llm)
        self.newscaster = NewscasterAgent(self.llm)
        self.island_orchestrator = IslandOrchestrator(self.llm)

    def run_personality_pass(self, miis: List[Mii]) -> List[Mii]:
        """Enriches raw Mii requests (name/role/dials) with traits + a personality summary."""
        print("\n=== PERSONALITY PASS: Mii Personality Agent ===")
        return [self.personality_agent.run(m.name, m.role, m.dials) for m in miis]

    def run_relationship_pass(self, miis: List[Mii]) -> List[Mii]:
        """Maps how every pair of Miis feels about each other. Requires .traits."""
        print("\n=== RELATIONSHIP PASS: Relationship Agent ===")
        return self.relationship_agent.run(miis)

    def run_prep_pass(self, miis: List[Mii], apartments: List[Apartment]) -> dict:
        """Simulates a designer asking the Island Orchestrator for new content.

        Expects `miis` to already carry personality traits (see
        run_personality_pass). Order matters here: IslandLayoutAgent must
        assign apartment.location before ApartmentDesignerAgent/SkitWriter
        read it, and MiiVoiceAgent/MiiAppearanceAgent need mii.traits,
        which is why layout runs first and voice/appearance run last.
        """
        print("\n=== PREP PASS: Island Orchestrator ===")
        layout = self.island_orchestrator.run("layout", apartments)
        apartment_specs = [self.island_orchestrator.run("apartment", a) for a in apartments]
        voices = [self.island_orchestrator.run("voice", m) for m in miis]
        appearances = [self.island_orchestrator.run("appearance", m) for m in miis]
        return {"layout": layout, "apartment_specs": apartment_specs, "voices": voices, "appearances": appearances}

    def run_event_tick(self, miis: List[Mii], apartments: List[Apartment]) -> dict:
        """One pass of the daily loop: events -> skit -> staged moment -> news bulletin.

        Expects `miis` to already carry traits + relationships + voice +
        appearance, and `apartments` to already carry an assigned
        location + design (see run_personality_pass, run_relationship_pass,
        and run_prep_pass) -- EventCreator, SkitWriter, Director, and
        Newscaster all validate this and raise if a prior agent was
        skipped.
        """
        print("\n=== EVENT TICK ===")

        events = self.event_creator.run(miis, apartments)
        if not events:
            return {"miis": miis, "events": [], "skit": None, "staged_moments": [], "news": None}

        active_event = events[0]
        skit = self.skit_writer.run(active_event, miis, apartments)
        staged_moments = self.director.run(skit, active_event, apartments)
        news = self.newscaster.run(staged_moments, active_event)

        return {
            "miis": miis,
            "events": events,
            "skit": skit,
            "staged_moments": staged_moments,
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
