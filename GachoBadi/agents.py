"""The eight agents defined in gdd.txt's 'AI Architecture' section.

Each class mirrors the CrewAI Agent shape (role / goal / backstory / run)
without depending on the crewai package, so this runs anywhere Python 3
runs. Every agent calls self.llm.generate(..., fallback=...) -- when no
API key is configured (the default), the deterministic fallback is what
executes, so the crew always produces output.
"""
from __future__ import annotations

from typing import List, Optional

from llm_client import LLMClient
from models import Building, Resident, Screenplay, Sliders, StagedAction, Task


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


class TaskCreatorAgent(BaseAgent):
    role = "Task Creator Agent"
    goal = "Generate an open-ended task list from the residents and buildings currently on the island."
    backstory = "One of the GDD's two 'One Wow' agents: batch-generates the tasks that gate island expansion."

    """
    Input:  residents enriched by CharacterPersonalityAgent (need .traits),
            buildings enriched by IslandLayoutAgent (need .location).
    Output: List[Task] consumed by WriterAgent.
    Removing CharacterPersonalityAgent or IslandLayoutAgent breaks this
    agent outright (raises ValueError below) rather than degrading
    silently, so the dependency is provable, not just cosmetic.
    """

    TEMPLATES = [
        "Get {resident} to change their outfit before they notice.",
        "Make {resident} laugh using the {building}.",
        "Cause a mix-up between {resident} and the {building} that draws a crowd.",
        "Get {resident} to leave the {building} without saying goodbye.",
        "Use the {building} to interrupt {resident} mid-conversation.",
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
            template = self.TEMPLATES[i % len(self.TEMPLATES)]
            fallback = template.format(resident=resident.name, building=building.name)
            description = self.llm.generate(
                system="You invent one short, open-ended, indirect physical-comedy task for a goose-sim game.",
                prompt=(
                    f"Resident: {resident.name} ({resident.role}, traits: {resident.traits})\n"
                    f"Building: {building.name} at {building.location} ({building.interactive_feature})"
                ),
                fallback=fallback,
            )
            tasks.append(
                Task(
                    task_id=i + 1,
                    description=description,
                    target_resident=resident.name,
                    involves_building=building.name,
                )
            )
        self._log(f"generated {len(tasks)} task(s)")
        return tasks


class WriterAgent(BaseAgent):
    role = "Writer Agent"
    goal = "Given a task and its actors, write screenplay-style dialogue and action cues."
    backstory = "Produces the 'script' the Director later blocks into gameplay."

    """
    Input:  a Task from TaskCreatorAgent, plus the resident enriched by
            CharacterAppearanceAgent (needs .appearance) and the building
            enriched by IslandLayoutAgent (needs .location).
    Output: Screenplay consumed by DirectorAgent.
    """

    def run(self, task: Task, residents: List[Resident], buildings: List[Building]) -> Screenplay:
        resident = next((r for r in residents if r.name == task.target_resident), None)
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
        fallback_lines = [
            f"INT./EXT. {building.name.upper() if building else 'ISLAND'} - {building.location.upper() if building else 'DAY'}",
            f"({resident.name if resident else 'RESIDENT'} looks like: {resident.appearance if resident else 'a nearby resident'}.)",
            f"GOOSE: (honks meaningfully near the {building.name if building else 'nearest prop'})",
            f"{resident.name if resident else 'RESIDENT'}: (startled) \"What in the world--!\"",
            f"(Task resolves: {task.description})",
        ]
        screenplay_text = self.llm.generate(
            system="You write a short screenplay scene (dialogue + directional cues) for a Untitled-Goose-Game-style task.",
            prompt=f"Task: {task.description}\nActor: {resident}\nBuilding: {building}",
            fallback="\n".join(fallback_lines),
        )
        lines = screenplay_text.split("\n") if screenplay_text else fallback_lines
        self._log(f"wrote screenplay for task #{task.task_id} ({len(lines)} lines)")
        return Screenplay(task_id=task.task_id, lines=lines)


class DirectorAgent(BaseAgent):
    role = "Director Agent"
    goal = "Take the Writer's screenplay and stage it as the actions residents/goose actually perform."
    backstory = "The GDD's other 'One Wow' agent: converts script into the active gameplay the player sees."

    """
    Input:  the Screenplay from WriterAgent, the active Task, and buildings
            enriched by IslandLayoutAgent (needs .location, used as the
            physical staging location instead of just the building's name).
    Output: List[StagedAction] -- the actual gameplay behavior; this is
            the crew's terminal, player-visible output.
    """

    def run(self, screenplay: Screenplay, task: Task, buildings: List[Building]) -> List[StagedAction]:
        if not screenplay.lines:
            raise ValueError(
                f"DirectorAgent has nothing to stage for task #{task.task_id} "
                "-- WriterAgent returned an empty screenplay."
            )
        building = next((b for b in buildings if b.name == task.involves_building), None)
        location = building.location if building and building.location else (task.involves_building or "island")
        staged = [
            StagedAction(actor="Goose", action="approach and honk", location=location),
            StagedAction(
                actor=task.target_resident,
                action=f"react and progress toward: {task.description}",
                location=location,
            ),
        ]
        self._log(f"staged {len(staged)} action(s) for task #{task.task_id} at {location}")
        return staged


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
