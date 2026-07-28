"""Shared data structures passed between agents (the crew's 'blackboard').

Deliberately has NO dialogue-shaped field anywhere -- Untitled Goose Game
has no spoken lines at all, only honks, physical comedy, and a checklist.
That absence is a design decision, not an oversight.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class RoutineDials:
    """Village-designer-tuned inputs read by the Villager Routine Agent."""

    territorialness: int  # 0 (doesn't notice things going missing) - 100 (guards everything)
    obliviousness: int  # 0 (sharp-eyed) - 100 (easily fooled)
    fussiness: int  # 0 (unbothered) - 100 (rattled by the smallest thing)
    patience: int  # 0 (snaps immediately) - 100 (very slow to notice a pattern)


@dataclass
class Villager:
    name: str  # e.g. "The Groundskeeper" -- UGG never gives villagers proper names
    role: str  # e.g. gardener, shopkeeper, groundskeeper, boy
    dials: RoutineDials
    traits: List[str] = field(default_factory=list)
    routine_summary: str = ""  # the repeating loop of actions this villager walks
    appearance: str = ""  # set by VillagerDesignerAgent: loadout/outfit + tell-tale prop


@dataclass
class Prop:
    name: str
    kind: str  # e.g. garden tool, clothing item, food item, key
    affordance: str  # e.g. "rake that flings mud when stepped on"
    location: str = ""  # set by AreaLayoutAgent; required by ChecklistCreator/GooseVerbPlanner/ReactionDirector
    designed: bool = False  # set by PropDesignerAgent; required by ChecklistCreator/GooseVerbPlanner


@dataclass
class ChecklistItem:
    item_id: int
    description: str  # the mischief objective, e.g. "Make the groundskeeper lock himself out"
    target_villager: str
    involves_prop: Optional[str]
    status: str = "open"  # open | ticked off


@dataclass
class VerbPlan:
    item_id: int
    lines: List[str]  # goose-verb stage directions ONLY -- no dialogue, ever


@dataclass
class StagedGag:
    actor: str
    action: str
    location: str
