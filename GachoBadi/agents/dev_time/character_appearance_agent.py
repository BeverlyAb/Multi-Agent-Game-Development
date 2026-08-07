from __future__ import annotations

from agents.base import BaseAgent
from models import Resident


class CharacterAppearanceAgent(BaseAgent):
    role = "Character Appearance Agent"
    goal = "Design a resident's visual appearance from their role and personality."

    """
    Input:  a Resident already enriched by CharacterPersonalityAgent
            (needs .traits).
    Output: an appearance spec, written into resident.appearance so
            WriterAgent can require and use it downstream.
    """

    def run(self, resident: Resident) -> str:
        if not resident.traits:
            raise ValueError(
                f"CharacterAppearanceAgent requires '{resident.name}' to carry personality traits "
                "-- run CharacterPersonalityAgent first."
            )
        fallback = (
            f"{resident.name}: a {resident.role} with a look reflecting "
            f"{', '.join(resident.traits)} -- palette and silhouette chosen to read at a glance."
        )
        spec = self.llm.generate(
            system="You write a one-paragraph appearance spec for a life-sim character.",
            prompt=f"Resident: {resident}",
            fallback=fallback,
        )
        resident.appearance = spec
        self._log(f"designed appearance for {resident.name}")
        return spec
