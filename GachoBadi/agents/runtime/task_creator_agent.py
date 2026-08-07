from __future__ import annotations

import math
from typing import List, Tuple

from agents.base import BaseAgent
from models import Building, Resident, Task


def build_catalog(residents: List[Resident], buildings: List[Building]) -> List[Tuple[str, str, str]]:
    """The lifetime task catalog: every (resident, other, building) premise
    slot the roster supports, in a fixed order. gdd.txt: '~30-40 one-time
    tasks, pre-authored the same way the resident roster and roles are --
    the Task Creator Agent's runtime job is to select and assemble an
    eligible premise... not to generate new premise text from scratch.'
    This is that catalog; TaskCreatorAgent.generate_set only ever slices
    from it, per that rule.

    Every ordered (resident, other) pair -- not just adjacent-in-list --
    times every building, so a resident/building combo is never generated
    twice: exhausting the catalog is what makes the true ending reachable
    and finite (see Game Completion in gdd.txt).
    """
    catalog: List[Tuple[str, str, str]] = []
    for resident in residents:
        for other in residents:
            if other.name == resident.name:
                continue
            for building in buildings:
                catalog.append((resident.name, other.name, building.name))
    return catalog


class TaskCreatorAgent(BaseAgent):
    role = "Task Creator Agent"
    goal = "Select and assemble the next 5-9-task set from the pre-authored lifetime catalog."
    backstory = (
        "One of the GDD's two 'One Wow' agents. An earlier version of this code generated one "
        "ad-lib task per invocation from 5 generic templates, with no concept of a set, a 75% "
        "threshold, or a finite catalog -- none of which matched gdd.txt's 'Scoping the task "
        "system concretely' section. This version selects real premises from build_catalog()'s "
        "pre-authored lifetime list in sets of 5-9, exactly as the GDD specifies; only the "
        "flavor text and goal-state phrasing are generated per premise, not the premise itself."
    )

    SET_SIZE_MIN = 5
    SET_SIZE_MAX = 9

    """
    Input:  residents enriched by CharacterPersonalityAgent (need .traits)
            and, when there's more than one resident, RelationshipAgent
            (need .relationships); buildings enriched by IslandLayoutAgent
            (need .location) and BuildingDesignerAgent (need .designed).
    Output: List[Task] consumed by GooseSolutionPlannerAgent (which
            approves or retires each candidate -- this agent does not
            certify solvability, per the GDD) and, for approved tasks,
            WriterAgent and the Director.
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

    @classmethod
    def threshold_for(cls, set_size: int) -> int:
        """75% of a set, rounded up -- e.g. 6 of 8 -- per gdd.txt."""
        return math.ceil(set_size * 0.75)

    def generate_set(
        self,
        catalog: List[Tuple[str, str, str]],
        offset: int,
        set_id: int,
        residents: List[Resident],
        buildings: List[Building],
        size: int = SET_SIZE_MAX,
    ) -> List[Task]:
        """Slices catalog[offset:offset+size] (clamped to SET_SIZE_MIN..MAX
        and to what's left) and turns each premise slot into a Task with a
        checkable goal_state, rather than inventing the premise fresh."""
        tasks: List[Task] = []
        residents_by_name = {r.name: r for r in residents}
        buildings_by_name = {b.name: b for b in buildings}

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

        size = max(self.SET_SIZE_MIN, min(self.SET_SIZE_MAX, size))
        slice_ = catalog[offset : offset + size]
        for i, (resident_name, other_name, building_name) in enumerate(slice_):
            resident = residents_by_name[resident_name]
            other = residents_by_name[other_name]
            building = buildings_by_name[building_name]
            relationship = resident.relationships.get(other.name, "acquaintances")
            template = self.TEMPLATES[(offset + i) % len(self.TEMPLATES)]
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
            goal_state = (
                f"{resident.name} and {other.name} are both present at {building.name} "
                f"with a positive reaction flag set on {other.name}"
            )
            tasks.append(
                Task(
                    task_id=offset + i + 1,
                    set_id=set_id,
                    description=description,
                    target_resident=resident.name,
                    other_resident=other.name,
                    involves_building=building.name,
                    goal_state=goal_state,
                )
            )
        self._log(f"generated set #{set_id}: {len(tasks)} task(s) (catalog offset {offset})")
        return tasks
