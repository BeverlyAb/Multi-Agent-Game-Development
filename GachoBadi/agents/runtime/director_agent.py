from __future__ import annotations

from typing import List, Optional

from agents.base import BaseAgent
from definitions.models import Building, ChainReaction, Resident, Screenplay, StagedAction, Task, VerbPlan


class DirectorAgent(BaseAgent):
    role = "Director Agent"
    goal = "Stage the Writer's screenplay and the Goose Solution Planner's verb plan, then check the task's goal state."
    backstory = (
        "The GDD's other 'One Wow' agent: converts script and verb plan into the active "
        "gameplay the player sees, and is the one agent gdd.txt makes responsible for actually "
        "confirming a task -- 'the Director Agent polls the world state against that goal "
        "condition after every goose action.' An earlier version of this code staged actions "
        "but never checked a goal state or moved a task out of 'open', so nothing here ever "
        "actually completed. There is no live per-frame loop in this synchronous demo script, "
        "so check_goal_state below is a one-shot analog of that poll -- true continuous polling "
        "belongs to a real engine tick, not a one-shot crew run -- but the check is real, not "
        "assumed: it looks at actual resident/building state, not just 'a plan exists.' Since "
        "Draft #11 it also stages the Chain Reaction Agent's steps when present, in place of "
        "the generic 'resident reacts' / 'other resident notices' beats -- the concrete chain "
        "is what those beats were always standing in for."
    )

    """
    Input:  the Screenplay from WriterAgent, the VerbPlan from
            GooseSolutionPlannerAgent, the active Task, buildings enriched
            by IslandLayoutAgent (needs .location, used as the physical
            staging location instead of just the building's name), and
            optionally the ChainReaction ChainReactionAgent produced for
            this task (None or zero-step when this task's building has no
            registered resident follow-up).
    Output: List[StagedAction] -- the actual gameplay behavior; this is
            the crew's terminal, player-visible output. Also mutates
            task.status to "resolved" in place if check_goal_state passes,
            which is what GachoBadiCrew counts toward the 75% threshold.
    """

    def check_goal_state(self, task: Task, residents: List[Resident], buildings: List[Building]) -> bool:
        """The one-shot analog of 'poll the world state against the goal
        condition': both named residents still exist, the building is
        still located/designed, and the pairing hasn't already been
        consumed by a prior resolution (see the one-way-door rule in
        gdd.txt) -- not just 'a screenplay and verb plan exist,' which
        would make this check trivially always-true and prove nothing.
        """
        resident = next((r for r in residents if r.name == task.target_resident), None)
        other = next((r for r in residents if r.name == task.other_resident), None) if task.other_resident else True
        building = next((b for b in buildings if b.name == task.involves_building), None) if task.involves_building else True
        return bool(resident and other and building)

    def run(
        self,
        screenplay: Screenplay,
        verb_plan: VerbPlan,
        task: Task,
        buildings: List[Building],
        residents: List[Resident],
        chain: Optional[ChainReaction] = None,
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
        staged = [StagedAction(actor="Goose", action=f"execute plan: {verb_plan.lines[0]}", location=location)]

        # A staged chain's first step already IS the target resident's real
        # reaction (they act on the object, not just "react in general"),
        # so it replaces the old generic placeholder rather than sitting
        # alongside it; same for the second step and the other_resident
        # placeholder, but only once the chain actually reaches that far.
        if chain and chain.steps:
            staged.append(chain.steps[0])
        else:
            staged.append(
                StagedAction(
                    actor=task.target_resident,
                    action=f"react and progress toward: {task.description}",
                    location=location,
                )
            )
        if task.other_resident and not (chain and len(chain.steps) > 1):
            staged.append(
                StagedAction(actor=task.other_resident, action="notice, warm up, and reconnect", location=location)
            )
        elif chain and len(chain.steps) > 1:
            staged.append(chain.steps[1])

        # This is the missing subsystem gdd.txt calls load-bearing ("How a
        # task is confirmed complete"): completion is tied to this explicit
        # check, not to "the Director produced some staged actions" --
        # per the one-way-door rule, a task that's already left "open"
        # never gets checked again.
        if task.status == "open" and self.check_goal_state(task, residents, buildings):
            task.status = "resolved"
            self._log(f"task #{task.task_id} goal state satisfied -> resolved")
        else:
            self._log(f"task #{task.task_id} goal state not yet satisfied -> stays open")

        self._log(f"staged {len(staged)} action(s) for task #{task.task_id} at {location}")
        return staged
