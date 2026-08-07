from __future__ import annotations

from typing import List, Optional

from agents.base import BaseAgent
from definitions.models import Building, ChainReaction, Resident, Screenplay, Task


class WriterAgent(BaseAgent):
    role = "Writer Agent"
    goal = "Given a task and its actors (and their relationship to each other), write screenplay-style dialogue and action cues."
    backstory = (
        "Produces the 'script' the Director later blocks into gameplay, now aware of how the "
        "two residents in a task actually feel about each other. Since Draft #11 it's also "
        "aware of the Chain Reaction Agent's output when one exists, so a task that chains -- "
        "the goose drops a hose, the resident waters the garden, a second resident is drawn "
        "over by the bloom -- reads as one continuous cause-and-effect beat instead of the "
        "resident's own action going unmentioned between the goose's plan and the payoff line."
    )

    """
    Input:  a Task from TaskCreatorAgent, plus the resident enriched by
            CharacterAppearanceAgent (needs .appearance), the building
            enriched by IslandLayoutAgent (needs .location) and
            BuildingDesignerAgent (needs .designed), and optionally the
            ChainReaction ChainReactionAgent produced for this task (None
            or zero-step when this task's building has no registered
            resident follow-up -- common, and not an error).
    Output: Screenplay consumed by DirectorAgent. Any line that resolves a
            relationship must reference RelationshipAgent's specific
            backstory for that pair, not just the label -- "a label alone
            is never sufficient content for a task" (gdd.txt).
    """

    def run(
        self,
        task: Task,
        residents: List[Resident],
        buildings: List[Building],
        chain: Optional[ChainReaction] = None,
    ) -> Screenplay:
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
        ]
        # When the Chain Reaction Agent staged a real follow-up, narrate it
        # explicitly instead of jumping straight from the goose's action to
        # the resolution line -- otherwise the resident's own use of the
        # object, and whoever it draws in, never actually get written.
        if chain and chain.steps:
            fallback_lines.append(f"{chain.steps[0].actor}: ({chain.steps[0].action})")
            if len(chain.steps) > 1:
                fallback_lines.append(f"{chain.steps[1].actor}: ({chain.steps[1].action})")
        fallback_lines.append(
            f"{resident.name if resident else 'RESIDENT'}: (startled, then softening, remembering {backstory or 'them'}) \"Oh -- it's you.\""
        )
        fallback_lines.append(f"(Task resolves: {task.description})")
        chain_summary = (
            f"{chain.steps[0].actor} {chain.steps[0].action}"
            + (f"; then {chain.steps[1].actor} {chain.steps[1].action}" if chain and len(chain.steps) > 1 else "")
            if chain and chain.steps
            else "(no chain reaction staged for this task)"
        )
        screenplay_text = self.llm.generate(
            system=(
                "You write a short screenplay scene (dialogue + directional cues) for a "
                "community-building goose-sim task. The line that resolves the relationship "
                "MUST reference the given authored backstory specifically -- never a generic "
                "reconciliation line with no cause. If a chain reaction is given, narrate it as "
                "its own beat between the goose's action and the resolution -- never skip "
                "straight past what the resident (and, if present, the second resident) "
                "actually did."
            ),
            prompt=(
                f"Task: {task.description}\nActor: {resident}\nOther resident: "
                f"{other.name if other else None} ({relationship})\nAuthored backstory: "
                f"{backstory}\nBuilding: {building}\nChain reaction: {chain_summary}"
            ),
            fallback="\n".join(fallback_lines),
        )
        lines = screenplay_text.split("\n") if screenplay_text else fallback_lines
        self._log(f"wrote screenplay for task #{task.task_id} ({len(lines)} lines)")
        return Screenplay(task_id=task.task_id, lines=lines)
