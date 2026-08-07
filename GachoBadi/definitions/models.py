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
class VerbOutcome:
    """One possible way a resident's own follow-up on an object can go.
    Set by ItemInteractionAgent (a short list per Building/Item); which
    ONE of them actually happens for a given task is picked at random by
    ChainReactionAgent itself -- a real goose's exact motion in front of a
    resident isn't fully predictable even when the goose's own action was
    legal and planned, and this is where that variability lives, entirely
    downstream of (and untouched by) the Goose Solution Planner, which
    only ever proves *a* legal verb sequence exists."""

    resident_action: str  # what the target resident does with the object in this particular outcome
    chain_effect: str = ""  # further consequence, if any -- empty means this outcome never cascades to a second resident


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
    # set by ItemInteractionAgent, consumed only by ChainReactionAgent: the
    # possible ways a resident can follow up once the goose has dropped or
    # delivered this item -- ChainReactionAgent randomly picks ONE per task
    # (see VerbOutcome), so the same item can play out differently between
    # two tasks that both involve it. An empty list means this item has no
    # resident follow-up at all, which is common (most tasks are
    # non-sequential, per gdd.txt) and not an error.
    possible_outcomes: List[VerbOutcome] = field(default_factory=list)


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
    # See Item.possible_outcomes above -- same meaning, same
    # ChainReactionAgent-only consumer and random-pick behavior, just for a
    # building's fixed feature instead of a movable item (e.g. sometimes
    # the resident who finds the garden hose waters the garden with it,
    # drawing a second resident over to admire it; other times they just
    # coil it back up with no one else noticing -- same hose, same goose
    # action, different outcome).
    possible_outcomes: List[VerbOutcome] = field(default_factory=list)


@dataclass
class Task:
    task_id: int
    set_id: int
    description: str
    target_resident: str
    other_resident: Optional[str]  # the resident on the other side of the relationship, if any
    involves_building: Optional[str]
    # Set by TaskCreatorAgent.generate_set() (round-robin over the seeded
    # item roster) when at least one Item exists -- GooseSolutionPlannerAgent
    # and ChainReactionAgent both fold this item's own registered
    # goose_actions/possible_outcomes in alongside the building's, so a
    # task's legal verbs and possible chain outcomes aren't limited to
    # whatever one building.kind happens to offer. None means this task has
    # no item riding along, which is a legitimate, common case, not an error.
    involves_item: Optional[str] = None
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
    lines: List[str]  # goose-verb-only stage directions (honk/grab/drop/duck/dash) -- no dialogue, ever


@dataclass
class StagedAction:
    actor: str
    action: str
    location: str


@dataclass
class ChainReaction:
    """The Chain Reaction Agent's output: at most two follow-on beats after
    the goose's own action -- the target resident's own use of whatever the
    goose dropped or delivered, and, only when the affordance registers a
    chain_effect AND the task has an other_resident to draw in, that second
    resident's reaction. Zero steps is the common case (most Building/Item
    affordances have no resident_actions registered at all) and is not an
    error -- see ChainReactionAgent."""

    task_id: int
    steps: List[StagedAction] = field(default_factory=list)
    # The chain_effect text actually realized this run, if the chain
    # reached its second step -- empty otherwise, including when steps has
    # exactly one entry (a resident acted on the object, but nothing
    # cascaded further).
    chain_effect: str = ""


@dataclass
class NewsBulletin:
    task_id: int
    headline: str
