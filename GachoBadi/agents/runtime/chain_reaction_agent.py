from __future__ import annotations

from typing import List, Optional

from agents.base import BaseAgent
from models import Building, ChainReaction, Item, Resident, StagedAction, Task


class ChainReactionAgent(BaseAgent):
    role = "Chain Reaction Agent"
    goal = (
        "Extend a single goose action into a short, readable cause-and-effect scene: the "
        "target resident's own follow-up action on whatever the goose just dropped or "
        "triggered, and, only where the Item Interaction Agent's schema registers one, a "
        "second resident drawn in by that follow-up."
    )
    backstory = (
        "Added in Draft #11 to close a gap the Item Interaction Agent's own player-facing "
        "description already promised -- 'understandable chains of cause and effect' -- but "
        "nothing in the architecture actually produced. Before this agent, every task's "
        "gameplay stopped at the goose's own action: honk, grab, drop, one resident reacts on "
        "the spot, done. That undersells the GDD's own hose example: the goose drops the hose "
        "in front of a resident, the resident is the one who actually waters the garden with "
        "it, and it's the garden coming back to life -- not the goose's own action directly -- "
        "that draws a second resident over to admire it. This agent is that missing middle "
        "step. It never invents a resident action or a chain effect absent from the Item "
        "Interaction Agent's schema (Building/Item .resident_actions / .chain_effect) -- the "
        "same hard boundary the Goose Solution Planner already holds for goose_actions -- so a "
        "chain reaction is exactly as findable as the affordance graph allows, never an ad-lib "
        "the player can't reason about."
    )

    """
    Input:  the Task (needs .target_resident, and .other_resident for a
            two-step chain), the Building it involves (needs
            .resident_actions and .chain_effect, set by ItemInteractionAgent
            -- an empty resident_actions list means this affordance has no
            resident follow-up at all, which is common and not an error),
            and the current resident roster (to resolve .other_resident to
            an actual Resident to draw in).
    Output: a ChainReaction consumed by WriterAgent (narrates each step)
            and DirectorAgent (stages each step and folds the second step,
            when present, into what used to be a generic "other_resident
            notices" beat). Zero steps when the building has no registered
            resident_actions; one step when it does but there's no
            chain_effect or no other_resident to draw in; two steps only
            when both are present -- a task is never required to chain,
            per gdd.txt's "most tasks are non-sequential" framing.
    """

    def run(self, task: Task, building: Optional[Building], residents: List[Resident]) -> ChainReaction:
        if building is None or not building.resident_actions:
            self._log(f"task #{task.task_id}: no registered resident action -- no chain to stage")
            return ChainReaction(task_id=task.task_id, steps=[])

        location = building.location or "the island"
        resident_action = building.resident_actions[0]
        steps: List[StagedAction] = [
            StagedAction(
                actor=task.target_resident,
                action=f"follows up on what the goose left behind: {resident_action}",
                location=location,
            )
        ]

        chain_effect = ""
        other = next((r for r in residents if r.name == task.other_resident), None) if task.other_resident else None
        if building.chain_effect and other is not None:
            chain_effect = building.chain_effect
            steps.append(
                StagedAction(
                    actor=other.name,
                    action=f"is drawn over by it -- {chain_effect}",
                    location=location,
                )
            )

        self._log(
            f"task #{task.task_id}: staged {len(steps)}-step chain"
            + (f" ending in {other.name} being drawn in" if chain_effect and other else "")
        )
        return ChainReaction(task_id=task.task_id, steps=steps, chain_effect=chain_effect)
