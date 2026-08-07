"""Relationship Backstory Content Agent -- adapted from
UntitledGooseGame_Multi_Agent's VillagerRoutineAgent.
"""
from __future__ import annotations

from agents.base import BaseAgent


class RelationshipBackstoryContentAgent(BaseAgent):
    role = "Relationship Backstory Content Agent"
    goal = (
        "Write the one-line authored backstory the GDD requires behind a relationship label, "
        "for Assignment #4's RAG-grounded, critic-checked content pipeline."
    )
    backstory = (
        "Adapted from UntitledGooseGame_Multi_Agent's Villager Routine Agent -- the same 'turn "
        "a structured value into one specific, non-generic sentence' pattern, pointed at "
        "relationship labels instead of routine dials. At the time this pipeline was built, the "
        "runtime RelationshipAgent (agents/runtime/relationship_agent.py) only assigned the "
        "label itself, never the 'why' Draft #9 made mandatory; that gap has since been closed "
        "there directly. This agent still serves Assignment #4's distinct purpose -- RAG "
        "grounding and critic verification -- independent of the runtime crew's own version."
    )

    LABEL_SEEDS = {
        "drifted apart": [
            "a mixed-up mail delivery",
            "a missed birthday",
            "moving to opposite ends of the island",
        ],
        "close friends": [
            "splitting a bakery order every week",
            "a shared umbrella during the first island storm",
        ],
        "friendly rivals": [
            "dueling garden competitions",
            "a running bet neither will admit to losing",
        ],
        "warm acquaintances": ["a polite nod every market day that never became more"],
        "budding crush": ["a dropped basket the other one picked up without being asked"],
    }

    def run(self, resident_a: str, resident_b: str, relationship_label: str, retrieved_context: str) -> str:
        seeds = self.LABEL_SEEDS.get(
            relationship_label, ["a small, half-remembered moment neither brought up again"]
        )
        seed = self.llm.choice(seeds)
        # Matches the GDD's own example format ("'drifted apart after a
        # mixed-up mail delivery'") rather than "X and Y are {label} after
        # Z", which reads fine for "drifted apart" but breaks grammatically
        # for labels like "budding crush" ("are budding crush").
        fallback = f"{resident_a} and {resident_b}: {relationship_label} -- {seed}."
        line = self.llm.generate(
            system=(
                "You write ONE short sentence: the specific, authored reason two Gacho Badi "
                "residents ended up in the given relationship state. Ground it in the provided "
                "GDD context's own tone and examples. Never write a generic 'they had a falling "
                "out' line with no specific cause -- the GDD explicitly calls a label alone "
                "insufficient content for a task."
            ),
            prompt=(
                f"GDD context:\n{retrieved_context}\n\nResident A: {resident_a}\n"
                f"Resident B: {resident_b}\nRelationship: {relationship_label}"
            ),
            fallback=fallback,
        )
        self._log(f"authored backstory for {resident_a}/{resident_b} ({relationship_label})")
        return line
