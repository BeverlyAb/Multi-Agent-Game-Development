"""Gap-detection LOGIC for agents/runtime/goose_solution_planner_agent.py
-- pairs with goose_solution_planner_constraints.yaml, which holds this
same agent's token budget and priority weights (the values that don't
need code). Split this way per the project's own choice: declarative
values live in YAML, only genuine logic (regex extraction, etc.) lives
in Python -- see config_loader.py and workflow/README.md's "What's
generic vs. what's per-agent" section for why.

The checks below encode the hard rules that agent's own docstring
already claims but never mechanically checked before this workflow
existed: it "cannot invent an object behavior that isn't real"
(agents/base.py's shared BaseAgent contract) and must never write
dialogue, since the goose has none in this universe.

context dict this file's detectors expect:
  {
    "legal_verbs": List[str],   # building.goose_actions for this task
    "task_description": str,   # task.description, for the relevance check
  }
"""
from __future__ import annotations

import os
import re
from typing import Dict, List

from ..generic.guardrails import TokenBudget
from ..definitions.models_verification import Finding, Severity
from .base import AgentConstraints
from .config_loader import load_constraint_config

_CONFIG = load_constraint_config(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "goose_solution_planner_constraints.yaml")
)
TOKEN_BUDGET = TokenBudget(**_CONFIG["token_budget"])

_GOOSE_LINE_RE = re.compile(r"^\s*\*?\s*Goose:\s*([A-Za-z ]+?)\b", re.MULTILINE)


def no_unregistered_verb(output: str, context: Dict) -> List[Finding]:
    """The single most important check for this agent: every 'Goose:
    <verb> ...' line must use a verb from context['legal_verbs'] (the
    building's registered goose_actions). An unregistered verb here means
    the planner invented an action the Item Interaction Agent never
    certified -- exactly the failure mode the crew's whole architecture
    (GooseSolutionPlannerAgent's hard dependency on ItemInteractionAgent)
    exists to prevent."""
    legal = {v.lower() for v in context.get("legal_verbs", [])}
    if not legal:
        return []  # no legal set supplied -- nothing to check against
    findings = []
    for match in _GOOSE_LINE_RE.finditer(output):
        verb = match.group(1).strip().lower()
        # Verb text can run past a single word (e.g. "Grab" vs "Grab the
        # nozzle") -- only the first word is the actual verb.
        first_word = verb.split()[0] if verb.split() else verb
        if first_word not in legal:
            findings.append(
                Finding(
                    rule="no_unregistered_verb",
                    message=f"line uses verb '{first_word}', which is not in the registered set {sorted(legal)}",
                    severity=Severity.BLOCKING,
                )
            )
    return findings


def no_dialogue_leak(output: str, context: Dict) -> List[Finding]:
    """The goose never speaks -- this agent's own system prompt says so
    ('no dialogue, ever'), matching gdd.txt's Writer Agent being the ONLY
    place any character's spoken line is allowed to appear. A quoted
    string following 'GOOSE:' would mean the LLM ignored that instruction."""
    if re.search(r"GOOSE:[^\n]*[\"“]", output, re.IGNORECASE):
        return [
            Finding(
                rule="no_dialogue_leak",
                message="output appears to give the goose a quoted spoken line, which this agent must never do",
                severity=Severity.BLOCKING,
            )
        ]
    return []


def has_at_least_one_verb_step(output: str, context: Dict) -> List[Finding]:
    """Distinct from guardrails.check_non_empty: text can be non-empty
    (e.g. just a scene heading) while still containing zero actionable
    'Goose: <verb>' steps, which leaves DirectorAgent nothing to stage --
    DirectorAgent.run() raises ValueError on an empty VerbPlan.lines, but
    a plan with lines and zero real verb steps would slip past that
    check and silently do nothing in-game."""
    if not _GOOSE_LINE_RE.search(output):
        return [
            Finding(
                rule="has_at_least_one_verb_step",
                message="output contains no 'Goose: <verb>' step for the Director to stage",
                severity=Severity.BLOCKING,
            )
        ]
    return []


def mentions_task_context(output: str, context: Dict) -> List[Finding]:
    """Advisory, not blocking: flags a plan that never references the
    task's own description in any recognizable way, which usually means
    the LLM produced generic boilerplate disconnected from what this
    specific task actually needs solved. Not blocking because the
    fallback template text legitimately paraphrases rather than quotes
    the description verbatim, and an LLM's paraphrase is normal, not a
    defect -- a human/reviewer should still see it flagged, though."""
    description = context.get("task_description", "")
    if not description:
        return []
    # Cheap relevance signal: does the plan share at least one
    # non-trivial word (4+ letters) with the task description?
    desc_words = {w.lower() for w in re.findall(r"[A-Za-z]{4,}", description)}
    output_words = {w.lower() for w in re.findall(r"[A-Za-z]{4,}", output)}
    if desc_words and not (desc_words & output_words):
        return [
            Finding(
                rule="mentions_task_context",
                message="plan shares no words with the task description -- may be generic boilerplate",
                severity=Severity.ADVISORY,
            )
        ]
    return []


# Priority weights (e.g. no_unregistered_verb outranking every other
# BLOCKING finding for this agent) come straight from the YAML config
# above -- no Python subclass needed just to boost one rule's ranking;
# AgentConstraints.priority_score() already consults priority_weights
# generically. Only add a real priority_score() override here if this
# agent ever needs ranking logic a flat rule -> weight table can't express.
GOOSE_SOLUTION_PLANNER_CONSTRAINTS = AgentConstraints(
    agent_name="Goose Solution Planner Agent",
    token_budget=TOKEN_BUDGET,
    gap_detectors=[
        no_unregistered_verb,
        no_dialogue_leak,
        has_at_least_one_verb_step,
        mentions_task_context,
    ],
    priority_weights=_CONFIG.get("priority_weights", {}),
    max_retries=_CONFIG.get("max_retries", 2),
)
