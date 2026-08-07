"""Consistency Critic Agent -- not adapted from either reference crew.

Exists specifically because borrowing agent patterns from Untitled Goose
Game (a mischief/chaos game with a five-verb set Gacho Badi doesn't
share) risks leaking exactly that vocabulary into Gacho Badi's content.
It checks every generated output against the GDD chunks it was actually
grounded in, not against its own opinion.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

from agents.base import BaseAgent


@dataclass
class CriticReport:
    violations: List[str]
    corrected_text: str
    commentary: str


class ConsistencyCriticAgent(BaseAgent):
    role = "Consistency Critic Agent"
    goal = "Catch and correct lore breaks or tone drift before generated content reaches the pipeline's output."
    backstory = (
        "Exists specifically because borrowing agent patterns from Untitled Goose Game (a "
        "mischief/chaos game with a five-verb set Gacho Badi doesn't share) risks leaking "
        "exactly that vocabulary into Gacho Badi's content. It checks every generated output "
        "against the GDD chunks it was actually grounded in, not against its own opinion."
    )

    ALLOWED_VERBS = {"Honk", "Grab", "Pick up", "Duck", "Dash"}
    VERB_FIX = {"Run": "Dash", "Tug": "Pick up", "Flap": "Duck"}
    TONE_FIX = {"mischief": "connection", "chaos": "harmony", "prank": "gesture", "mischievous": "well-meaning"}

    @staticmethod
    def _match_case(replacement: str, original: str) -> str:
        if original[:1].isupper():
            return replacement[:1].upper() + replacement[1:]
        return replacement

    def run(self, content_text: str, grounding_chunks, valid_names: Optional[List[str]] = None) -> CriticReport:
        violations: List[str] = []
        corrected = content_text

        for bad_verb, good_verb in self.VERB_FIX.items():
            pattern = re.compile(rf"\b{re.escape(bad_verb)}\b")
            if pattern.search(corrected):
                violations.append(
                    f"used goose verb '{bad_verb}', which is not one of Gacho Badi's five verbs "
                    f"({', '.join(sorted(self.ALLOWED_VERBS))}) -- consistent with it being "
                    f"carried over while adapting an Untitled Goose Game agent; replaced with "
                    f"'{good_verb}'."
                )
                corrected = pattern.sub(good_verb, corrected)

        for bad_word, good_word in self.TONE_FIX.items():
            pattern = re.compile(rf"\b{re.escape(bad_word)}\b", re.IGNORECASE)
            match = pattern.search(corrected)
            if match:
                fixed = self._match_case(good_word, match.group(0))
                violations.append(
                    f"used tone word '{match.group(0)}', which contradicts the GDD's 'quiet "
                    f"community-builder, not mischief-for-its-own-sake' framing; replaced with "
                    f"'{fixed}'."
                )
                corrected = pattern.sub(fixed, corrected)

        grounding_text = "\n".join(getattr(c, "text", str(c)) for c in grounding_chunks)
        fallback_commentary = (
            f"Checked against {len(grounding_chunks)} retrieved GDD chunk(s); "
            + (
                f"found {len(violations)} issue(s), corrected in place."
                if violations
                else "no lore breaks or tone drift found."
            )
        )
        commentary = self.llm.generate(
            system=(
                "You are a strict continuity checker for a game design document. In one or two "
                "sentences, say whether the given content is consistent with the given GDD "
                "context (residents, verbs, tone) or name the specific break."
            ),
            prompt=f"GDD context:\n{grounding_text}\n\nContent to check:\n{content_text}",
            fallback=fallback_commentary,
        )

        if violations:
            self._log(f"caught {len(violations)} issue(s)")
        else:
            self._log("no issues found")
        return CriticReport(violations=violations, corrected_text=corrected, commentary=commentary)
