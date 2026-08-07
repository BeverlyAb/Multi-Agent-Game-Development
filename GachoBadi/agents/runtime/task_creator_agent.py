from __future__ import annotations

from typing import List

from agents.base import BaseAgent
from models import Building, Resident, Task


class TaskCreatorAgent(BaseAgent):
    role = "Task Creator Agent"
    goal = "Generate an open-ended task list from the residents and buildings currently on the island."
    backstory = (
        "One of the GDD's two 'One Wow' agents: batch-generates the tasks that gate island "
        "expansion. Draft #2 of the GDD reframed these tasks around community-building rather "
        "than mischief for its own sake, so this agent now reads relationships, not just traits."
    )

    """
    Input:  residents enriched by CharacterPersonalityAgent (need .traits)
            and, when there's more than one resident, RelationshipAgent
            (need .relationships); buildings enriched by IslandLayoutAgent
            (need .location) and BuildingDesignerAgent (need .designed).
    Output: List[Task] consumed by WriterAgent and GooseSolutionPlannerAgent.
    Removing CharacterPersonalityAgent, RelationshipAgent, IslandLayoutAgent,
    or BuildingDesignerAgent breaks this agent outright (raises ValueError
    below) rather than degrading silently, so the dependency is provable,
    not just cosmetic.
    """

    TEMPLATES = [
        "Get {resident} to reconnect with {other}, who they've drifted apart from, near the {building}.",
        "Help {resident} and {other} ({relationship}) patch up a disagreement at the {building}.",
        "Nudge {resident} to notice {other} sitting alone near the {building} and invite them over.",
        "Get {resident} to return something of {other}'s at the {building}, giving them a reason to talk.",
        "Bring {resident} and {other} together at the {building} despite being {relationship}.",
    ]

    def run(self, residents: List[Resident], buildings: List[Building]) -> List[Task]:
        tasks: List[Task] = []
        if not residents or not buildings:
            self._log("no residents/buildings yet -> no tasks available")
            return tasks
        for resident in residents:
            if not resident.traits:
                raise ValueError(
                    f"TaskCreatorAgent requires '{resident.name}' to carry personality traits "
                    "-- run CharacterPersonalityAgent first."
                )
        if len(residents) > 1:
            for resident in residents:
                if not resident.relationships:
                    raise ValueError(
                        f"TaskCreatorAgent requires '{resident.name}' to have mapped relationships "
                        "-- run RelationshipAgent first."
                    )
        for building in buildings:
            if not building.location:
                raise ValueError(
                    f"TaskCreatorAgent requires '{building.name}' to have an assigned location "
                    "-- run IslandLayoutAgent first."
                )
            if not building.designed:
                raise ValueError(
                    f"TaskCreatorAgent requires '{building.name}' to be designed "
                    "-- run BuildingDesignerAgent first."
                )
        for i, resident in enumerate(residents):
            building = buildings[i % len(buildings)]
            other = residents[(i + 1) % len(residents)]
            relationship = resident.relationships.get(other.name, "acquaintances")
            template = self.TEMPLATES[i % len(self.TEMPLATES)]
            fallback = template.format(
                resident=resident.name, other=other.name, relationship=relationship, building=building.name,
            )
            description = self.llm.generate(
                system="You invent one short, open-ended task for a goose-sim game that nudges two residents toward connection -- friendship or community belonging as much as romance -- through an indirect, physical-comedy interaction.",
                prompt=(
                    f"Resident: {resident.name} ({resident.role}, traits: {resident.traits})\n"
                    f"Other resident: {other.name}, relationship: {relationship}\n"
                    f"Building: {building.name} at {building.location} ({building.interactive_feature})"
                ),
                fallback=fallback,
            )
            tasks.append(
                Task(
                    task_id=i + 1,
                    description=description,
                    target_resident=resident.name,
                    other_resident=other.name if other.name != resident.name else None,
                    involves_building=building.name,
                )
            )
        self._log(f"generated {len(tasks)} task(s)")
        return tasks
