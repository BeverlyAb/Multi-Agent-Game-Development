"""Shared data structures passed between agents (the crew's 'blackboard')."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Sliders:
    """Player-tuned inputs described in the GDD's Character Personality Agent."""

    movement: int  # 0 (slow) - 100 (fast)
    speech: int  # 0 (reserved) - 100 (candid)
    energy: int  # 0 (flat) - 100 (excited)
    intelligence: int  # 0 (dull) - 100 (astute)


@dataclass
class Resident:
    name: str
    role: str  # e.g. baker, teacher, gym instructor
    sliders: Sliders
    traits: List[str] = field(default_factory=list)
    personality_summary: str = ""
    appearance: str = ""
    relationships: Dict[str, str] = field(default_factory=dict)  # set by RelationshipAgent: other resident -> label
    # set by RelationshipAgent alongside the label above: other resident -> the
    # one-line authored "why" the GDD requires ("a label alone is never
    # sufficient content for a task"). WriterAgent must reference this, not
    # just the label, when a task involving that pair resolves.
    relationship_backstories: Dict[str, str] = field(default_factory=dict)


@dataclass
class Item:
    """A movable prop (e.g. a memento) -- distinct from a Building's fixed
    interactive_feature, but enriched by the same Item Interaction Agent
    and consumed the same way by the Goose Solution Planner."""

    name: str
    kind: str  # e.g. memento, tool
    affordance: str = ""  # enriched description, set by ItemInteractionAgent
    goose_actions: List[str] = field(default_factory=list)  # e.g. grab, carry, drop, hide
    reset_rule: str = ""  # the no-permanent-loss guarantee's mechanism
    designed: bool = False  # set by ItemInteractionAgent; required by GooseSolutionPlanner


@dataclass
class Building:
    name: str
    kind: str  # e.g. bakery, mailbox, garden
    interactive_feature: str  # e.g. "hose that can spout water"
    location: str = ""  # set by IslandLayoutAgent; required by TaskCreator/Writer/Director
    designed: bool = False  # set by BuildingDesignerAgent; required by TaskCreator/Writer
    # set by ItemInteractionAgent: the goose actions this building's own
    # interactive_feature actually supports (e.g. a gate: open/close). Kept
    # separate from `designed` because BuildingDesignerAgent (dev-time,
    # visual/authored) and ItemInteractionAgent (runtime, gameplay-legal
    # actions) own different halves of "what can happen at this building."
    goose_actions: List[str] = field(default_factory=list)


@dataclass
class Task:
    task_id: int
    set_id: int
    description: str
    target_resident: str
    other_resident: Optional[str]  # the resident on the other side of the relationship, if any
    involves_building: Optional[str]
    # An explicit, checkable condition ("resident A and resident B are both
    # present at the same building with a positive reaction flag set"),
    # not just a text description -- see gdd.txt's "How a task is confirmed
    # complete." DirectorAgent checks this to decide resolved vs. still-open;
    # it is never used to decide anything by itself, only reported alongside
    # the decision so the check is inspectable.
    goal_state: str = ""
    status: str = "open"  # open | resolved | retired
    retire_reason: str = ""  # set only when status == "retired"


@dataclass
class Screenplay:
    task_id: int
    lines: List[str]  # screenplay-style dialogue + directional cues


@dataclass
class VerbPlan:
    task_id: int
    lines: List[str]  # goose-verb-only stage directions (honk/grab/pick up/duck/dash) -- no dialogue, ever


@dataclass
class StagedAction:
    actor: str
    action: str
    location: str


@dataclass
class NewsBulletin:
    task_id: int
    headline: str
