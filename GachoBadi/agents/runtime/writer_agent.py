from __future__ import annotations

from typing import List

from agents.base import BaseAgent
from models import Building, Resident, Screenplay, Task


class WriterAgent(BaseAgent):
    role = "Writer Agent"
    goal = "Given a task and its actors (and their relationship to each other), write screenplay-style dialogue and action cues."
    backstory = "Produces the 'script' the Director later blocks into gameplay, now aware of how the two residents in a task actually feel about each other."

    """
    Input:  a Task from TaskCreatorAgent, plus the resident enriched by
            CharacterAppearanceAgent (needs .appearance) and the building
            enriched by IslandLayoutAgent (needs .location) and
            BuildingDesignerAgent (needs .designed).
    Output: Screenplay consumed by DirectorAgent. Any line that resolves a
            relationship must reference RelationshipAgent's specific
            backstory for that pair, not just the label -- "a label alone
            is never sufficient content for a task" (gdd.txt).
    """

    def run(self, task: Task, residents: List[Resident], buildings: List[Building]) -> Screenplay:
        resident = next((r for r in residents if r.name == task.target_resident), None)
        other = next((r for r in residents if r.name == task.other_resident), None)
        building = next((b for b in buildings if b.name == task.involves_building), None)
        if resident is not None and not resident.appearance:
            raise ValueError(
                f"WriterAgent requires '{resident.name}' to have an appearance spec "
                "-- run CharacterAppearanceAgent first."
            )
        if building is not None and not building.location:
            raise ValueError(
                f"WriterAgent requires '{building.name}' to have an assigned location "
                "-- run IslandLayoutAgent first."
            )
        if building is not None and not building.designed:
            raise ValueError(
                f"WriterAgent requires '{building.name}' to be designed "
                "-- run BuildingDesignerAgent first."
            )
        if resident is not None and other is not None and other.name not in resident.relationship_backstories:
            raise ValueError(
                f"WriterAgent requires an authored backstory for {resident.name}/{other.name} "
                "-- run RelationshipAgent first."
            )
        relationship = resident.relationships.get(other.name, "acquaintances") if resident and other else "acquaintances"
        backstory = (
            resident.relationship_backstories.get(other.name, "")
            if resident and other
            else ""
        )
        fallback_lines = [
            f"INT./EXT. {building.name.upper() if building else 'ISLAND'} - {building.location.upper() if building else 'DAY'}",
            f"({resident.name if resident else 'RESIDENT'} looks like: {resident.appearance if resident else 'a nearby resident'}.)",
            f"(They are {relationship} with {other.name if other else 'a neighbor'} -- {backstory or 'no history recorded yet'})",
            f"GOOSE: (honks meaningfully near the {building.name if building else 'nearest prop'})",
            f"{resident.name if resident else 'RESIDENT'}: (startled, then softening, remembering {backstory or 'them'}) \"Oh -- it's you.\"",
            f"(Task resolves: {task.description})",
        ]
        screenplay_text = self.llm.generate(
            system=(
                "You write a short screenplay scene (dialogue + directional cues) for a "
                "community-building goose-sim task. The line that resolves the relationship "
                "MUST reference the given authored backstory specifically -- never a generic "
                "reconciliation line with no cause."
            ),
            prompt=(
                f"Task: {task.description}\nActor: {resident}\nOther resident: "
                f"{other.name if other else None} ({relationship})\nAuthored backstory: "
                f"{backstory}\nBuilding: {building}"
            ),
            fallback="\n".join(fallback_lines),
        )
        lines = screenplay_text.split("\n") if screenplay_text else fallback_lines
        self._log(f"wrote screenplay for task #{task.task_id} ({len(lines)} lines)")
        return Screenplay(task_id=task.task_id, lines=lines)
