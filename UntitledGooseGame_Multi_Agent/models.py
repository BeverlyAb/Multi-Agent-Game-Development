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
    status: str = "open"  # open | done | retired
    # Set by ChecklistCreatorAgent; looked up in agents.OBJECTIVE_KINDS to get
    # this item's required prop kind, goose-verb template, and completion
    # mechanic+params. Empty only if the item predates this field.
    objective_kind: str = ""
    # Set by GooseVerbPlannerAgent when it retires an item instead of planning
    # it -- e.g. target_villager/involves_prop no longer exist in this cast,
    # or the resolved prop's kind can't satisfy this item's objective_kind.
    # Empty for "open"/"done" items.
    retire_reason: str = ""


@dataclass
class CompletionCondition:
    """A structured, checkable win condition for a ChecklistItem's VerbPlan.

    Both the crew (for its own verification) and the web client (for actual
    gameplay) read `mechanic`+`params` to decide when an item is done,
    instead of the web client hardcoding one rule for every item.
    """

    mechanic: str  # "deliver_to_villager" | "move_away_from_origin" | "lure_into_hazard"
    prop: str
    target_villager: str
    params: dict = field(default_factory=dict)


@dataclass
class VerbPlan:
    item_id: int
    lines: List[str]  # goose-verb stage directions ONLY -- no dialogue, ever
    steps: List[dict] = field(default_factory=list)  # structured [{"verb": ..., "target": ...}, ...]
    completion: Optional[CompletionCondition] = None
    # Set by GooseVerbPlannerAgent: True once the plan's objective_kind/prop
    # kind compatibility and required world data have been confirmed. This
    # asserts internal consistency, not that the objective is fun or
    # reachable in every possible world -- see verification_note.
    verified: bool = False
    verification_note: str = ""


@dataclass
class StagedGag:
    actor: str
    action: str
    location: str
