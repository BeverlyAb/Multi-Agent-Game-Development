from __future__ import annotations

from typing import List

from agents.base import BaseAgent
from models import Building, Item


class ItemInteractionAgent(BaseAgent):
    role = "Item Interaction / World Affordance Agent"
    goal = (
        "Own the authoritative gameplay schema for every interactive item and building feature, "
        "so the Goose Solution Planner never has to invent an object behavior that isn't real."
    )
    backstory = (
        "The GDD (Draft #8 onward) makes this a Planner-Critical Runtime Agent -- gdd.txt's own "
        "'How items participate in tasks' section -- but it was never actually implemented in "
        "this crew's code, only in the separate Assignment #4 content pipeline "
        "(agents/dynamic_content/item_affordance_content_agent.py). This is that agent, wired "
        "into the actual runtime crew: it loads a compact affordance graph at initialization "
        "(Buildings' interactive_feature hints, plus standalone movable Items like a memento), "
        "which the Goose Solution Planner then treats as the only legal action set."
    )

    """
    Input:  Buildings (raw .interactive_feature hint) and Items (raw .kind
            hint).
    Output: enriched Building.goose_actions / Item.goose_actions +
            .affordance / .reset_rule, plus .designed = True on Items, so
            GooseSolutionPlannerAgent can require and confirm a registered
            affordance record instead of inventing one -- removing this
            agent makes every task unsolvable (see run_item_pass below),
            the same hard-dependency guarantee every other agent here has.
    """

    # goose_actions per building.kind: what the goose can legally do with
    # this building's own interactive_feature. Mirrors the GDD's own
    # examples (a gate that opens/closes, a hose that sprays water, a
    # mailbox that holds mail) rather than inventing new ones.
    BUILDING_ACTIONS = {
        "shop": ["Grab", "Pick up"],
        "structure": ["Honk", "Duck"],
        "prop": ["Grab", "Dash"],
    }
    DEFAULT_BUILDING_ACTIONS = ["Honk"]

    ITEM_ACTIONS = {
        "memento": ["Grab", "Pick up"],
        "garden tool": ["Grab", "Dash"],
    }
    DEFAULT_ITEM_ACTIONS = ["Grab"]

    def run_building(self, building: Building) -> str:
        if not building.designed:
            raise ValueError(
                f"ItemInteractionAgent requires '{building.name}' to be designed "
                "-- run BuildingDesignerAgent first (dev-time authors the feature; "
                "this agent owns its runtime legal actions)."
            )
        actions = self.BUILDING_ACTIONS.get(building.kind, self.DEFAULT_BUILDING_ACTIONS)
        fallback = (
            f"{building.name} ({building.interactive_feature}): the goose can "
            f"{'/'.join(a.lower() for a in actions)} it; residents notice and react "
            "according to their personality. No task-critical state here can become "
            "permanently unrecoverable -- it resets to a safe default if left alone."
        )
        spec = self.llm.generate(
            system=(
                "You write a one-paragraph affordance spec for a building's interactive "
                "feature: which goose actions are legal, and how residents react. Never "
                "invent an action outside the given list."
            ),
            prompt=f"Building: {building.name} ({building.interactive_feature})\nLegal actions: {actions}",
            fallback=fallback,
        )
        building.goose_actions = actions
        self._log(f"registered affordance for building {building.name} -> {actions}")
        return spec

    def run_item(self, item: Item) -> str:
        actions = self.ITEM_ACTIONS.get(item.kind, self.DEFAULT_ITEM_ACTIONS)
        reset_rule = (
            f"if dropped or hidden outside of active use, {item.name} drifts back to its "
            "owner or origin after a short time -- it can never become permanently lost."
        )
        fallback = (
            f"{item.name} ({item.kind}): the goose can {'/'.join(a.lower() for a in actions)} "
            f"it; residents can notice, retrieve, or discuss it. {reset_rule}"
        )
        spec = self.llm.generate(
            system=(
                "You write a one-paragraph item affordance spec: which goose actions are "
                "legal, how residents react, and the no-permanent-loss reset rule. Never "
                "invent an action outside the given list."
            ),
            prompt=f"Item: {item.name} ({item.kind})\nLegal actions: {actions}",
            fallback=fallback,
        )
        item.affordance = spec
        item.goose_actions = actions
        item.reset_rule = reset_rule
        item.designed = True
        self._log(f"registered affordance for item {item.name} -> {actions}")
        return spec

    def run(self, buildings: List[Building], items: List[Item]) -> dict:
        building_specs = [self.run_building(b) for b in buildings]
        item_specs = [self.run_item(i) for i in items]
        return {"building_specs": building_specs, "item_specs": item_specs}
