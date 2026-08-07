"""Gap-detection LOGIC for agents/runtime/task_creator_agent.py -- pairs
with task_creator_constraints.yaml.

These checks re-create, in a properly-scoped place, a capability this
project used to get from the (now-removed) Assignment #4 Consistency
Critic Agent: catching tone drift (mischief/chaos language that
contradicts this game's own "quiet community-builder" pitch) and
descriptions disconnected from the pair/building they're supposed to be
about. Unlike that removed, separate RAG pipeline, this lives right next
to the one agent that actually authors task descriptions during real
play, in the same crew that ships them.

context dict this file's detectors expect:
  {
    "resident_name": str,
    "other_name": str,
    "building_name": str,
  }
"""
from __future__ import annotations

import os
from typing import Dict, List

from ..guardrails import TokenBudget
from ..verification_models import Finding, Severity
from .base import AgentConstraints
from .config_loader import load_constraint_config

_CONFIG = load_constraint_config(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "task_creator_constraints.yaml")
)
TOKEN_BUDGET = TokenBudget(**_CONFIG["token_budget"])

# Same tone list the (now-removed) Consistency Critic Agent used to
# enforce (agents/dynamic_content/consistency_critic_agent.py, deleted
# along with the rest of Assignment #4's pipeline) -- Gacho Badi's pitch
# is explicitly NOT mischief-for-its-own-sake, unlike the Untitled Goose
# Game agents this crew's own agents were partly adapted from.
_BANNED_TONE_WORDS = ("mischief", "chaos", "prank", "mischievous", "trick", "sabotage")


def mentions_both_residents(output: str, context: Dict) -> List[Finding]:
    """A task is ABOUT a specific pair -- a description naming neither of
    them usually means the LLM drifted into generic flavor text
    disconnected from who this task actually concerns."""
    resident = context.get("resident_name", "")
    other = context.get("other_name", "")
    missing = [n for n in (resident, other) if n and n not in output]
    if missing:
        return [
            Finding(
                rule="mentions_both_residents",
                message=f"description never names {', '.join(missing)}, the resident(s) this task is about",
                severity=Severity.BLOCKING,
            )
        ]
    return []


def mentions_building(output: str, context: Dict) -> List[Finding]:
    """Every one of this agent's own TEMPLATES references {building} --
    a generated description that drops the building entirely loses the
    one piece of staging context the Goose Solution Planner and Director
    both need to physically place the scene. Advisory, not blocking:
    unlike naming the residents, an LLM paraphrase that implies the
    location without naming it verbatim ("at her own bakery") is a
    plausible, acceptable rewrite, not a defect."""
    building = context.get("building_name", "")
    if building and building not in output:
        return [
            Finding(
                rule="mentions_building",
                message=f"description never names '{building}', the building this task is staged at",
                severity=Severity.ADVISORY,
            )
        ]
    return []


def no_mischief_tone(output: str, context: Dict) -> List[Finding]:
    """gdd.txt Executive Summary: Gacho Badi's goose 'is a quiet
    community-builder,' explicitly not causing 'chaos for its own sake'
    the way Untitled Goose Game's goose does -- a task description
    leaning on mischief/chaos language has drifted into the wrong game's
    voice, the specific risk this crew's own agents (partly adapted from
    UntitledGooseGame_Multi_Agent) were always most exposed to."""
    lowered = output.lower()
    hits = [w for w in _BANNED_TONE_WORDS if w in lowered]
    if hits:
        return [
            Finding(
                rule="no_mischief_tone",
                message=f"description uses tone word(s) {hits}, contradicting the GDD's 'quiet community-builder' framing",
                severity=Severity.BLOCKING,
            )
        ]
    return []


def not_too_short(output: str, context: Dict) -> List[Finding]:
    """Advisory: a task description under ~20 characters is almost
    certainly truncated or degenerate, even if nothing above fired."""
    stripped = output.strip()
    if len(stripped) < 20:
        return [
            Finding(
                rule="not_too_short",
                message=f"description is only {len(stripped)} character(s) long",
                severity=Severity.ADVISORY,
            )
        ]
    return []


TASK_CREATOR_CONSTRAINTS = AgentConstraints(
    agent_name="Task Creator Agent",
    token_budget=TOKEN_BUDGET,
    gap_detectors=[mentions_both_residents, no_mischief_tone, mentions_building, not_too_short],
    priority_weights=_CONFIG.get("priority_weights", {}),
    max_retries=_CONFIG.get("max_retries", 2),
)
