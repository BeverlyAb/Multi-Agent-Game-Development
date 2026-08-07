from __future__ import annotations

from agents.base import BaseAgent
from definitions.models import Building


class BuildingDesignerAgent(BaseAgent):
    role = "Building Designer Agent"
    goal = "Design a building and its interactive architecture."

    """
    Input:  a Building with a raw .interactive_feature hint.
    Output: an enriched design spec, written back into
            building.interactive_feature, plus building.designed = True
            so every downstream agent (Task Creator, Writer) can require
            and confirm a designed building, not just the raw seed text.
    """

    def run(self, building: Building) -> str:
        fallback = f"{building.name} ({building.kind}): features {building.interactive_feature}."
        spec = self.llm.generate(
            system="You write a one-paragraph building design spec, emphasizing the interactive feature.",
            prompt=f"Building: {building}",
            fallback=fallback,
        )
        building.interactive_feature = spec
        building.designed = True
        self._log(f"designed building {building.name}")
        return spec
