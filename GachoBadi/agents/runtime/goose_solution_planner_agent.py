from __future__ import annotations

from typing import List

from agents.base import BaseAgent
from models import Building, Task, VerbPlan


class GooseSolutionPlannerAgent(BaseAgent):
    role = "Goose Solution Planner Agent"
    goal = "Plan at least one valid indirect solution to a task using only the goose's own verbs -- never dialogue."
    backstory = (
        "Borrowed from the Untitled Goose Game reference crew's Goose Verb Planner Agent: the "
        "goose never speaks, so this agent guarantees every task the Task Creator invents is "
        "actually solvable with honk/grab/pick up/duck/dash before the player ever sees it, and "
        "doubles as the source for an in-game hint if the player gets stuck."
    )

    VERBS = ["Honk", "Grab", "Pick up", "Duck", "Dash"]

    """
    Input:  a Task from TaskCreatorAgent, plus the building enriched by
            IslandLayoutAgent (needs .location) and BuildingDesignerAgent
            (needs .designed).
    Output: VerbPlan consumed by DirectorAgent, alongside the Writer's
            Screenplay.
    """

    def run(self, task: Task, buildings: List[Building]) -> VerbPlan:
        building = next((b for b in buildings if b.name == task.involves_building), None)
        if building is not None and not building.location:
            raise ValueError(
                f"GooseSolutionPlannerAgent requires '{building.name}' to have an assigned location "
                "-- run IslandLayoutAgent first."
            )
        if building is not None and not building.designed:
            raise ValueError(
                f"GooseSolutionPlannerAgent requires '{building.name}' to be designed "
                "-- run BuildingDesignerAgent first."
            )
        fallback_lines = [
            f"* SCENE: {building.location if building else 'the island'}.",
            f"* Goose: {self.VERBS[0]} near {building.name if building else 'the nearest prop'}.",
            f"* Goose: {self.VERBS[1]} {building.interactive_feature if building else 'the nearest object'}.",
            f"* Goose: {self.VERBS[2]} it and carry it toward {task.target_resident}.",
            f"* Objective resolves: {task.description}",
        ]
        plan_text = self.llm.generate(
            system=(
                "You write a short stage-direction-only action plan (no dialogue, ever) using "
                "only these goose verbs: Honk, Grab, Pick up, Duck, Dash, that indirectly solves "
                "the given community-building task."
            ),
            prompt=f"Task: {task.description}\nBuilding: {building}",
            fallback="\n".join(fallback_lines),
        )
        lines = plan_text.split("\n") if plan_text else fallback_lines
        self._log(f"planned verb sequence for task #{task.task_id} ({len(lines)} lines)")
        return VerbPlan(task_id=task.task_id, lines=lines)
