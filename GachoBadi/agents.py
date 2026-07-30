"""The eleven agents defined in gdd.txt's 'AI Architecture' section
(Draft #2). The original 8-agent list didn't track how residents felt
about each other, and didn't guarantee a task was actually solvable with
the goose's own moves -- Relationship Agent, Goose Solution Planner
Agent, and Newscaster Agent close those two gaps, borrowed respectively
from this repo's Tomodachi Life and Untitled Goose Game reference crews.

Each class mirrors the CrewAI Agent shape (role / goal / backstory / run)
without depending on the crewai package, so this runs anywhere Python 3
runs. Every agent calls self.llm.generate(..., fallback=...) -- when no
API key is configured (the default), the deterministic fallback is what
executes, so the crew always produces output.
"""
from __future__ import annotations

from typing import List

from llm_client import LLMClient
from models import (
    Building,
    NewsBulletin,
    Resident,
    Screenplay,
    Sliders,
    StagedAction,
    Task,
    VerbPlan,
)


class BaseAgent:
    role: str = "Agent"
    goal: str = ""
    backstory: str = ""

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def _log(self, message: str) -> None:
        print(f"  [{self.role}] {message}")


# ---------------------------------------------------------------------------
# Runtime loop agents
# ---------------------------------------------------------------------------


class CharacterPersonalityAgent(BaseAgent):
    role = "Character Personality Agent"
    goal = "Turn a resident's tuned sliders into a coherent personality profile."
    backstory = "Reads player-set movement/speech/energy/intelligence sliders and names the personality that falls out of them."

    TRAIT_TABLE = {
        "movement": {"low": "sedentary", "high": "energetic"},
        "speech": {"low": "reserved", "high": "candid"},
        "energy": {"low": "flat", "high": "excitable"},
        "intelligence": {"low": "dull", "high": "astute"},
    }

    def _bucket(self, value: int) -> str:
        return "high" if value >= 50 else "low"

    def run(self, name: str, role_title: str, sliders: Sliders) -> Resident:
        traits = [
            self.TRAIT_TABLE["movement"][self._bucket(sliders.movement)],
            self.TRAIT_TABLE["speech"][self._bucket(sliders.speech)],
            self.TRAIT_TABLE["energy"][self._bucket(sliders.energy)],
            self.TRAIT_TABLE["intelligence"][self._bucket(sliders.intelligence)],
        ]
        fallback = (
            f"{name} the {role_title} comes across as {', '.join(traits)}. "
            f"({sliders.movement}/{sliders.speech}/{sliders.energy}/{sliders.intelligence} "
            f"movement/speech/energy/intelligence)"
        )
        summary = self.llm.generate(
            system="You write a one-sentence personality summary for a life-sim resident from slider values.",
            prompt=f"Name: {name}\nRole: {role_title}\nSliders: {sliders}\nTraits: {traits}",
            fallback=fallback,
        )
        self._log(f"built personality for {name} -> {traits}")
        return Resident(name=name, role=role_title, sliders=sliders, traits=traits, personality_summary=summary)


class RelationshipAgent(BaseAgent):
    role = "Relationship Agent"
    goal = "Work out how every pair of residents on the island feels about each other."
    backstory = (
        "Borrowed from the Tomodachi Life reference crew: the original 8-agent GDD had no way "
        "to make a task like 'these two used to be close' mean anything. This agent is what "
        "turns the island's new community-building premise into something the Task Creator can "
        "actually generate tasks from."
    )

    """
    Input:  residents already enriched by CharacterPersonalityAgent
            (need .traits).
    Output: resident.relationships populated in place on every resident
            (other resident name -> relationship label), required by
            TaskCreatorAgent whenever there's more than one resident.
    """

    def _label(self, a: Resident, b: Resident) -> str:
        a_candid = "candid" in a.traits
        b_candid = "candid" in b.traits
        a_energetic = "energetic" in a.traits
        b_energetic = "energetic" in b.traits
        a_excitable = "excitable" in a.traits
        b_excitable = "excitable" in b.traits
        if a_energetic and b_energetic:
            return "friendly rivals"
        if a_excitable and b_excitable:
            return "close friends"
        if a_candid != b_candid:
            return "drifted apart"
        return "warm acquaintances"

    def run(self, residents: List[Resident]) -> List[Resident]:
        for resident in residents:
            if not resident.traits:
                raise ValueError(
                    f"RelationshipAgent requires '{resident.name}' to carry personality traits "
                    "-- run CharacterPersonalityAgent first."
                )
        if len(residents) < 2:
            self._log("fewer than 2 residents -> no relationships to compute")
            return residents
        for i, resident in enumerate(residents):
            other = residents[(i + 1) % len(residents)]
            fallback = self._label(resident, other)
            label = self.llm.generate(
                system="You name, in 2-4 words, the relationship between two life-sim residents based on their personality traits.",
                prompt=f"Resident A: {resident.name} ({resident.traits})\nResident B: {other.name} ({other.traits})",
                fallback=fallback,
            )
            resident.relationships[other.name] = label
        self._log(f"mapped relationships: {[(r.name, r.relationships) for r in residents]}")
        return residents


class TaskCreatorAgent(BaseAgent):
    role = "Task Creator Agent"
    goal = "Generate an open-ended task list from the residents and buildings currently on the island."
    backstory = (
        "One of the GDD's two 'One Wow' agents: batch-generates the tasks that gate island "
        "expansion. Draft #2 of the GDD reframed these tasks around community-building rather "
        "than mischief for its own sake, so this agent now reads relationships, not just traits."
    )

    """
    Input:  residents enriched by CharacterPersonalityAgent (need .traits)
            and, when there's more than one resident, RelationshipAgent
            (need .relationships); buildings enriched by IslandLayoutAgent
            (need .location) and BuildingDesignerAgent (need .designed).
    Output: List[Task] consumed by WriterAgent and GooseSolutionPlannerAgent.
    Removing CharacterPersonalityAgent, RelationshipAgent, IslandLayoutAgent,
    or BuildingDesignerAgent breaks this agent outright (raises ValueError
    below) rather than degrading silently, so the dependency is provable,
    not just cosmetic.
    """

    TEMPLATES = [
        "Get {resident} to reconnect with {other}, who they've drifted apart from, near the {building}.",
        "Help {resident} and {other} ({relationship}) patch up a disagreement at the {building}.",
        "Nudge {resident} to notice {other} sitting alone near the {building} and invite them over.",
        "Get {resident} to return something of {other}'s at the {building}, giving them a reason to talk.",
        "Bring {resident} and {other} together at the {building} despite being {relationship}.",
    ]

    def run(self, residents: List[Resident], buildings: List[Building]) -> List[Task]:
        tasks: List[Task] = []
        if not residents or not buildings:
            self._log("no residents/buildings yet -> no tasks available")
            return tasks
        for resident in residents:
            if not resident.traits:
                raise ValueError(
                    f"TaskCreatorAgent requires '{resident.name}' to carry personality traits "
                    "-- run CharacterPersonalityAgent first."
                )
        if len(residents) > 1:
            for resident in residents:
                if not resident.relationships:
                    raise ValueError(
                        f"TaskCreatorAgent requires '{resident.name}' to have mapped relationships "
                        "-- run RelationshipAgent first."
                    )
        for building in buildings:
            if not building.location:
                raise ValueError(
                    f"TaskCreatorAgent requires '{building.name}' to have an assigned location "
                    "-- run IslandLayoutAgent first."
                )
            if not building.designed:
                raise ValueError(
                    f"TaskCreatorAgent requires '{building.name}' to be designed "
                    "-- run BuildingDesignerAgent first."
                )
        for i, resident in enumerate(residents):
            building = buildings[i % len(buildings)]
            other = residents[(i + 1) % len(residents)]
            relationship = resident.relationships.get(other.name, "acquaintances")
            template = self.TEMPLATES[i % len(self.TEMPLATES)]
            fallback = template.format(
                resident=resident.name, other=other.name, relationship=relationship, building=building.name,
            )
            description = self.llm.generate(
                system="You invent one short, open-ended task for a goose-sim game that nudges two residents toward connection -- friendship or community belonging as much as romance -- through an indirect, physical-comedy interaction.",
                prompt=(
                    f"Resident: {resident.name} ({resident.role}, traits: {resident.traits})\n"
                    f"Other resident: {other.name}, relationship: {relationship}\n"
                    f"Building: {building.name} at {building.location} ({building.interactive_feature})"
                ),
                fallback=fallback,
            )
            tasks.append(
                Task(
                    task_id=i + 1,
                    description=description,
                    target_resident=resident.name,
                    other_resident=other.name if other.name != resident.name else None,
                    involves_building=building.name,
                )
            )
        self._log(f"generated {len(tasks)} task(s)")
        return tasks


class WriterAgent(BaseAgent):
    role = "Writer Agent"
    goal = "Given a task and its actors (and their relationship to each other), write screenplay-style dialogue and action cues."
    backstory = "Produces the 'script' the Director later blocks into gameplay, now aware of how the two residents in a task actually feel about each other."

    """
    Input:  a Task from TaskCreatorAgent, plus the resident enriched by
            CharacterAppearanceAgent (needs .appearance) and the building
            enriched by IslandLayoutAgent (needs .location) and
            BuildingDesignerAgent (needs .designed).
    Output: Screenplay consumed by DirectorAgent.
    """

    def run(self, task: Task, residents: List[Resident], buildings: List[Building]) -> Screenplay:
        resident = next((r for r in residents if r.name == task.target_resident), None)
        other = next((r for r in residents if r.name == task.other_resident), None)
        building = next((b for b in buildings if b.name == task.involves_building), None)
        if resident is not None and not resident.appearance:
            raise ValueError(
                f"WriterAgent requires '{resident.name}' to have an appearance spec "
                "-- run CharacterAppearanceAgent first."
            )
        if building is not None and not building.location:
            raise ValueError(
                f"WriterAgent requires '{building.name}' to have an assigned location "
                "-- run IslandLayoutAgent first."
            )
        if building is not None and not building.designed:
            raise ValueError(
                f"WriterAgent requires '{building.name}' to be designed "
                "-- run BuildingDesignerAgent first."
            )
        relationship = resident.relationships.get(other.name, "acquaintances") if resident and other else "acquaintances"
        fallback_lines = [
            f"INT./EXT. {building.name.upper() if building else 'ISLAND'} - {building.location.upper() if building else 'DAY'}",
            f"({resident.name if resident else 'RESIDENT'} looks like: {resident.appearance if resident else 'a nearby resident'}.)",
            f"(They are {relationship} with {other.name if other else 'a neighbor'}.)",
            f"GOOSE: (honks meaningfully near the {building.name if building else 'nearest prop'})",
            f"{resident.name if resident else 'RESIDENT'}: (startled, then softening) \"Oh -- it's you.\"",
            f"(Task resolves: {task.description})",
        ]
        screenplay_text = self.llm.generate(
            system="You write a short screenplay scene (dialogue + directional cues) for a community-building goose-sim task, reflecting the relationship between the two residents involved.",
            prompt=f"Task: {task.description}\nActor: {resident}\nOther resident: {other.name if other else None} ({relationship})\nBuilding: {building}",
            fallback="\n".join(fallback_lines),
        )
        lines = screenplay_text.split("\n") if screenplay_text else fallback_lines
        self._log(f"wrote screenplay for task #{task.task_id} ({len(lines)} lines)")
        return Screenplay(task_id=task.task_id, lines=lines)


class GooseSolutionPlannerAgent(BaseAgent):
    role = "Goose Solution Planner Agent"
    goal = "Plan at least one valid indirect solution to a task using only the goose's own verbs -- never dialogue."
    backstory = (
        "Borrowed from the Untitled Goose Game reference crew's Goose Verb Planner Agent: the "
        "goose never speaks, so this agent guarantees every task the Task Creator invents is "
        "actually solvable with honk/grab/pick up/duck/dash before the player ever sees it, and "
        "doubles as the source for an in-game hint if the player gets stuck."
    )

    VERBS = ["Honk", "Grab", "Pick up", "Duck", "Dash"]

    """
    Input:  a Task from TaskCreatorAgent, plus the building enriched by
            IslandLayoutAgent (needs .location) and BuildingDesignerAgent
            (needs .designed).
    Output: VerbPlan consumed by DirectorAgent, alongside the Writer's
            Screenplay.
    """

    def run(self, task: Task, buildings: List[Building]) -> VerbPlan:
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
        fallback_lines = [
            f"* SCENE: {building.location if building else 'the island'}.",
            f"* Goose: {self.VERBS[0]} near {building.name if building else 'the nearest prop'}.",
            f"* Goose: {self.VERBS[1]} {building.interactive_feature if building else 'the nearest object'}.",
            f"* Goose: {self.VERBS[2]} it and carry it toward {task.target_resident}.",
            f"* Objective resolves: {task.description}",
        ]
        plan_text = self.llm.generate(
            system=(
                "You write a short stage-direction-only action plan (no dialogue, ever) using "
                "only these goose verbs: Honk, Grab, Pick up, Duck, Dash, that indirectly solves "
                "the given community-building task."
            ),
            prompt=f"Task: {task.description}\nBuilding: {building}",
            fallback="\n".join(fallback_lines),
        )
        lines = plan_text.split("\n") if plan_text else fallback_lines
        self._log(f"planned verb sequence for task #{task.task_id} ({len(lines)} lines)")
        return VerbPlan(task_id=task.task_id, lines=lines)


class DirectorAgent(BaseAgent):
    role = "Director Agent"
    goal = "Take the Writer's screenplay and the Goose Solution Planner's verb plan and stage both as the actions residents/goose actually perform."
    backstory = "The GDD's other 'One Wow' agent: converts script and verb plan into the active gameplay the player sees."

    """
    Input:  the Screenplay from WriterAgent, the VerbPlan from
            GooseSolutionPlannerAgent, the active Task, and buildings
            enriched by IslandLayoutAgent (needs .location, used as the
            physical staging location instead of just the building's name).
    Output: List[StagedAction] -- the actual gameplay behavior; this is
            the crew's terminal, player-visible output.
    """

    def run(
        self, screenplay: Screenplay, verb_plan: VerbPlan, task: Task, buildings: List[Building]
    ) -> List[StagedAction]:
        if not screenplay.lines:
            raise ValueError(
                f"DirectorAgent has nothing to stage for task #{task.task_id} "
                "-- WriterAgent returned an empty screenplay."
            )
        if not verb_plan.lines:
            raise ValueError(
                f"DirectorAgent has no goose actions to stage for task #{task.task_id} "
                "-- GooseSolutionPlannerAgent returned an empty verb plan."
            )
        building = next((b for b in buildings if b.name == task.involves_building), None)
        location = building.location if building and building.location else (task.involves_building or "island")
        staged = [
            StagedAction(actor="Goose", action=f"execute plan: {verb_plan.lines[0]}", location=location),
            StagedAction(
                actor=task.target_resident,
                action=f"react and progress toward: {task.description}",
                location=location,
            ),
        ]
        if task.other_resident:
            staged.append(
                StagedAction(actor=task.other_resident, action="notice, warm up, and reconnect", location=location)
            )
        self._log(f"staged {len(staged)} action(s) for task #{task.task_id} at {location}")
        return staged


class NewscasterAgent(BaseAgent):
    role = "Newscaster Agent"
    goal = "Recap a resolved task as a short island bulletin."
    backstory = (
        "Borrowed from the Tomodachi Life reference crew's Newscaster Agent: gives the island's "
        "new community-building premise a visible, recurring payoff -- the island literally "
        "buzzes with what the goose just did."
    )

    """
    Input:  the staged actions from DirectorAgent and the active Task.
    Output: a NewsBulletin -- this crew's second terminal, player-visible
            output (alongside the staged actions themselves).
    """

    def run(self, staged_actions: List[StagedAction], task: Task) -> NewsBulletin:
        if not staged_actions:
            raise ValueError(
                f"NewscasterAgent has nothing to report for task #{task.task_id} "
                "-- DirectorAgent returned no staged actions."
            )
        fallback = f"ISLAND BULLETIN: {task.description}"
        headline = self.llm.generate(
            system="You write one short, warm island-bulletin headline recapping this community-building task.",
            prompt=f"Task: {task.description}\nStaged actions: {staged_actions}",
            fallback=fallback,
        )
        self._log(f"filed news bulletin for task #{task.task_id}")
        return NewsBulletin(task_id=task.task_id, headline=headline)


# ---------------------------------------------------------------------------
# Development-time agents (spun up by the Scene Orchestrator)
# ---------------------------------------------------------------------------


class CharacterAppearanceAgent(BaseAgent):
    role = "Character Appearance Agent"
    goal = "Design a resident's visual appearance from their role and personality."

    """
    Input:  a Resident already enriched by CharacterPersonalityAgent
            (needs .traits).
    Output: an appearance spec, written into resident.appearance so
            WriterAgent can require and use it downstream.
    """

    def run(self, resident: Resident) -> str:
        if not resident.traits:
            raise ValueError(
                f"CharacterAppearanceAgent requires '{resident.name}' to carry personality traits "
                "-- run CharacterPersonalityAgent first."
            )
        fallback = (
            f"{resident.name}: a {resident.role} with a look reflecting "
            f"{', '.join(resident.traits)} -- palette and silhouette chosen to read at a glance."
        )
        spec = self.llm.generate(
            system="You write a one-paragraph appearance spec for a life-sim character.",
            prompt=f"Resident: {resident}",
            fallback=fallback,
        )
        resident.appearance = spec
        self._log(f"designed appearance for {resident.name}")
        return spec


class BuildingDesignerAgent(BaseAgent):
    role = "Building Designer Agent"
    goal = "Design a building and its interactive architecture."

    """
    Input:  a Building with a raw .interactive_feature hint.
    Output: an enriched design spec, written back into
            building.interactive_feature, plus building.designed = True
            so every downstream agent (Task Creator, Writer) can require
            and confirm a designed building, not just the raw seed text.
    """

    def run(self, building: Building) -> str:
        fallback = f"{building.name} ({building.kind}): features {building.interactive_feature}."
        spec = self.llm.generate(
            system="You write a one-paragraph building design spec, emphasizing the interactive feature.",
            prompt=f"Building: {building}",
            fallback=fallback,
        )
        building.interactive_feature = spec
        building.designed = True
        self._log(f"designed building {building.name}")
        return spec


class IslandLayoutAgent(BaseAgent):
    role = "Island Layout Agent"
    goal = "Arrange available buildings into a coherent island layout."

    """
    Input:  the list of Buildings on the island.
    Output: a layout narrative, and each building is mutated in place
            with a .location, which TaskCreatorAgent, WriterAgent, and
            DirectorAgent all require.
    """

    ZONES = ["north dock", "town square", "east meadow", "pond overlook", "west orchard", "south gate"]

    def run(self, buildings: List[Building]) -> str:
        if not buildings:
            self._log("no buildings yet -> nothing to lay out")
            return "(no buildings yet)"
        for i, building in enumerate(buildings):
            building.location = self.ZONES[i % len(self.ZONES)]
        names = ", ".join(f"{b.name} ({b.location})" for b in buildings)
        fallback = f"Layout: {names}, arranged in a loop around the goose's starting pond."
        spec = self.llm.generate(
            system="You write a short island layout description placing the given buildings at their assigned zones.",
            prompt=f"Buildings and zones: {[(b.name, b.location) for b in buildings]}",
            fallback=fallback,
        )
        self._log(f"assigned locations: {[(b.name, b.location) for b in buildings]}")
        return spec


class SceneOrchestratorAgent(BaseAgent):
    role = "Scene Orchestrator"
    goal = "Spin up the right dev-time agent for a programmer's scene request and return its output."
    backstory = "Prompted by the programmer with the scene they expect; dispatches to a sub-agent and reports back."

    def __init__(self, llm: LLMClient):
        super().__init__(llm)
        self.appearance_agent = CharacterAppearanceAgent(llm)
        self.building_agent = BuildingDesignerAgent(llm)
        self.layout_agent = IslandLayoutAgent(llm)

    def run(self, request_kind: str, payload) -> str:
        self._log(f"dispatching '{request_kind}' request")
        if request_kind == "appearance":
            return self.appearance_agent.run(payload)
        if request_kind == "building":
            return self.building_agent.run(payload)
        if request_kind == "layout":
            return self.layout_agent.run(payload)
        raise ValueError(f"Unknown scene request kind: {request_kind}")
