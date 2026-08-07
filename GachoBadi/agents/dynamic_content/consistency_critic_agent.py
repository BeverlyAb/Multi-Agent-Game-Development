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

    def _find_redundant_step_targets(self, content_text: str) -> List[str]:
        """Flags goose-verb steps that only differ by which verb is used --
        e.g. "Grab near the bakery." / "Honk near the bakery." -- reads as
        a copy-paste of the same line with the verb swapped, not a real
        staged sequence. This is a detection-only check: unlike a wrong
        verb or a banned tone word, there's no single mechanical
        substitution that fixes a redundant *target* -- that requires the
        Task Premise Content Agent to actually author a distinct target
        per step, so this reports the break rather than papering over it.
        """
        known_verbs = sorted(self.ALLOWED_VERBS | set(self.VERB_FIX), key=len, reverse=True)
        verb_alt = "|".join(re.escape(v) for v in known_verbs)
        step_re = re.compile(rf"^Goose:\s*(?:{verb_alt})\s+(.+?)\.?\s*$", re.MULTILINE)
        lines_by_target: dict = {}
        for match in step_re.finditer(content_text):
            target = match.group(1).strip().lower()
            lines_by_target.setdefault(target, []).append(match.group(0).strip())

        violations: List[str] = []
        for target, lines in lines_by_target.items():
            if len(lines) > 1:
                violations.append(
                    f"{len(lines)} goose-verb steps all target the identical phrase "
                    f"'{target}' ({'; '.join(lines)}) -- each step reads as a copy-paste of "
                    f"the last with only the verb swapped; the Task Premise Content Agent "
                    f"needs to vary what each step actually targets, not just which verb "
                    f"performs it."
                )
        return violations

    def check_catalog_redundancy(self, task_records: List[dict]) -> List[str]:
        """Batch-level check across multiple already-generated task premises.

        _find_redundant_step_targets only sees one task at a time, so it
        can't catch the redundancy that only shows up once a catalog is
        read as a whole: two structurally fine, individually-non-redundant
        tasks that both center on the same item, or run the identical
        verb sequence, still read as a reused template once the player
        (or the ~30-40-task catalog Draft #10 describes) sees both.

        Each dict in task_records needs 'label' (e.g. a connection_kind),
        'item_name', and 'text' (the task's final_output).
        """
        known_verbs = sorted(self.ALLOWED_VERBS | set(self.VERB_FIX), key=len, reverse=True)
        verb_alt = "|".join(re.escape(v) for v in known_verbs)
        verb_re = re.compile(rf"^Goose:\s*({verb_alt})\b", re.MULTILINE)

        seen_items: dict = {}
        seen_verb_sequences: dict = {}
        for rec in task_records:
            label = rec.get("label", "task")
            item = rec.get("item_name")
            if item:
                seen_items.setdefault(item, []).append(label)
            verbs = tuple(verb_re.findall(rec.get("text", "")))
            if verbs:
                seen_verb_sequences.setdefault(verbs, []).append(label)

        violations: List[str] = []
        for item, labels in seen_items.items():
            if len(labels) > 1:
                violations.append(
                    f"{len(labels)} tasks ({', '.join(labels)}) all center on the same item "
                    f"'{item}' -- a catalog where every task reuses one item reads as reused "
                    "content no matter how each individual task is worded."
                )
        for verbs, labels in seen_verb_sequences.items():
            if len(labels) > 1:
                violations.append(
                    f"{len(labels)} tasks ({', '.join(labels)}) all run the identical verb "
                    f"sequence {list(verbs)} -- distinct premises with the same mechanical "
                    "solution read as the same task twice."
                )
        if violations:
            self._log(f"caught {len(violations)} catalog-level issue(s)")
        else:
            self._log(f"no catalog-level redundancy across {len(task_records)} task(s)")
        return violations

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

        auto_corrected_count = len(violations)
        redundancy_violations = self._find_redundant_step_targets(corrected)
        violations.extend(redundancy_violations)

        grounding_text = "\n".join(getattr(c, "text", str(c)) for c in grounding_chunks)
        if not violations:
            fallback_summary = "no lore breaks or tone drift found."
        elif redundancy_violations and auto_corrected_count:
            fallback_summary = (
                f"found {len(violations)} issue(s): {auto_corrected_count} corrected in place, "
                f"{len(redundancy_violations)} flagged for the Task Premise Content Agent to fix "
                "(redundant step targets aren't mechanically correctable)."
            )
        elif redundancy_violations:
            fallback_summary = (
                f"found {len(redundancy_violations)} redundant-step issue(s), flagged for the "
                "Task Premise Content Agent to fix (not mechanically correctable)."
            )
        else:
            fallback_summary = f"found {len(violations)} issue(s), corrected in place."
        fallback_commentary = f"Checked against {len(grounding_chunks)} retrieved GDD chunk(s); {fallback_summary}"
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
