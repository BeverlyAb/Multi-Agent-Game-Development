from __future__ import annotations

from typing import List

from agents.base import BaseAgent
from models import Building, Screenplay, StagedAction, Task, VerbPlan


class DirectorAgent(BaseAgent):
    role = "Director Agent"
    goal = "Take the Writer's screenplay and the Goose Solution Planner's verb plan and stage both as the actions residents/goose actually perform."
    backstory = "The GDD's other 'One Wow' agent: converts script and verb plan into the active gameplay the player sees."

    """
    Input:  the Screenplay from WriterAgent, the VerbPlan from
            GooseSolutionPlannerAgent, the active Task, and buildings
            enriched by IslandLayoutAgent (needs .location, used as the
            physical staging location instead of just the building's name).
    Output: List[StagedAction] -- the actual gameplay behavior; this is
            the crew's terminal, player-visible output.
    """

    def run(
        self, screenplay: Screenplay, verb_plan: VerbPlan, task: Task, buildings: List[Building]
    ) -> List[StagedAction]:
        if not screenplay.lines:
            raise ValueError(
                f"DirectorAgent has nothing to stage for task #{task.task_id} "
                "-- WriterAgent returned an empty screenplay."
            )
        if not verb_plan.lines:
            raise ValueError(
                f"DirectorAgent has no goose actions to stage for task #{task.task_id} "
                "-- GooseSolutionPlannerAgent returned an empty verb plan."
            )
        building = next((b for b in buildings if b.name == task.involves_building), None)
        location = building.location if building and building.location else (task.involves_building or "island")
        staged = [
            StagedAction(actor="Goose", action=f"execute plan: {verb_plan.lines[0]}", location=location),
            StagedAction(
                actor=task.target_resident,
                action=f"react and progress toward: {task.description}",
                location=location,
            ),
        ]
        if task.other_resident:
            staged.append(
                StagedAction(actor=task.other_resident, action="notice, warm up, and reconnect", location=location)
            )
        self._log(f"staged {len(staged)} action(s) for task #{task.task_id} at {location}")
        return staged
