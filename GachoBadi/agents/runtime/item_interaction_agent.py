from __future__ import annotations

from typing import List

from agents.base import BaseAgent
from definitions.models import Building, Item


class ItemInteractionAgent(BaseAgent):
    role = "Item Interaction / World Affordance Agent"
    goal = (
        "Own the authoritative gameplay schema for every interactive item and building feature, "
        "so the Goose Solution Planner never has to invent an object behavior that isn't real."
    )
    backstory = (
        "The GDD (Draft #8 onward) makes this a Planner-Critical Runtime Agent -- gdd.txt's own "
        "'How items participate in tasks' section. It loads a compact affordance graph at initialization "
        "(Buildings' interactive_feature hints, plus standalone movable Items like a memento), "
        "which the Goose Solution Planner then treats as the only legal action set. Per Draft "
        "#11, that graph now also records what a RESIDENT (not just the goose) can do with the "
        "object once it's in front of them, and what further effect that resident's own action "
        "can cause -- the Chain Reaction Agent is the only consumer of those two fields, the "
        "same hard boundary the Goose Solution Planner already holds for goose_actions."
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
            Also sets .resident_actions / .chain_effect, consumed only by
            ChainReactionAgent (see that agent's docstring) -- an empty
            resident_actions list is common and not an error, since most
            affordances have no resident follow-up at all.
    """

    # goose_actions per building.kind: what the goose can legally do with
    # this building's own interactive_feature. Mirrors the GDD's own
    # examples (a gate that opens/closes, a hose that sprays water, a
    # mailbox that holds mail) rather than inventing new ones.
    BUILDING_ACTIONS = {
        "shop": ["Grab", "Drop"],
        "structure": ["Honk", "Duck"],
        "prop": ["Grab", "Dash"],
    }
    DEFAULT_BUILDING_ACTIONS = ["Honk"]

    # resident_actions per building.kind: what the TARGET resident can then
    # do themselves with whatever the goose just dropped or triggered.
    # Deliberately sparse -- only "prop"-kind buildings (like a garden hose
    # stand) get a chain_effect at all, matching gdd.txt's "most tasks are
    # non-sequential" framing rather than chaining every single task.
    BUILDING_RESIDENT_ACTIONS = {
        "shop": ["restock or tidy up with it"],
        "structure": ["settle it back into their own routine"],
        "prop": ["pick it up and put it to use themselves"],
    }
    DEFAULT_BUILDING_RESIDENT_ACTIONS = ["notice it and react in character"]
    BUILDING_CHAIN_EFFECTS = {
        "prop": "the visible result of using it draws a second resident over to see what's going on",
    }

    ITEM_ACTIONS = {
        "memento": ["Grab", "Drop"],
        "garden tool": ["Grab", "Dash"],
    }
    DEFAULT_ITEM_ACTIONS = ["Grab"]

    ITEM_RESIDENT_ACTIONS = {
        "memento": ["hold onto it and remember who it belonged to"],
        "garden tool": ["put it to use in the garden themselves"],
    }
    DEFAULT_ITEM_RESIDENT_ACTIONS = ["pick it up and react in character"]
    ITEM_CHAIN_EFFECTS = {
        "garden tool": "the visible result of using it draws a second resident over to see what's going on",
    }

    def run_building(self, building: Building) -> str:
        if not building.designed:
            raise ValueError(
                f"ItemInteractionAgent requires '{building.name}' to be designed "
                "-- run BuildingDesignerAgent first (dev-time authors the feature; "
                "this agent owns its runtime legal actions)."
            )
        actions = self.BUILDING_ACTIONS.get(building.kind, self.DEFAULT_BUILDING_ACTIONS)
        resident_actions = self.BUILDING_RESIDENT_ACTIONS.get(building.kind, self.DEFAULT_BUILDING_RESIDENT_ACTIONS)
        chain_effect = self.BUILDING_CHAIN_EFFECTS.get(building.kind, "")
        fallback = (
            f"{building.name} ({building.interactive_feature}): the goose can "
            f"{'/'.join(a.lower() for a in actions)} it; a resident who then finds or receives "
            f"it can {resident_actions[0]}"
            + (f", and {chain_effect}" if chain_effect else "")
            + ". Residents notice and react according to their personality. No task-critical "
            "state here can become permanently unrecoverable -- it resets to a safe default "
            "if left alone."
        )
        spec = self.llm.generate(
            system=(
                "You write a one-paragraph affordance spec for a building's interactive "
                "feature: which goose actions are legal, what a resident can then do with it "
                "themselves, and whether that resident's own action can draw in a second "
                "resident. Never invent an action outside the given lists."
            ),
            prompt=(
                f"Building: {building.name} ({building.interactive_feature})\n"
                f"Legal goose actions: {actions}\nLegal resident actions: {resident_actions}\n"
                f"Chain effect if any: {chain_effect or '(none)'}"
            ),
            fallback=fallback,
        )
        building.goose_actions = actions
        building.resident_actions = resident_actions
        building.chain_effect = chain_effect
        self._log(
            f"registered affordance for building {building.name} -> goose:{actions} "
            f"resident:{resident_actions}" + (f" chain:{chain_effect}" if chain_effect else "")
        )
        return spec

    def run_item(self, item: Item) -> str:
        actions = self.ITEM_ACTIONS.get(item.kind, self.DEFAULT_ITEM_ACTIONS)
        resident_actions = self.ITEM_RESIDENT_ACTIONS.get(item.kind, self.DEFAULT_ITEM_RESIDENT_ACTIONS)
        chain_effect = self.ITEM_CHAIN_EFFECTS.get(item.kind, "")
        reset_rule = (
            f"if dropped or hidden outside of active use, {item.name} drifts back to its "
            "owner or origin after a short time -- it can never become permanently lost."
        )
        fallback = (
            f"{item.name} ({item.kind}): the goose can {'/'.join(a.lower() for a in actions)} "
            f"it; a resident who receives it can {resident_actions[0]}"
            + (f", and {chain_effect}" if chain_effect else "")
            + f". {reset_rule}"
        )
        spec = self.llm.generate(
            system=(
                "You write a one-paragraph item affordance spec: which goose actions are "
                "legal, what a resident can then do with it themselves, whether that can draw "
                "in a second resident, and the no-permanent-loss reset rule. Never invent an "
                "action outside the given lists."
            ),
            prompt=(
                f"Item: {item.name} ({item.kind})\nLegal goose actions: {actions}\n"
                f"Legal resident actions: {resident_actions}\nChain effect if any: {chain_effect or '(none)'}"
            ),
            fallback=fallback,
        )
        item.affordance = spec
        item.goose_actions = actions
        item.resident_actions = resident_actions
        item.chain_effect = chain_effect
        item.reset_rule = reset_rule
        item.designed = True
        self._log(
            f"registered affordance for item {item.name} -> goose:{actions} resident:{resident_actions}"
            + (f" chain:{chain_effect}" if chain_effect else "")
        )
        return spec

    def run(self, buildings: List[Building], items: List[Item]) -> dict:
        building_specs = [self.run_building(b) for b in buildings]
        item_specs = [self.run_item(i) for i in items]
        return {"building_specs": building_specs, "item_specs": item_specs}
