"""Eight agents built around Untitled Goose Game's own defining systems:
villager routines (not personalities-with-dialogue -- UGG villagers never
speak), prop affordances, village layout, the checklist of mischief
objectives, and a goose-verb planner that solves each objective using
only the game's five verbs (Honk, Grab, Run, Tug, Flap) instead of
writing any dialogue at all.

This is deliberately NOT a re-skin of Gacho Badi's 8-agent GDD template,
nor of this repo's other crews. Untitled Goose Game has no spoken lines,
no personality-slider system, and no orchestrator-spawned appearance
agent in the GDD's sense -- its identity is entirely physical comedy and
indirect object manipulation, so the agent roles here are built around
that instead of forcing the game into a borrowed shape. The
pipeline-with-hard-dependencies engineering pattern is shared with every
crew in this repo; the *roles* are not.

Each class mirrors the CrewAI Agent shape (role / goal / backstory / run)
without depending on the crewai package, so this runs anywhere Python 3
runs. Every agent calls self.llm.generate(..., fallback=...) -- when no
API key is configured (the default), the deterministic fallback is what
executes, so the crew always produces output.
"""
from __future__ import annotations

from typing import List, Optional

from llm_client import LLMClient
from models import ChecklistItem, Prop, RoutineDials, StagedGag, VerbPlan, Villager


class BaseAgent:
    role: str = "Agent"
    goal: str = ""
    backstory: str = ""

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def _log(self, message: str) -> None:
        print(f"  [{self.role}] {message}")


# ---------------------------------------------------------------------------
# Mischief-loop agents (run every time the goose starts a new objective)
# ---------------------------------------------------------------------------


class VillagerRoutineAgent(BaseAgent):
    role = "Villager Routine Agent"
    goal = "Turn a villager's tuned routine dials into a coherent behavior loop."
    backstory = (
        "Untitled Goose Game never gives a villager a personality through dialogue -- there is "
        "no dialogue. It's told entirely through a repeating routine (sweep, water the flowers, "
        "shoo the goose) that the player learns to read and disrupt. This agent is what makes "
        "that routine specific to who the villager is, instead of a generic patrol loop."
    )

    DIAL_TABLE = {
        "territorialness": {"low": "barely notices what's missing", "high": "guards their things like a hawk"},
        "obliviousness": {"low": "sharp-eyed and hard to fool", "high": "easily tricked by the obvious"},
        "fussiness": {"low": "unbothered by chaos", "high": "rattled by the smallest thing out of place"},
        "patience": {"low": "snaps the instant something's wrong", "high": "slow to notice a pattern"},
    }

    def _bucket(self, value: int) -> str:
        return "high" if value >= 50 else "low"

    def run(self, name: str, role_title: str, dials: RoutineDials) -> Villager:
        traits = [
            self.DIAL_TABLE["territorialness"][self._bucket(dials.territorialness)],
            self.DIAL_TABLE["obliviousness"][self._bucket(dials.obliviousness)],
            self.DIAL_TABLE["fussiness"][self._bucket(dials.fussiness)],
            self.DIAL_TABLE["patience"][self._bucket(dials.patience)],
        ]
        fallback = (
            f"{name}, the {role_title}, {', '.join(traits)}. "
            f"(territorialness/obliviousness/fussiness/patience: "
            f"{dials.territorialness}/{dials.obliviousness}/{dials.fussiness}/{dials.patience})"
        )
        summary = self.llm.generate(
            system="You describe, in one sentence, the repeating daily routine of an Untitled-Goose-Game-style villager, based on dial values. No dialogue -- describe only actions.",
            prompt=f"Name: {name}\nRole: {role_title}\nDials: {dials}\nTraits: {traits}",
            fallback=fallback,
        )
        self._log(f"built routine for {name} -> {traits}")
        return Villager(name=name, role=role_title, dials=dials, traits=traits, routine_summary=summary)


class ChecklistCreatorAgent(BaseAgent):
    role = "Checklist Creator Agent"
    goal = "Generate the area's open-ended checklist of mischief objectives from the villagers and props available."
    backstory = (
        "One of this crew's two 'One Wow' agents: Untitled Goose Game's whole structure is the "
        "checklist -- a list of objectives that only make sense given which villager guards "
        "which prop where. A generic checklist item breaks the puzzle-comedy premise for the "
        "whole area."
    )

    """
    Input:  villagers enriched by VillagerRoutineAgent (need .traits),
            props enriched by AreaLayoutAgent (need .location) and
            PropDesignerAgent (need .designed).
    Output: List[ChecklistItem] consumed by GooseVerbPlannerAgent.
    Removing VillagerRoutineAgent, AreaLayoutAgent, or PropDesignerAgent
    breaks this agent outright (raises ValueError below) rather than
    degrading silently.
    """

    TEMPLATES = [
        "Get {villager} to drop {prop} without noticing.",
        "Make {villager} lock themselves out near {location} using {prop}.",
        "Steal {prop} from right under {villager}'s nose at {location}.",
        "Get {villager} to chase you into {prop}'s reach at {location}.",
        "Make {villager} put on {prop} by mistake.",
    ]

    def run(self, villagers: List[Villager], props: List[Prop]) -> List[ChecklistItem]:
        items: List[ChecklistItem] = []
        if not villagers or not props:
            self._log("no villagers/props yet -> no checklist available")
            return items
        for villager in villagers:
            if not villager.traits:
                raise ValueError(
                    f"ChecklistCreatorAgent requires '{villager.name}' to carry routine traits "
                    "-- run VillagerRoutineAgent first."
                )
        for prop in props:
            if not prop.location:
                raise ValueError(
                    f"ChecklistCreatorAgent requires '{prop.name}' to have an assigned location "
                    "-- run AreaLayoutAgent first."
                )
            if not prop.designed:
                raise ValueError(
                    f"ChecklistCreatorAgent requires '{prop.name}' to be designed "
                    "-- run PropDesignerAgent first."
                )
        for i, villager in enumerate(villagers):
            prop = props[i % len(props)]
            template = self.TEMPLATES[i % len(self.TEMPLATES)]
            fallback = template.format(villager=villager.name, prop=prop.name, location=prop.location)
            description = self.llm.generate(
                system="You invent one short, open-ended, indirect physical-comedy checklist objective for an Untitled-Goose-Game-style area. No dialogue -- describe only the objective.",
                prompt=(
                    f"Villager: {villager.name} ({villager.role}, traits: {villager.traits})\n"
                    f"Prop: {prop.name} at {prop.location} ({prop.affordance})"
                ),
                fallback=fallback,
            )
            items.append(
                ChecklistItem(
                    item_id=i + 1,
                    description=description,
                    target_villager=villager.name,
                    involves_prop=prop.name,
                )
            )
        self._log(f"generated {len(items)} checklist item(s)")
        return items


class GooseVerbPlannerAgent(BaseAgent):
    role = "Goose Verb Planner Agent"
    goal = "Plan the sequence of goose verbs (Honk, Grab, Run, Tug, Flap) that indirectly solves a checklist item."
    backstory = (
        "Untitled Goose Game has no dialogue and no cutscenes -- everything is solved through "
        "five verbs and object physics. This agent replaces the 'Writer Agent' slot other crews "
        "in this repo have, because writing dialogue here would be inauthentic; what the game "
        "actually needs is a plan of physical actions. It is also this crew's Goose Solution "
        "Planner: the Checklist Creator does not certify solvability, so no item may reach the "
        "player until this agent proves a goose-only solution actually exists against the "
        "current cast and world model -- it never invents a villager or prop that isn't there."
    )

    """
    Input:  a ChecklistItem from ChecklistCreatorAgent, plus the villager
            enriched by VillagerDesignerAgent (needs .appearance) and the
            prop enriched by AreaLayoutAgent (needs .location) and
            PropDesignerAgent (needs .designed).
    Output: a VerbPlan consumed by ReactionDirectorAgent, or None if no
            solution is reachable -- e.g. the item's target_villager or
            involves_prop no longer names anything in the current cast.
            An unreachable item is the caller's (Crew's) job to retire, the
            same way an unavailable resident/building/item is handled in
            the GDD: re-plan or retire the task outright, never leave the
            player stuck chasing something that isn't there.
    """

    VERBS = ["Honk", "Grab", "Run", "Tug", "Flap"]

    def run(self, item: ChecklistItem, villagers: List[Villager], props: List[Prop]) -> Optional[VerbPlan]:
        villager = next((v for v in villagers if v.name == item.target_villager), None)
        prop = next((p for p in props if p.name == item.involves_prop), None) if item.involves_prop else None

        if villager is None:
            self._log(
                f"item #{item.item_id} UNREACHABLE -- no villager named '{item.target_villager}' "
                "in the current cast"
            )
            return None
        if item.involves_prop and prop is None:
            self._log(
                f"item #{item.item_id} UNREACHABLE -- no prop named '{item.involves_prop}' "
                "in the current world model"
            )
            return None

        if not villager.appearance:
            raise ValueError(
                f"GooseVerbPlannerAgent requires '{villager.name}' to have a designed appearance "
                "-- run VillagerDesignerAgent first."
            )
        if prop is not None and not prop.location:
            raise ValueError(
                f"GooseVerbPlannerAgent requires '{prop.name}' to have an assigned location "
                "-- run AreaLayoutAgent first."
            )
        if prop is not None and not prop.designed:
            raise ValueError(
                f"GooseVerbPlannerAgent requires '{prop.name}' to be designed "
                "-- run PropDesignerAgent first."
            )
        fallback_lines = [
            f"* SCENE: {prop.location if prop else 'the village'}.",
            f"* ({villager.name} is {villager.appearance}.)",
            f"* Goose: {self.VERBS[0]} near {prop.name if prop else 'the nearest object'}.",
            f"* Goose: {self.VERBS[1]} {prop.name if prop else 'the object'}.",
            f"* Objective resolves: {item.description}",
        ]
        plan_text = self.llm.generate(
            system=(
                "You write a short stage-direction-only action plan (no dialogue, ever) using "
                "only these goose verbs: Honk, Grab, Run, Tug, Flap, for an "
                "Untitled-Goose-Game-style checklist item."
            ),
            prompt=f"Checklist item: {item.description}\nVillager: {villager}\nProp: {prop}",
            fallback="\n".join(fallback_lines),
        )
        lines = plan_text.split("\n") if plan_text else fallback_lines
        self._log(f"planned verb sequence for item #{item.item_id} ({len(lines)} lines)")
        return VerbPlan(item_id=item.item_id, lines=lines)


class ReactionDirectorAgent(BaseAgent):
    role = "Reaction Director Agent"
    goal = "Take the Goose Verb Planner's plan and stage it as the villager reaction and object physics the player actually sees."
    backstory = "This crew's other 'One Wow' agent: converts a verb plan into the live physical-comedy beat -- prop state change, villager reaction, goose animation -- that is the actual gameplay."

    """
    Input:  the VerbPlan from GooseVerbPlannerAgent, the active
            ChecklistItem, and props enriched by AreaLayoutAgent (needs
            .location, used as the physical staging location instead of
            just the prop's name).
    Output: List[StagedGag] -- the actual gameplay behavior; this is the
            crew's terminal, player-visible output.
    """

    def run(self, plan: VerbPlan, item: ChecklistItem, props: List[Prop]) -> List[StagedGag]:
        if not plan.lines:
            raise ValueError(
                f"ReactionDirectorAgent has nothing to stage for item #{item.item_id} "
                "-- GooseVerbPlannerAgent returned an empty plan."
            )
        prop = next((p for p in props if p.name == item.involves_prop), None)
        location = prop.location if prop and prop.location else (item.involves_prop or "the village")
        staged = [
            StagedGag(actor="Goose", action=f"execute plan: {item.description}", location=location),
            StagedGag(actor=item.target_villager, action="notice, react, and give chase or give up", location=location),
        ]
        self._log(f"staged {len(staged)} gag(s) for item #{item.item_id} at {location}")
        return staged


# ---------------------------------------------------------------------------
# Prep-time agents (spun up by the Area Orchestrator)
# ---------------------------------------------------------------------------


class VillagerDesignerAgent(BaseAgent):
    role = "Villager Designer Agent"
    goal = "Design a villager's outfit and tell-tale carried prop from their routine."
    backstory = "Untitled Goose Game's villagers are instantly readable from their silhouette alone -- the gardener's hat, the boy's overalls. A villager with no designed look is just a hitbox."

    """
    Input:  a Villager already enriched by VillagerRoutineAgent (needs
            .traits).
    Output: an appearance/loadout spec, written into villager.appearance
            so GooseVerbPlannerAgent can require and use it downstream.
    """

    def run(self, villager: Villager) -> str:
        if not villager.traits:
            raise ValueError(
                f"VillagerDesignerAgent requires '{villager.name}' to carry routine traits "
                "-- run VillagerRoutineAgent first."
            )
        fallback = (
            f"{villager.name}: a {villager.role} whose {', '.join(villager.traits)} shows in their "
            "outfit and the one prop they're never without."
        )
        spec = self.llm.generate(
            system="You write a one-paragraph villager outfit/loadout spec for an Untitled-Goose-Game-style character, based on its traits. No dialogue.",
            prompt=f"Villager: {villager}",
            fallback=fallback,
        )
        villager.appearance = spec
        self._log(f"designed loadout for {villager.name}")
        return spec


class PropDesignerAgent(BaseAgent):
    role = "Prop Designer Agent"
    goal = "Design a prop and the physical affordance that makes it useful to the goose."
    backstory = "Every object in Untitled Goose Game is defined by what the goose can do to it -- the Prop Designer is what keeps props from being inert scenery."

    """
    Input:  a Prop with a raw .affordance hint.
    Output: an enriched affordance spec, written back into
            prop.affordance, plus prop.designed = True so every
            downstream agent (Checklist Creator, Goose Verb Planner) can
            require and confirm a designed prop, not just the raw seed
            text.
    """

    def run(self, prop: Prop) -> str:
        fallback = f"{prop.name} ({prop.kind}): affords {prop.affordance}."
        spec = self.llm.generate(
            system="You write a one-paragraph prop design spec, emphasizing the physical affordance a goose could exploit.",
            prompt=f"Prop: {prop}",
            fallback=fallback,
        )
        prop.affordance = spec
        prop.designed = True
        self._log(f"designed prop {prop.name}")
        return spec


class AreaLayoutAgent(BaseAgent):
    role = "Area Layout Agent"
    goal = "Place props around the village's named areas."
    backstory = "Untitled Goose Game's pacing depends on which area a prop sits in -- the same rake reads differently in the Garden than propped against the Pub."

    """
    Input:  the list of Props in this mischief set.
    Output: a village-layout narrative, and each prop is mutated in place
            with a .location, which ChecklistCreator, GooseVerbPlanner,
            and ReactionDirector all require.
    """

    ZONES = ["Garden", "High Street", "Back Gardens", "Pub", "Market", "Manor"]

    def run(self, props: List[Prop]) -> str:
        if not props:
            self._log("no props yet -> nothing to lay out")
            return "(no props yet)"
        for i, prop in enumerate(props):
            prop.location = self.ZONES[i % len(self.ZONES)]
        names = ", ".join(f"{p.name} ({p.location})" for p in props)
        fallback = f"Layout: {names}, spread across the village."
        spec = self.llm.generate(
            system="You write a short village-layout description placing the given props in their assigned areas.",
            prompt=f"Props and areas: {[(p.name, p.location) for p in props]}",
            fallback=fallback,
        )
        self._log(f"assigned locations: {[(p.name, p.location) for p in props]}")
        return spec


class AreaOrchestrator(BaseAgent):
    role = "Area Orchestrator"
    goal = "Spin up the right prep-time agent for a designer's content request and return its output."
    backstory = "Prompted by the designer with the area content they expect; dispatches to a sub-agent and reports back."

    def __init__(self, llm: LLMClient):
        super().__init__(llm)
        self.villager_agent = VillagerDesignerAgent(llm)
        self.prop_agent = PropDesignerAgent(llm)
        self.layout_agent = AreaLayoutAgent(llm)

    def run(self, request_kind: str, payload):
        self._log(f"dispatching '{request_kind}' request")
        if request_kind == "villager":
            return self.villager_agent.run(payload)
        if request_kind == "prop":
            return self.prop_agent.run(payload)
        if request_kind == "layout":
            return self.layout_agent.run(payload)
        raise ValueError(f"Unknown area request kind: {request_kind}")
