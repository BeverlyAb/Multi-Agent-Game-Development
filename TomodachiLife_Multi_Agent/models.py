"""Shared data structures passed between agents (the crew's 'blackboard')."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PersonalityDials:
    """Creation-quiz-tuned inputs read by the Mii Personality Agent."""

    expressiveness: int  # 0 (reserved) - 100 (flamboyant)
    diligence: int  # 0 (laid-back) - 100 (driven)
    confidence: int  # 0 (shy) - 100 (bold)
    mischief: int  # 0 (sweet) - 100 (devious)


@dataclass
class Mii:
    name: str
    role: str  # e.g. aspiring chef, poet, gym rat
    dials: PersonalityDials
    traits: List[str] = field(default_factory=list)
    personality_summary: str = ""
    voice_pattern: str = ""  # set by MiiVoiceAgent
    appearance: str = ""  # set by MiiAppearanceAgent
    relationships: Dict[str, str] = field(default_factory=dict)  # set by RelationshipAgent: other Mii name -> label


@dataclass
class Apartment:
    name: str
    kind: str  # e.g. cafe, clothes shop, photo studio, apartment block
    feature: str  # e.g. "jukebox that plays a Mii's own song"
    location: str = ""  # set by IslandLayoutAgent; required by EventCreator/SkitWriter/Director
    designed: bool = False  # set by ApartmentDesignerAgent; required by EventCreator/SkitWriter


@dataclass
class Event:
    event_id: int
    description: str  # the drama/skit premise
    involves_mii: str
    other_mii: Optional[str]  # the Mii on the other side of the relationship, if any
    takes_place_in: Optional[str]
    status: str = "open"  # open | resolved


@dataclass
class Skit:
    event_id: int
    lines: List[str]  # thought-bubble dialogue + stage directions


@dataclass
class StagedMoment:
    actor: str
    action: str
    location: str


@dataclass
class NewsBulletin:
    event_id: int
    headline: str
