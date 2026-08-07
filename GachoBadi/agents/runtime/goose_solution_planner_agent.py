from __future__ import annotations

from typing import List, Optional

from agents.base import BaseAgent
from definitions.models import Building, Item, Task, VerbPlan


class GooseSolutionPlannerAgent(BaseAgent):
    role = "Goose Solution Planner Agent"
    goal = "Approve, modify, or retire each candidate task by proving a solution using only registered goose affordances."
    backstory = (
        "Borrowed from the Untitled Goose Game reference crew's Goose Verb Planner Agent: the "
        "goose never speaks, so this agent guarantees every task the Task Creator invents is "
        "actually solvable with honk/grab/drop/duck/dash before the player ever sees it, and "
        "doubles as the source for an in-game hint if the player gets stuck. Per gdd.txt: 'The "
        "Task Creator does not certify solvability... only approved tasks enter the "
        "player-facing set' -- an earlier version of this code skipped that gate entirely and "
        "handed the Task Creator's first candidate straight to staging. This version doesn't: "
        "run() returns None for anything it can't prove solvable against the Item Interaction "
        "Agent's registered actions, and the caller (GachoBadiCrew) retires that task instead of "
        "staging it."
    )

    VERBS = ["Honk", "Grab", "Drop", "Duck", "Dash"]

    """
    Input:  a Task from TaskCreatorAgent, plus the building enriched by
            IslandLayoutAgent (needs .location), BuildingDesignerAgent
            (needs .designed), and ItemInteractionAgent (needs
            .goose_actions -- the base legal verbs this agent may use;
            it cannot invent an action absent from that list). If the
            task also has an involves_item, and that Item has been
            enriched by ItemInteractionAgent (.designed), that item's own
            .goose_actions are folded in too -- a task's legal verbs are
            never limited to one building.kind's fixed pair alone.
    Output: a VerbPlan consumed by DirectorAgent, or None if the building
            has no registered goose_actions -- the caller must retire the
            task rather than stage an invented solution. This is the
            planner's hard dependency on ItemInteractionAgent: skip that
            agent and every task in the set retires, provably, not just
            by convention.
    """

    def run(self, task: Task, buildings: List[Building], items: Optional[List[Item]] = None) -> Optional[VerbPlan]:
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
        if building is not None and not building.goose_actions:
            self._log(
                f"task #{task.task_id} UNSOLVABLE -- '{building.name}' has no registered goose "
                "actions (run ItemInteractionAgent first); retiring rather than inventing one"
            )
            return None

        item = next((i for i in (items or []) if i.name == task.involves_item), None) if task.involves_item else None
        legal_verbs = list(building.goose_actions) if building else list(self.VERBS)
        if item is not None and item.designed and item.goose_actions:
            # Merge, de-duplicated, order preserved -- an item never
            # narrows what the building itself already allows, only adds
            # to it (see ItemInteractionAgent.ITEM_ACTIONS).
            legal_verbs = list(dict.fromkeys(legal_verbs + item.goose_actions))

        fallback_lines = [
            f"* SCENE: {building.location if building else 'the island'}.",
            f"* Goose: {legal_verbs[0]} near {building.name if building else 'the nearest prop'}.",
        ]
        if item is not None and item.designed and item.goose_actions:
            # Give the item its own explicit step rather than letting it
            # sit unused in legal_verbs -- otherwise the deterministic
            # fallback (the only plan text produced with no LLM provider
            # configured) would never actually show the extra option this
            # task now has. Prefer whichever of the item's verbs the
            # building DOESN'T already offer, so this step visibly adds
            # something new rather than (validly, but confusingly)
            # repeating the building's own first verb.
            building_verbs = building.goose_actions if building else []
            item_verb = next((v for v in item.goose_actions if v not in building_verbs), item.goose_actions[0])
            fallback_lines.append(f"* Goose: {item_verb} {item.name}.")
        else:
            fallback_lines.append(
                f"* Goose: {legal_verbs[min(1, len(legal_verbs) - 1)]} "
                f"{building.interactive_feature if building else 'the nearest object'}."
            )
        fallback_lines.append(f"* Goose: carries it toward {task.target_resident}.")
        fallback_lines.append(f"* Objective resolves: {task.description}")

        plan_text = self.llm.generate(
            system=(
                "You write a short stage-direction-only action plan (no dialogue, ever) using "
                f"ONLY these registered goose actions: {legal_verbs} -- never an action outside "
                "this list -- that indirectly solves the given community-building task."
            ),
            prompt=(
                f"Task: {task.description}\nBuilding: {building}\n"
                f"Item riding along: {item.name if item else 'none'}\nRegistered actions: {legal_verbs}"
            ),
            fallback="\n".join(fallback_lines),
        )
        lines = plan_text.split("\n") if plan_text else fallback_lines
        self._log(f"approved task #{task.task_id}; planned verb sequence ({len(lines)} lines)")
        return VerbPlan(task_id=task.task_id, lines=lines)
