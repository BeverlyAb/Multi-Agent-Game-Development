from __future__ import annotations

from typing import List, Optional

from agents.base import BaseAgent
from definitions.models import Building, ChainReaction, Item, Resident, StagedAction, Task


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
        "step, and the one place in the crew where the goose's own unpredictability lives: "
        "which of the Item Interaction Agent's registered possible_outcomes actually happens is "
        "picked at random (seeded, so a given seed still replays identically), not because the "
        "Goose Solution Planner's verb choice was wrong or ambiguous -- a real goose's exact "
        "motion in front of a resident isn't fully determined by 'which verb was legal.' It "
        "never invents an outcome absent from that registered list -- the same hard boundary "
        "the Goose Solution Planner already holds for goose_actions -- so the *range* of what "
        "can happen is still fully authored and inspectable, only *which one* is left to chance."
    )

    """
    Input:  the Task (needs .target_resident, and .other_resident for a
            two-step chain), the Building it involves (needs
            .possible_outcomes, set by ItemInteractionAgent -- an empty
            list means this affordance has no resident follow-up at all,
            which is common and not an error), and the current resident
            roster (to resolve .other_resident to an actual Resident to
            draw in).
    Output: a ChainReaction consumed by WriterAgent (narrates each step)
            and DirectorAgent (stages each step and folds the second step,
            when present, into what used to be a generic "other_resident
            notices" beat). Zero steps when the building has no registered
            possible_outcomes; one step when the randomly-picked outcome
            has no chain_effect or there's no other_resident to draw in;
            two steps only when both are present -- a task is never
            required to chain, per gdd.txt's "most tasks are non-sequential"
            framing, and even a chain-capable building doesn't chain every
            time it's picked.
    """

    def run(self, task: Task, building: Optional[Building], residents: List[Resident]) -> ChainReaction:
        if building is None or not building.possible_outcomes:
            self._log(f"task #{task.task_id}: no registered resident outcome -- no chain to stage")
            return ChainReaction(task_id=task.task_id, steps=[])

        # This is the one random draw in the whole crew that isn't just
        # flavor text: which registered outcome actually happens this time
        # -- seeded, so a given seed still replays identically end to end,
        # but a different seed (or a later draw in the same run) can land
        # on a different, equally-legal outcome for the exact same
        # building/task.
        outcome = self.llm.choice(building.possible_outcomes)
        location = building.location or "the island"
        steps: List[StagedAction] = [
            StagedAction(
                actor=task.target_resident,
                action=f"follows up on what the goose left behind: {outcome.resident_action}",
                location=location,
            )
        ]

        chain_effect = ""
        other = next((r for r in residents if r.name == task.other_resident), None) if task.other_resident else None
        if outcome.chain_effect and other is not None:
            chain_effect = outcome.chain_effect
            steps.append(
                StagedAction(
                    actor=other.name,
                    action=f"is drawn over by it -- {chain_effect}",
                    location=location,
                )
            )

        self._log(
            f"task #{task.task_id}: rolled outcome '{outcome.resident_action}' -> staged {len(steps)}-step chain"
            + (f" ending in {other.name} being drawn in" if chain_effect and other else "")
        )
        return ChainReaction(task_id=task.task_id, steps=steps, chain_effect=chain_effect)
