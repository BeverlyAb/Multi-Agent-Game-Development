from __future__ import annotations

from typing import List

from agents.base import BaseAgent
from definitions.models import NewsBulletin, StagedAction, Task


class NewscasterAgent(BaseAgent):
    role = "Newscaster Agent"
    goal = "Recap a resolved task as a short island bulletin."
    backstory = (
        "Borrowed from the Tomodachi Life reference crew's Newscaster Agent: gives the island's "
        "new community-building premise a visible, recurring payoff -- the island literally "
        "buzzes with what the goose just did."
    )

    """
    Input:  the staged actions from DirectorAgent and the active Task.
    Output: a NewsBulletin -- this crew's second terminal, player-visible
            output (alongside the staged actions themselves).
    """

    def run(self, staged_actions: List[StagedAction], task: Task) -> NewsBulletin:
        if not staged_actions:
            raise ValueError(
                f"NewscasterAgent has nothing to report for task #{task.task_id} "
                "-- DirectorAgent returned no staged actions."
            )
        fallback = f"ISLAND BULLETIN: {task.description}"
        headline = self.llm.generate(
            system="You write one short, warm island-bulletin headline recapping this community-building task.",
            prompt=f"Task: {task.description}\nStaged actions: {staged_actions}",
            fallback=fallback,
        )
        self._log(f"filed news bulletin for task #{task.task_id}")
        return NewsBulletin(task_id=task.task_id, headline=headline)
