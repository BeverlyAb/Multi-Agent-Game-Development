"""Item Interaction Content Agent -- adapted from
UntitledGooseGame_Multi_Agent's PropDesignerAgent.
"""
from __future__ import annotations

from agents.base import BaseAgent


class ItemAffordanceContentAgent(BaseAgent):
    role = "Item Interaction Content Agent"
    goal = (
        "Write a GDD-grounded affordance spec for one interactive item, in the voice of the "
        "Item Interaction / World Affordance Agent role the GDD describes (Draft #8 onward)."
    )
    backstory = (
        "Adapted from UntitledGooseGame_Multi_Agent's Prop Designer Agent -- UGG's props are "
        "defined entirely by what the goose can do to them, which is exactly the gap Gacho "
        "Badi's GDD assigns to an Item Interaction Agent. At the time this pipeline was built, "
        "agents/runtime/ had no such agent at all; that gap has since been closed directly "
        "(agents/runtime/item_interaction_agent.py). This agent still serves a distinct "
        "purpose -- RAG-grounded, critic-checked content generation for Assignment #4 -- rather "
        "than owning the runtime crew's live affordance schema. Since Draft #11, that runtime "
        "schema also records what a RESIDENT (not just the goose) can do with an item once "
        "it's dropped in front of them, and what further chain_effect that can cause (see the "
        "Chain Reaction Agent); this content agent's own specs now describe that resident "
        "follow-up too, so the two stay in the same voice."
    )

    ITEM_DEFAULTS = {
        "memento": (
            "identifies an owner and a shared-memory association; the goose can grab/carry/"
            "drop/hide it; a resident who receives it can hold onto it and remember who it "
            "belonged to; residents can notice/retrieve/discuss it; it drifts back to its "
            "owner or origin building if left obscure outside of active use."
        ),
        "hose": (
            "the goose can grab the nozzle, drag, activate, and release it, or simply drop it "
            "in front of a resident; a resident who picks it up can water nearby plants with "
            "it themselves, and the garden coming back to life is what can draw a second "
            "resident over to admire it -- a short chain of cause and effect, not just the "
            "goose's own action landing directly; residents react with irritation, laughter, "
            "avoidance, or investigation depending on personality."
        ),
        "mailbox": (
            "holds mail the goose can grab/carry/drop/hide; a resident who receives a piece of "
            "mail can read it and act on whatever it says themselves; residents can notice/"
            "retrieve/discuss its contents; contents drift back to the mailbox if left "
            "elsewhere."
        ),
    }

    def run(self, item_name: str, item_kind: str, retrieved_context: str) -> str:
        default_afford = self.ITEM_DEFAULTS.get(
            item_kind,
            "the goose can grab/carry/drop/hide it; a resident who receives it can pick it up "
            "and put it to use themselves; residents can notice/retrieve/discuss it; it drifts "
            "back to its owner or origin if left obscure.",
        )
        fallback = (
            f"{item_name} ({item_kind}): {default_afford} No task-critical item can become "
            "permanently unrecoverable, per the GDD's Item Interaction Agent guarantee."
        )
        spec = self.llm.generate(
            system=(
                "You write a one-paragraph item affordance spec for Gacho Badi's Item "
                "Interaction / World Affordance Agent, grounded ONLY in the provided GDD "
                "context: goose actions, what a resident can then do with the item themselves, "
                "whether that resident's own use can chain into a second resident's reaction, "
                "and the no-permanent-loss reset rule. Never invent an affordance the context "
                "doesn't support."
            ),
            prompt=f"GDD context:\n{retrieved_context}\n\nItem: {item_name} ({item_kind})",
            fallback=fallback,
        )
        self._log(f"drafted affordance spec for {item_name}")
        return spec
