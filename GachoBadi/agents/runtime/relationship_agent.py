from __future__ import annotations

from typing import List

from agents.base import BaseAgent
from models import Resident


class RelationshipAgent(BaseAgent):
    role = "Relationship Agent"
    goal = "Work out how every pair of residents on the island feels about each other."
    backstory = (
        "Borrowed from the Tomodachi Life reference crew: the original 8-agent GDD had no way "
        "to make a task like 'these two used to be close' mean anything. This agent is what "
        "turns the island's new community-building premise into something the Task Creator can "
        "actually generate tasks from."
    )

    """
    Input:  residents already enriched by CharacterPersonalityAgent
            (need .traits).
    Output: resident.relationships populated in place on every resident
            (other resident name -> relationship label), required by
            TaskCreatorAgent whenever there's more than one resident.
    """

    def _label(self, a: Resident, b: Resident) -> str:
        a_candid = "candid" in a.traits
        b_candid = "candid" in b.traits
        a_energetic = "energetic" in a.traits
        b_energetic = "energetic" in b.traits
        a_excitable = "excitable" in a.traits
        b_excitable = "excitable" in b.traits
        if a_energetic and b_energetic:
            return "friendly rivals"
        if a_excitable and b_excitable:
            return "close friends"
        if a_candid != b_candid:
            return "drifted apart"
        return "warm acquaintances"

    def run(self, residents: List[Resident]) -> List[Resident]:
        for resident in residents:
            if not resident.traits:
                raise ValueError(
                    f"RelationshipAgent requires '{resident.name}' to carry personality traits "
                    "-- run CharacterPersonalityAgent first."
                )
        if len(residents) < 2:
            self._log("fewer than 2 residents -> no relationships to compute")
            return residents
        for i, resident in enumerate(residents):
            other = residents[(i + 1) % len(residents)]
            fallback = self._label(resident, other)
            label = self.llm.generate(
                system="You name, in 2-4 words, the relationship between two life-sim residents based on their personality traits.",
                prompt=f"Resident A: {resident.name} ({resident.traits})\nResident B: {other.name} ({other.traits})",
                fallback=fallback,
            )
            resident.relationships[other.name] = label
        self._log(f"mapped relationships: {[(r.name, r.relationships) for r in residents]}")
        return residents
