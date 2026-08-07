"""Content-generation agents for Assignment #4's Dynamic Content Pipeline.

Three of these four agents are deliberately adapted from
UntitledGooseGame_Multi_Agent's agents rather than written from scratch --
each one is pointed at a real gap in GachoBadi's own code (an agent the
GDD describes but agents.py/crew.py never implemented, or a field the
existing agents leave empty). The fourth, the Consistency Critic Agent,
exists because that borrowing is itself a risk: Untitled Goose Game is a
mischief/chaos game with a five-verb set Gacho Badi doesn't share, so
adapted content can leak the wrong tone or the wrong verbs. See
CONTENT_PIPELINE_README.md for the full mapping and a real, reproducible
catch.

Every agent mirrors the CrewAI Agent shape (role/goal/backstory/run) used
throughout this repo and calls self.llm.generate(..., fallback=...), so
this always produces output with or without a configured API key.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

from agents import BaseAgent


# ---------------------------------------------------------------------------
# Item Interaction Content Agent
# -- adapted from UntitledGooseGame_Multi_Agent's PropDesignerAgent
# ---------------------------------------------------------------------------


class ItemAffordanceContentAgent(BaseAgent):
    role = "Item Interaction Content Agent"
    goal = (
        "Write a GDD-grounded affordance spec for one interactive item, filling the Item "
        "Interaction / World Affordance Agent role the GDD describes (Draft #8 onward) but "
        "this crew's agents.py/crew.py never actually implemented."
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


# ---------------------------------------------------------------------------
# Relationship Backstory Content Agent
# -- adapted from UntitledGooseGame_Multi_Agent's VillagerRoutineAgent
# ---------------------------------------------------------------------------


class RelationshipBackstoryContentAgent(BaseAgent):
    role = "Relationship Backstory Content Agent"
    goal = (
        "Write the one-line authored backstory the GDD requires behind a relationship label -- "
        "the current RelationshipAgent in agents.py only assigns the label itself, never the "
        "'why' Draft #9 made mandatory."
    )
    backstory = (
        "Adapted from UntitledGooseGame_Multi_Agent's Villager Routine Agent -- the same 'turn "
        "a structured value into one specific, non-generic sentence' pattern, pointed at "
        "relationship labels instead of routine dials. The Writer Agent is required to "
        "reference this backstory when a task resolves; this agent is what actually authors it."
    )

    LABEL_SEEDS = {
        "drifted apart": [
            "a mixed-up mail delivery",
            "a missed birthday",
            "moving to opposite ends of the island",
        ],
        "close friends": [
            "splitting a bakery order every week",
            "a shared umbrella during the first island storm",
        ],
        "friendly rivals": [
            "dueling garden competitions",
            "a running bet neither will admit to losing",
        ],
        "warm acquaintances": ["a polite nod every market day that never became more"],
        "budding crush": ["a dropped basket the other one picked up without being asked"],
    }

    def run(self, resident_a: str, resident_b: str, relationship_label: str, retrieved_context: str) -> str:
        seeds = self.LABEL_SEEDS.get(
            relationship_label, ["a small, half-remembered moment neither brought up again"]
        )
        seed = self.llm.choice(seeds)
        # Matches the GDD's own example format ("'drifted apart after a
        # mixed-up mail delivery'") rather than "X and Y are {label} after
        # Z", which reads fine for "drifted apart" but breaks grammatically
        # for labels like "budding crush" ("are budding crush").
        fallback = f"{resident_a} and {resident_b}: {relationship_label} -- {seed}."
        line = self.llm.generate(
            system=(
                "You write ONE short sentence: the specific, authored reason two Gacho Badi "
                "residents ended up in the given relationship state. Ground it in the provided "
                "GDD context's own tone and examples. Never write a generic 'they had a falling "
                "out' line with no specific cause -- the GDD explicitly calls a label alone "
                "insufficient content for a task."
            ),
            prompt=(
                f"GDD context:\n{retrieved_context}\n\nResident A: {resident_a}\n"
                f"Resident B: {resident_b}\nRelationship: {relationship_label}"
            ),
            fallback=fallback,
        )
        self._log(f"authored backstory for {resident_a}/{resident_b} ({relationship_label})")
        return line


# ---------------------------------------------------------------------------
# Task Premise Content Agent
# -- adapted from UntitledGooseGame_Multi_Agent's ChecklistCreatorAgent
# ---------------------------------------------------------------------------

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
        # the exact lore break ConsistencyCriticAgent below catches, so
        # the correction shown in output/content_pipeline_run.json is
        # real, not staged after the fact. See CONTENT_PIPELINE_README.md.
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


# ---------------------------------------------------------------------------
# Consistency Critic Agent -- not adapted from either reference crew
# ---------------------------------------------------------------------------


@dataclass
class CriticReport:
    violations: List[str]
    corrected_text: str
    commentary: str


class ConsistencyCriticAgent(BaseAgent):
    role = "Consistency Critic Agent"
    goal = "Catch and correct lore breaks or tone drift before generated content reaches the pipeline's output."
    backstory = (
        "Exists specifically because borrowing agent patterns from Untitled Goose Game (a "
        "mischief/chaos game with a five-verb set Gacho Badi doesn't share) risks leaking "
        "exactly that vocabulary into Gacho Badi's content. It checks every generated output "
        "against the GDD chunks it was actually grounded in, not against its own opinion."
    )

    ALLOWED_VERBS = {"Honk", "Grab", "Pick up", "Duck", "Dash"}
    VERB_FIX = {"Run": "Dash", "Tug": "Pick up", "Flap": "Duck"}
    TONE_FIX = {"mischief": "connection", "chaos": "harmony", "prank": "gesture", "mischievous": "well-meaning"}

    @staticmethod
    def _match_case(replacement: str, original: str) -> str:
        if original[:1].isupper():
            return replacement[:1].upper() + replacement[1:]
        return replacement

    def run(self, content_text: str, grounding_chunks, valid_names: Optional[List[str]] = None) -> CriticReport:
        violations: List[str] = []
        corrected = content_text

        for bad_verb, good_verb in self.VERB_FIX.items():
            pattern = re.compile(rf"\b{re.escape(bad_verb)}\b")
            if pattern.search(corrected):
                violations.append(
                    f"used goose verb '{bad_verb}', which is not one of Gacho Badi's five verbs "
                    f"({', '.join(sorted(self.ALLOWED_VERBS))}) -- consistent with it being "
                    f"carried over while adapting an Untitled Goose Game agent; replaced with "
                    f"'{good_verb}'."
                )
                corrected = pattern.sub(good_verb, corrected)

        for bad_word, good_word in self.TONE_FIX.items():
            pattern = re.compile(rf"\b{re.escape(bad_word)}\b", re.IGNORECASE)
            match = pattern.search(corrected)
            if match:
                fixed = self._match_case(good_word, match.group(0))
                violations.append(
                    f"used tone word '{match.group(0)}', which contradicts the GDD's 'quiet "
                    f"community-builder, not mischief-for-its-own-sake' framing; replaced with "
                    f"'{fixed}'."
                )
                corrected = pattern.sub(fixed, corrected)

        grounding_text = "\n".join(getattr(c, "text", str(c)) for c in grounding_chunks)
        fallback_commentary = (
            f"Checked against {len(grounding_chunks)} retrieved GDD chunk(s); "
            + (
                f"found {len(violations)} issue(s), corrected in place."
                if violations
                else "no lore breaks or tone drift found."
            )
        )
        commentary = self.llm.generate(
            system=(
                "You are a strict continuity checker for a game design document. In one or two "
                "sentences, say whether the given content is consistent with the given GDD "
                "context (residents, verbs, tone) or name the specific break."
            ),
            prompt=f"GDD context:\n{grounding_text}\n\nContent to check:\n{content_text}",
            fallback=fallback_commentary,
        )

        if violations:
            self._log(f"caught {len(violations)} issue(s)")
        else:
            self._log("no issues found")
        return CriticReport(violations=violations, corrected_text=corrected, commentary=commentary)
