from __future__ import annotations

from typing import List

from agents.base import BaseAgent
from definitions.models import Building, Item, VerbOutcome


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
        "#11, that graph now also records the range of ways a RESIDENT (not just the goose) can "
        "follow up once the object is in front of them, and whatever further effect each of "
        "those can cause -- the Chain Reaction Agent is the only consumer of that field, the "
        "same hard boundary the Goose Solution Planner already holds for goose_actions, and it "
        "picks which one actually happens at random, since not even a legal, well-planned goose "
        "action fully determines how a resident reacts to it."
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
            Also sets .possible_outcomes (a short list of VerbOutcome),
            consumed only by ChainReactionAgent, which randomly picks one
            per task (see that agent's docstring) -- an empty list is
            common and not an error, since most affordances have no
            resident follow-up at all.
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

    # possible_outcomes per building.kind: the range of ways the TARGET
    # resident might follow up on whatever the goose just dropped or
    # triggered -- ChainReactionAgent picks one at random per task, not
    # this agent, since this agent only registers what's *possible*, never
    # what *happens*. Deliberately sparse -- only "prop"-kind buildings
    # (like a garden hose stand) ever get an outcome with a chain_effect,
    # matching gdd.txt's "most tasks are non-sequential" framing rather
    # than chaining every single task.
    BUILDING_POSSIBLE_OUTCOMES = {
        "shop": [
            VerbOutcome("restocks the shelf themselves, pleased someone bothered", ""),
            VerbOutcome("tidies up without much thought and moves on", ""),
        ],
        "structure": [
            VerbOutcome("comes over to see what the fuss was about", ""),
            VerbOutcome("settles it back into their own routine, barely breaking stride", ""),
        ],
        "prop": [
            VerbOutcome(
                "picks it up and puts it to careful, deliberate use",
                "the calm result draws a second resident over to see what's going on",
            ),
            VerbOutcome("just resets it where it belongs with a shrug", ""),
        ],
    }
    DEFAULT_BUILDING_POSSIBLE_OUTCOMES = [VerbOutcome("notices it and reacts in character", "")]

    ITEM_ACTIONS = {
        "memento": ["Grab", "Drop"],
        "garden tool": ["Grab", "Dash"],
    }
    DEFAULT_ITEM_ACTIONS = ["Grab"]

    ITEM_POSSIBLE_OUTCOMES = {
        "memento": [
            VerbOutcome(
                "recognizes it immediately and can't help showing someone else",
                "recognizing it draws a second resident over to see it too",
            ),
            VerbOutcome("holds onto it quietly and remembers who it belonged to", ""),
        ],
        "garden tool": [
            VerbOutcome(
                "puts it to use in the garden themselves",
                "the visible result of using it draws a second resident over to see what's going on",
            ),
            VerbOutcome("sets it aside for later without using it", ""),
        ],
    }
    DEFAULT_ITEM_POSSIBLE_OUTCOMES = [VerbOutcome("picks it up and reacts in character", "")]

    def run_building(self, building: Building) -> str:
        if not building.designed:
            raise ValueError(
                f"ItemInteractionAgent requires '{building.name}' to be designed "
                "-- run BuildingDesignerAgent first (dev-time authors the feature; "
                "this agent owns its runtime legal actions)."
            )
        actions = self.BUILDING_ACTIONS.get(building.kind, self.DEFAULT_BUILDING_ACTIONS)
        outcomes = self.BUILDING_POSSIBLE_OUTCOMES.get(building.kind, self.DEFAULT_BUILDING_POSSIBLE_OUTCOMES)
        outcome_desc = "; or ".join(
            o.resident_action + (f" ({o.chain_effect})" if o.chain_effect else "") for o in outcomes
        )
        fallback = (
            f"{building.name} ({building.interactive_feature}): the goose can "
            f"{'/'.join(a.lower() for a in actions)} it; a resident who then finds or receives "
            f"it might {outcome_desc} -- exactly which one happens can vary. Residents notice "
            "and react according to their personality. No task-critical state here can become "
            "permanently unrecoverable -- it resets to a safe default if left alone."
        )
        spec = self.llm.generate(
            system=(
                "You write a one-paragraph affordance spec for a building's interactive "
                "feature: which goose actions are legal, and the range of ways a resident "
                "might then follow up themselves (not a single guaranteed reaction). Never "
                "invent an action or outcome outside the given lists."
            ),
            prompt=(
                f"Building: {building.name} ({building.interactive_feature})\n"
                f"Legal goose actions: {actions}\nPossible resident outcomes: {outcomes}"
            ),
            fallback=fallback,
        )
        building.goose_actions = actions
        building.possible_outcomes = outcomes
        self._log(
            f"registered affordance for building {building.name} -> goose:{actions} "
            f"{len(outcomes)} possible outcome(s)"
        )
        return spec

    def run_item(self, item: Item) -> str:
        actions = self.ITEM_ACTIONS.get(item.kind, self.DEFAULT_ITEM_ACTIONS)
        outcomes = self.ITEM_POSSIBLE_OUTCOMES.get(item.kind, self.DEFAULT_ITEM_POSSIBLE_OUTCOMES)
        outcome_desc = "; or ".join(
            o.resident_action + (f" ({o.chain_effect})" if o.chain_effect else "") for o in outcomes
        )
        reset_rule = (
            f"if dropped or hidden outside of active use, {item.name} drifts back to its "
            "owner or origin after a short time -- it can never become permanently lost."
        )
        fallback = (
            f"{item.name} ({item.kind}): the goose can {'/'.join(a.lower() for a in actions)} "
            f"it; a resident who receives it might {outcome_desc} -- exactly which one happens "
            f"can vary. {reset_rule}"
        )
        spec = self.llm.generate(
            system=(
                "You write a one-paragraph item affordance spec: which goose actions are "
                "legal, the range of ways a resident might then follow up themselves (not a "
                "single guaranteed reaction), and the no-permanent-loss reset rule. Never "
                "invent an action or outcome outside the given lists."
            ),
            prompt=(
                f"Item: {item.name} ({item.kind})\nLegal goose actions: {actions}\n"
                f"Possible resident outcomes: {outcomes}"
            ),
            fallback=fallback,
        )
        item.affordance = spec
        item.goose_actions = actions
        item.possible_outcomes = outcomes
        item.reset_rule = reset_rule
        item.designed = True
        self._log(
            f"registered affordance for item {item.name} -> goose:{actions} "
            f"{len(outcomes)} possible outcome(s)"
        )
        return spec

    def run(self, buildings: List[Building], items: List[Item]) -> dict:
        building_specs = [self.run_building(b) for b in buildings]
        item_specs = [self.run_item(i) for i in items]
        return {"building_specs": building_specs, "item_specs": item_specs}
