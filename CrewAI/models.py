"""Shared data structures passed between agents (the crew's 'blackboard')."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class BattleDials:
    """Encounter-designer-tuned inputs read by the Monster Personality Agent."""

    aggression: int  # 0 (won't fight back) - 100 (attacks relentlessly)
    playfulness: int  # 0 (dead serious) - 100 (constant bits/jokes)
    sympathy: int  # 0 (merciless) - 100 (visibly doesn't want to hurt you)
    chattiness: int  # 0 (silent) - 100 (talks through the whole fight)


@dataclass
class Monster:
    name: str
    role: str  # e.g. royal guard, skeleton sentry, ghost, flower
    dials: BattleDials
    traits: List[str] = field(default_factory=list)
    battle_style_summary: str = ""
    act_options: List[str] = field(default_factory=list)  # e.g. ["Check", "Flirt", "Threaten"]


@dataclass
class Room:
    name: str
    kind: str  # e.g. puzzle room, sentry station, battle arena
    feature: str  # e.g. "conveyor-belt puzzle that reverses on a switch"
    location: str = ""  # set by AreaLayoutAgent; required by BulletPatternDesigner/DialogueWriter/BattleDirector


@dataclass
class Attack:
    attack_id: int
    description: str  # the bullet-pattern flavor text
    performed_by: str  # monster name
    takes_place_in: Optional[str]  # room name
    status: str = "open"  # open | resolved


@dataclass
class BattleScript:
    attack_id: int
    lines: List[str]  # turn-based dialogue + directional cues (FIGHT/ACT/ITEM/MERCY box text)


@dataclass
class TurnAction:
    actor: str
    action: str
    location: str
