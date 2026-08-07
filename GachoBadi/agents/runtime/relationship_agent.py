from __future__ import annotations

from itertools import combinations
from typing import List

from agents.base import BaseAgent
from definitions.models import Resident


class RelationshipAgent(BaseAgent):
    role = "Relationship Agent"
    goal = "Work out how every pair of residents on the island feels about each other -- and why."
    backstory = (
        "Borrowed from the Tomodachi Life reference crew: the original 8-agent GDD had no way "
        "to make a task like 'these two used to be close' mean anything. This agent is what "
        "turns the island's new community-building premise into something the Task Creator can "
        "actually generate tasks from. Draft #9 of the GDD made a one-line authored backstory "
        "mandatory alongside the label ('a label alone is never sufficient content for a "
        "task') -- this agent produces both, not just the label a previous version of this "
        "code stopped at."
    )

    """
    Input:  residents already enriched by CharacterPersonalityAgent
            (need .traits).
    Output: resident.relationships AND resident.relationship_backstories
            populated in place on every resident (other resident name ->
            label, and other resident name -> the authored "why"),
            required by TaskCreatorAgent whenever there's more than one
            resident, and by WriterAgent when a task involving that pair
            resolves.
    """

    # Seeds a specific, non-generic backstory beat per label, matching the
    # GDD's own example ("drifted apart after a mixed-up mail delivery")
    # instead of a generic "they had a falling out" line with no cause.
    BACKSTORY_SEEDS = {
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
        # Every unordered pair, not a same-length cycle through the list --
        # a cycle only happens to cover every pair when there are exactly 3
        # residents; the task catalog (build_catalog) enumerates every
        # ordered pair for the *whole* roster, so every one of them needs a
        # relationship state on both sides, however large the roster gets.
        for resident, other in combinations(residents, 2):
            fallback = self._label(resident, other)
            label = self.llm.generate(
                system="You name, in 2-4 words, the relationship between two life-sim residents based on their personality traits.",
                prompt=f"Resident A: {resident.name} ({resident.traits})\nResident B: {other.name} ({other.traits})",
                fallback=fallback,
            )

            seeds = self.BACKSTORY_SEEDS.get(label, ["a small, half-remembered moment neither brought up again"])
            seed = self.llm.choice(seeds)
            backstory_fallback = f"{resident.name} and {other.name}: {label} -- {seed}."
            backstory = self.llm.generate(
                system=(
                    "You write ONE short sentence: the specific, authored reason two residents "
                    "ended up in the given relationship state. Never write a generic 'they had "
                    "a falling out' line with no specific cause."
                ),
                prompt=f"Resident A: {resident.name}\nResident B: {other.name}\nRelationship: {label}",
                fallback=backstory_fallback,
            )

            # A relationship is one shared state, not two independent ones --
            # set on both sides so a task can name either resident as the
            # target and still find it.
            resident.relationships[other.name] = label
            other.relationships[resident.name] = label
            resident.relationship_backstories[other.name] = backstory
            other.relationship_backstories[resident.name] = backstory

        self._log(f"mapped relationships: {[(r.name, r.relationships) for r in residents]}")
        return residents
