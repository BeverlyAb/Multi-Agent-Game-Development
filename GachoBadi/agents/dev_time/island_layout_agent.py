from __future__ import annotations

from typing import List

from agents.base import BaseAgent
from definitions.models import Building


class IslandLayoutAgent(BaseAgent):
    role = "Island Layout Agent"
    goal = "Arrange available buildings into a coherent island layout."

    """
    Input:  the list of Buildings on the island.
    Output: a layout narrative, and each building is mutated in place
            with a .location, which TaskCreatorAgent, WriterAgent, and
            DirectorAgent all require.
    """

    ZONES = ["north dock", "town square", "east meadow", "pond overlook", "west orchard", "south gate"]

    def run(self, buildings: List[Building]) -> str:
        if not buildings:
            self._log("no buildings yet -> nothing to lay out")
            return "(no buildings yet)"
        for i, building in enumerate(buildings):
            building.location = self.ZONES[i % len(self.ZONES)]
        names = ", ".join(f"{b.name} ({b.location})" for b in buildings)
        fallback = f"Layout: {names}, arranged in a loop around the goose's starting pond."
        spec = self.llm.generate(
            system="You write a short island layout description placing the given buildings at their assigned zones.",
            prompt=f"Buildings and zones: {[(b.name, b.location) for b in buildings]}",
            fallback=fallback,
        )
        self._log(f"assigned locations: {[(b.name, b.location) for b in buildings]}")
        return spec
