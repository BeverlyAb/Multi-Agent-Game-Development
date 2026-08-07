"""Item Interaction Content Agent -- adapted from
UntitledGooseGame_Multi_Agent's PropDesignerAgent.
"""
from __future__ import annotations

from agents.base import BaseAgent


class ItemAffordanceContentAgent(BaseAgent):
    role = "Item Interaction Content Agent"
    goal = (
        "Write a GDD-grounded affordance spec for one interactive item, filling the Item "
        "Interaction / World Affordance Agent role the GDD describes (Draft #8 onward) but "
        "this crew's agents/ package never actually implemented."
    )
    backstory = (
        "Adapted from UntitledGooseGame_Multi_Agent's Prop Designer Agent -- UGG's props are "
        "defined entirely by what the goose can do to them, which is exactly the gap Gacho "
        "Badi's GDD assigns to an Item Interaction Agent that GachoBadi/Readme.md's own caveat "
        "admits was never coded. This agent fills it, grounded in the GDD's own 'How items "
        "participate in tasks' section instead of writing item text cold."
    )

    ITEM_DEFAULTS = {
        "memento": (
            "identifies an owner and a shared-memory association; the goose can grab/carry/"
            "drop/hide it; residents can notice/retrieve/discuss it; it drifts back to its "
            "owner or origin building if left obscure outside of active use."
        ),
        "hose": (
            "the goose can grab the nozzle, drag, activate, and release it; it wets targets "
            "and moves loose objects; residents react with irritation, laughter, avoidance, "
            "or investigation depending on personality."
        ),
        "mailbox": (
            "holds mail the goose can grab/carry/drop/hide; residents can notice/retrieve/"
            "discuss its contents; contents drift back to the mailbox if left elsewhere."
        ),
    }

    def run(self, item_name: str, item_kind: str, retrieved_context: str) -> str:
        default_afford = self.ITEM_DEFAULTS.get(
            item_kind,
            "the goose can grab/carry/drop/hide it; residents can notice/retrieve/discuss it; "
            "it drifts back to its owner or origin if left obscure.",
        )
        fallback = (
            f"{item_name} ({item_kind}): {default_afford} No task-critical item can become "
            "permanently unrecoverable, per the GDD's Item Interaction Agent guarantee."
        )
        spec = self.llm.generate(
            system=(
                "You write a one-paragraph item affordance spec for Gacho Badi's Item "
                "Interaction / World Affordance Agent, grounded ONLY in the provided GDD "
                "context: goose actions, resident reactions, state changes, and the "
                "no-permanent-loss reset rule. Never invent an affordance the context doesn't "
                "support."
            ),
            prompt=f"GDD context:\n{retrieved_context}\n\nItem: {item_name} ({item_kind})",
            fallback=fallback,
        )
        self._log(f"drafted affordance spec for {item_name}")
        return spec
