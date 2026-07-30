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


@dataclass
class Building:
    name: str
    kind: str  # e.g. bakery, mailbox, garden
    interactive_feature: str  # e.g. "hose that can spout water"
    location: str = ""  # set by IslandLayoutAgent; required by TaskCreator/Writer/Director
    designed: bool = False  # set by BuildingDesignerAgent; required by TaskCreator/Writer


@dataclass
class Task:
    task_id: int
    description: str
    target_resident: str
    other_resident: Optional[str]  # the resident on the other side of the relationship, if any
    involves_building: Optional[str]
    status: str = "open"  # open | completed


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
