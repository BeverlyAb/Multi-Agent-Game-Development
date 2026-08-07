"""Task Premise Content Agent -- adapted from
UntitledGooseGame_Multi_Agent's ChecklistCreatorAgent.
"""
from __future__ import annotations

from agents.base import BaseAgent

CONNECTION_KINDS = {
    "reconnect_drifted": {
        "template": "Get {resident} to reconnect with {other}, who they've drifted apart from, near the {building}.",
        "verbs": ["Grab", "Dash"],
        "reaction": "notices the returned memento and softens toward {other}",
    },
    "welcome_isolated": {
        "template": "Nudge {resident} to notice {other} sitting alone near the {building} and invite them over.",
        "verbs": ["Honk", "Grab"],
        "reaction": "looks over, hesitates, then waves {other} closer",
    },
    "mend_fallout": {
        # Adapted from UntitledGooseGame_Multi_Agent's ChecklistCreatorAgent
        # OBJECTIVE_KINDS table ("distract_and_swap") without updating the
        # verb list for Gacho Badi's five verbs (Honk/Grab/Pick up/Duck/
        # Dash) -- "Run" isn't one of them. Left in on purpose: this is
        # the exact lore break ConsistencyCriticAgent catches, so the
        # correction shown in output/content_pipeline_run.json is real,
        # not staged after the fact. See Readme.md.
        "template": "Help {resident} and {other} patch up a disagreement at the {building}.",
        "verbs": ["Grab", "Run", "Honk"],
        "reaction": "startles, then laughs off the disagreement with {other}",
    },
    "nudge_romance": {
        "template": "Nudge {resident} toward romance with {other} through an indirect gesture at the {building}.",
        "verbs": ["Pick up", "Duck"],
        "reaction": "blushes and lingers near {other} a little longer than usual",
    },
}


class TaskPremiseContentAgent(BaseAgent):
    role = "Task Premise Content Agent"
    goal = (
        "Author one pre-authored task premise from the GDD's fixed connection-task catalog, "
        "grounded in retrieved GDD context."
    )
    backstory = (
        "Adapted from UntitledGooseGame_Multi_Agent's Checklist Creator Agent -- same "
        "objective-kind lookup-table pattern (a relationship kind maps to a template, a verb "
        "sequence, and a reaction), rebuilt around Gacho Badi's connection framing instead of "
        "UGG's mischief framing. Draft #10 of the GDD states the ~30-40 task premises are "
        "pre-authored content the runtime Task Creator Agent only selects from -- this agent is "
        "what actually authors one."
    )

    def run(
        self,
        resident: str,
        other: str,
        relationship_label: str,
        building: str,
        connection_kind: str,
        retrieved_context: str,
    ) -> str:
        spec = CONNECTION_KINDS.get(connection_kind)
        if spec is None:
            raise ValueError(f"Unknown connection_kind: {connection_kind!r}")
        fallback_lines = [
            spec["template"].format(resident=resident, other=other, building=building),
            *[f"Goose: {verb} near the {building}." for verb in spec["verbs"]],
            # `other` is the one reacting, so the {other} placeholder in the
            # reaction template must resolve to `resident` -- otherwise the
            # line reads as e.g. "Otto: ... toward Otto" instead of Hazel.
            f"{other}: {spec['reaction'].format(other=resident)}",
        ]
        fallback = "\n".join(fallback_lines)
        text = self.llm.generate(
            system=(
                "You write one short, open-ended Gacho Badi task premise (connection, never "
                "mischief) that nudges two residents together, plus a goose-verb-only stage "
                "plan using ONLY Honk/Grab/Pick up/Duck/Dash -- no dialogue, ever -- grounded in "
                "the provided GDD context."
            ),
            prompt=(
                f"GDD context:\n{retrieved_context}\n\nResident: {resident}\nOther: {other}\n"
                f"Relationship: {relationship_label}\nBuilding: {building}\n"
                f"Connection kind: {connection_kind}"
            ),
            fallback=fallback,
        )
        self._log(f"drafted task premise ({connection_kind}) for {resident}/{other}")
        return text
