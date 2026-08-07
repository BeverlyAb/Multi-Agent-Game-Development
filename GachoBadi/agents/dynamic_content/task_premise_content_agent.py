"""Task Premise Content Agent -- adapted from
UntitledGooseGame_Multi_Agent's ChecklistCreatorAgent.
"""
from __future__ import annotations

from agents.base import BaseAgent

# Each step is (verb, target-template) rather than a single verb list
# applied to one shared "near the {building}" suffix -- the Consistency
# Critic Agent's redundant-step check exists specifically because that
# shared-suffix shape reads as a copy-paste of the same line with only
# the verb swapped (e.g. "Grab near the bakery." / "Honk near the
# bakery."). {item} is filled from the Item Interaction Content Agent's
# own output, not invented here -- that's the "available agents" this
# agent is meant to draw on instead of working from the building name
# alone. Reaction templates use {counterpart}, not {other}, because the
# line is spoken BY `other`, so a same-named placeholder would resolve to
# itself (see the self-reference bug this fixed in an earlier revision).
CONNECTION_KINDS = {
    "reconnect_drifted": {
        "template": "Get {resident} to reconnect with {other}, who they've drifted apart from, near the {building}.",
        "steps": [
            ("Grab", "{item}, still sitting exactly where {other} dropped it"),
            ("Dash", "it back across to {resident} before the moment passes"),
        ],
        "reaction": "turns {item} over once, recognizes it, and finally looks up at {counterpart}",
    },
    "welcome_isolated": {
        "template": "Nudge {resident} to notice {other} sitting alone near the {building} and invite them over.",
        "steps": [
            ("Honk", "twice at {other}, sitting alone by the {building}"),
            ("Grab", "the empty seat beside {other} before anyone else takes it"),
        ],
        "reaction": "startles, then shifts over to make room without being asked",
    },
    "mend_fallout": {
        # Adapted from UntitledGooseGame_Multi_Agent's ChecklistCreatorAgent
        # OBJECTIVE_KINDS table ("distract_and_swap") without updating the
        # verb list for Gacho Badi's five verbs (Honk/Grab/Pick up/Duck/
        # Dash) -- "Run" isn't one of them. Left in on purpose: this is
        # the exact lore break ConsistencyCriticAgent catches, so the
        # correction shown in Readme.md is real, not staged after the fact.
        "template": "Help {resident} and {other} patch up a disagreement at the {building}.",
        "steps": [
            ("Grab", "{item}, the same one {resident} and {other} argued over"),
            ("Run", "it straight between them before either one can walk off"),
            ("Honk", "until neither of them can keep pretending not to notice"),
        ],
        "reaction": "goes quiet, then laughs -- the argument was never really about {item}",
    },
    "nudge_romance": {
        "template": "Nudge {resident} toward romance with {other} through an indirect gesture at the {building}.",
        "steps": [
            ("Pick up", "{item}, the one {other} keeps meaning to return"),
            ("Duck", "behind the {building} to leave it right where {resident} will find it"),
        ],
        "reaction": "finds {item} waiting, glances toward {counterpart}, and can't quite hide the smile",
    },
}


class TaskPremiseContentAgent(BaseAgent):
    role = "Task Premise Content Agent"
    goal = (
        "Author one pre-authored task premise from the GDD's fixed connection-task catalog, "
        "grounded in retrieved GDD context and in a specific, in-world item -- not a generic "
        "'near the building' gesture repeated with a different verb each time."
    )
    backstory = (
        "Adapted from UntitledGooseGame_Multi_Agent's Checklist Creator Agent -- same "
        "objective-kind lookup-table pattern (a relationship kind maps to a template, a verb "
        "sequence, and a reaction), rebuilt around Gacho Badi's connection framing instead of "
        "UGG's mischief framing. Draft #10 of the GDD states the ~30-40 task premises are "
        "pre-authored content the runtime Task Creator Agent only selects from -- this agent is "
        "what actually authors one, now drawing on the Item Interaction Content Agent's own "
        "output for a concrete target instead of naming the same building three times."
    )

    def run(
        self,
        resident: str,
        other: str,
        relationship_label: str,
        building: str,
        connection_kind: str,
        retrieved_context: str,
        item_name: str = "a small kept memento",
    ) -> str:
        spec = CONNECTION_KINDS.get(connection_kind)
        if spec is None:
            raise ValueError(f"Unknown connection_kind: {connection_kind!r}")
        fmt = {"resident": resident, "other": other, "building": building, "item": item_name}
        reaction_fmt = {**fmt, "counterpart": resident}
        fallback_lines = [
            spec["template"].format(**fmt),
            *[f"Goose: {verb} {target.format(**fmt)}." for verb, target in spec["steps"]],
            f"{other}: {spec['reaction'].format(**reaction_fmt)}",
        ]
        fallback = "\n".join(fallback_lines)
        text = self.llm.generate(
            system=(
                "You write one short, open-ended Gacho Badi task premise (connection, never "
                "mischief) that nudges two residents together, plus a goose-verb-only stage "
                "plan using ONLY Honk/Grab/Pick up/Duck/Dash -- no dialogue, ever -- grounded in "
                "the provided GDD context. Center the plan on the given item -- every step must "
                "target something specific (the item, the other resident, a named detail of the "
                "building), never the same generic 'near the building' phrase repeated with only "
                "the verb changed. Write the reaction line with the same specificity: a concrete "
                "beat, not a generic 'they reconcile.'"
            ),
            prompt=(
                f"GDD context:\n{retrieved_context}\n\nResident: {resident}\nOther: {other}\n"
                f"Relationship: {relationship_label}\nBuilding: {building}\nItem: {item_name}\n"
                f"Connection kind: {connection_kind}"
            ),
            fallback=fallback,
        )
        self._log(f"drafted task premise ({connection_kind}) for {resident}/{other}")
        return text
