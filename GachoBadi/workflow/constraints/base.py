"""The shape every per-agent constraint file implements. This is the
seam between the generic engine (generic/guarded_llm_client.py) and agent-
specific knowledge -- the engine only ever calls AgentConstraints.evaluate()
and .priority_score(); it never inspects gap_detectors directly.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List

from ..generic.guardrails import TokenBudget
from ..definitions.models_verification import Finding, Severity

# A gap detector inspects one generate() call's OUTPUT TEXT plus whatever
# domain context the caller supplied (e.g. {"legal_verbs": [...], "task":
# task}) and returns zero or more Findings. It never raises for a finding
# -- absence of a problem is just an empty list, not an exception.
GapDetector = Callable[[str, Dict], List[Finding]]


@dataclass
class AgentConstraints:
    """Per-agent bundle of: a token budget (from gdd.txt's Technical
    Strategy table), a gap-detection pass (domain-specific Python
    functions -- the checks that need real logic), and priority_weights
    (a plain rule-name -> int mapping, meant to be loaded straight out of
    that agent's <name>_constraints.yaml via config_loader.py rather than
    written in code). A rule named in priority_weights outranks the
    default BLOCKING/ADVISORY-based score regardless of severity; a rule
    left out just falls back to that default. Override priority_score()
    directly only if an agent needs ranking logic beyond a flat
    rule -> weight table (rare -- most agents don't).
    """

    agent_name: str
    token_budget: TokenBudget
    gap_detectors: List[GapDetector] = field(default_factory=list)
    priority_weights: Dict[str, int] = field(default_factory=dict)
    # How many times GuardedLLMClient will retry (with the blocking
    # findings fed back into the prompt) before giving up and accepting
    # the last attempt anyway -- matches this crew's own "never leave the
    # player/pipeline stuck" philosophy (agents/runtime/*'s hard-fail
    # docstrings) rather than looping forever.
    max_retries: int = 2

    def priority_score(self, finding: Finding) -> int:
        if finding.rule in self.priority_weights:
            return self.priority_weights[finding.rule]
        return 100 if finding.severity == Severity.BLOCKING else 10

    def evaluate(self, output_text: str, context: Dict) -> List[Finding]:
        findings: List[Finding] = []
        for detector in self.gap_detectors:
            findings.extend(detector(output_text, context))
        for f in findings:
            f.priority = self.priority_score(f)
        findings.sort(key=lambda f: -f.priority)
        return findings
