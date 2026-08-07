"""The Crew: coordinates all twelve agents through a personality pass, a
relationship pass, a dev-time pass, an item-interaction pass, and a full
playthrough of the lifetime task catalog (sets -> 75% threshold -> next
set -> backlog mop-up -> Game Completion), matching gdd.txt's Game
Mechanics and Game Completion sections -- not just one illustrative tick.
"""
from __future__ import annotations

from dataclasses import asdict
from typing import List

from agents.dev_time.scene_orchestrator import SceneOrchestratorAgent
from agents.runtime.character_personality_agent import CharacterPersonalityAgent
from agents.runtime.chain_reaction_agent import ChainReactionAgent
from agents.runtime.director_agent import DirectorAgent
from agents.runtime.goose_solution_planner_agent import GooseSolutionPlannerAgent
from agents.runtime.item_interaction_agent import ItemInteractionAgent
from agents.runtime.newscaster_agent import NewscasterAgent
from agents.runtime.relationship_agent import RelationshipAgent
from agents.runtime.task_creator_agent import TaskCreatorAgent, build_catalog
from agents.runtime.writer_agent import WriterAgent
from llm_client import LLMClient
from models import Building, Item, Resident, Task


class GachoBadiCrew:
    """Orchestrates the Gacho Badi AI agents for a full playthrough."""

    def __init__(self, seed: int = 7):
        self.llm = LLMClient(seed=seed)
        self.personality_agent = CharacterPersonalityAgent(self.llm)
        self.relationship_agent = RelationshipAgent(self.llm)
        self.item_interaction_agent = ItemInteractionAgent(self.llm)
        self.task_creator = TaskCreatorAgent(self.llm)
        self.writer = WriterAgent(self.llm)
        self.goose_planner = GooseSolutionPlannerAgent(self.llm)
        self.chain_reaction_agent = ChainReactionAgent(self.llm)
        self.director = DirectorAgent(self.llm)
        self.newscaster = NewscasterAgent(self.llm)
        self.scene_orchestrator = SceneOrchestratorAgent(self.llm)

    def run_personality_pass(self, residents: List[Resident]) -> List[Resident]:
        """Enriches raw resident requests (name/role/sliders) with traits + a summary."""
        print("\n=== PERSONALITY PASS: Character Personality Agent ===")
        return [self.personality_agent.run(r.name, r.role, r.sliders) for r in residents]

    def run_relationship_pass(self, residents: List[Resident]) -> List[Resident]:
        """Maps how every pair of residents feels about each other, and why. Requires .traits."""
        print("\n=== RELATIONSHIP PASS: Relationship Agent ===")
        return self.relationship_agent.run(residents)

    def run_dev_time_pass(self, residents: List[Resident], buildings: List[Building]) -> dict:
        """Simulates a programmer asking the Scene Orchestrator for new content.

        Expects `residents` to already carry personality traits (see
        run_personality_pass). Order matters here: IslandLayoutAgent must
        assign building.location before BuildingDesignerAgent/Writer read
        it, and CharacterAppearanceAgent needs resident.traits, which is
        why layout runs first and appearance runs last.
        """
        print("\n=== DEV-TIME PASS: Scene Orchestrator ===")
        layout = self.scene_orchestrator.run("layout", buildings)
        building_specs = [self.scene_orchestrator.run("building", b) for b in buildings]
        appearances = [self.scene_orchestrator.run("appearance", r) for r in residents]
        return {"layout": layout, "building_specs": building_specs, "appearances": appearances}

    def run_item_interaction_pass(self, buildings: List[Building], items: List[Item]) -> dict:
        """Loads the compact affordance graph the Goose Solution Planner
        treats as the only legal action set. Requires buildings already
        designed (run_dev_time_pass)."""
        print("\n=== ITEM INTERACTION PASS: Item Interaction / World Affordance Agent ===")
        return self.item_interaction_agent.run(buildings, items)

    def _resolve_or_retire(self, task: Task, residents: List[Resident], buildings: List[Building]) -> dict:
        """Runs one task through Goose Solution Planner -> Chain Reaction ->
        Writer -> Director -> Newscaster, per gdd.txt's approval-gate rule:
        the planner may retire a candidate instead of staging it, and that
        retirement counts toward the 75% threshold exactly like a
        resolution."""
        verb_plan = self.goose_planner.run(task, buildings)
        if verb_plan is None:
            task.status = "retired"
            task.retire_reason = f"no registered goose actions for '{task.involves_building}'"
            return {
                "task": task,
                "screenplay": None,
                "verb_plan": None,
                "chain": None,
                "staged_actions": [],
                "news": None,
            }

        building = next((b for b in buildings if b.name == task.involves_building), None)
        chain = self.chain_reaction_agent.run(task, building, residents)
        screenplay = self.writer.run(task, residents, buildings, chain)
        staged_actions = self.director.run(screenplay, verb_plan, task, buildings, residents, chain)
        news = self.newscaster.run(staged_actions, task)
        if task.status == "open":
            # check_goal_state failed (e.g. a referenced resident/building
            # vanished) -- gdd.txt: re-plan or retire outright rather than
            # leaving the player stuck.
            task.status = "retired"
            task.retire_reason = "goal state unreachable after generation (re-plan target missing)"
        return {
            "task": task,
            "screenplay": screenplay,
            "verb_plan": verb_plan,
            "chain": chain,
            "staged_actions": staged_actions,
            "news": news,
        }

    def run_playthrough(self, residents: List[Resident], buildings: List[Building]) -> dict:
        """The full task-set loop: reveal a 5-9-task set from the lifetime
        catalog, resolve/retire tasks until 75% of the set has left "open"
        status, reveal the next set, and repeat until the catalog is
        exhausted. Then mop up every task still sitting "open" on the
        always-visible backlog -- gdd.txt: the true ending needs every
        generated task to have left the active list, resolved or retired,
        not just each set's 75% gate -- and declare Game Completion.

        Expects `residents` to already carry personality traits +
        relationships + relationship backstories + an appearance spec, and
        `buildings` to already carry an assigned location, a design, and
        registered goose_actions (see run_personality_pass,
        run_relationship_pass, run_dev_time_pass, and
        run_item_interaction_pass) -- every agent below validates this and
        raises if a prior agent was skipped.
        """
        print("\n=== PLAYTHROUGH: task sets, 75% threshold, backlog, completion ===")
        catalog = build_catalog(residents, buildings)
        all_tasks: List[Task] = []
        set_summaries: List[dict] = []
        tick_records: List[dict] = []
        # Task Creator's own output (the premises + goal_states it selected
        # for this set) is a distinct agent output from what later happens
        # to each task (Goose Planner/Writer/Director/Newscaster, captured
        # in tick_records) -- snapshotted here, right after generate_set()
        # and before any resolution mutates task.status, so the two don't
        # collapse into one file when main.py writes them out separately.
        set_task_snapshots: List[dict] = []

        offset = 0
        set_id = 1
        while offset < len(catalog):
            remaining = len(catalog) - offset
            size = min(self.task_creator.SET_SIZE_MAX, remaining)
            tasks = self.task_creator.generate_set(catalog, offset, set_id, residents, buildings, size=size)
            threshold = self.task_creator.threshold_for(len(tasks))
            set_task_snapshots.append({"set_id": set_id, "premises": [asdict(t) for t in tasks]})

            settled = 0
            for task in tasks:
                if settled >= threshold:
                    break  # rest of this set stays "open" on the always-visible backlog
                tick_records.append(self._resolve_or_retire(task, residents, buildings))
                settled += 1

            all_tasks.extend(tasks)
            set_summaries.append(
                {
                    "set_id": set_id,
                    "size": len(tasks),
                    "threshold": threshold,
                    "settled_this_set": settled,
                    "still_open": len(tasks) - settled,
                }
            )
            print(
                f"  set #{set_id}: {len(tasks)} task(s), threshold {threshold} -- "
                f"{settled} settled this set, {len(tasks) - settled} left open on the backlog"
            )
            offset += len(tasks)
            set_id += 1

        backlog = [t for t in all_tasks if t.status == "open"]
        if backlog:
            print(f"\n  --- backlog mop-up: {len(backlog)} task(s) still open, resolving toward the true ending ---")
        for task in backlog:
            tick_records.append(self._resolve_or_retire(task, residents, buildings))

        completion = self._build_completion(all_tasks, residents)
        print(f"\n  {completion['headline']}")
        for line in completion["epilogue_lines"]:
            print(f"    {line}")

        return {
            "personalities": residents,
            "catalog_size": len(catalog),
            "sets": set_summaries,
            "set_task_snapshots": set_task_snapshots,
            "ticks": tick_records,
            "final_tasks": all_tasks,
            "completion": completion,
        }

    def _build_completion(self, tasks: List[Task], residents: List[Resident]) -> dict:
        """gdd.txt's Game Completion: 'a short cast-wide scene names every
        resident once' -- one authored line per relationship thread (not
        per task; the catalog generates several tasks per pair, one per
        building, and re-narrating the same pair 3 times would read as
        repetitive filler), differentiated by whether that thread
        ultimately resolved or was retired -- never told as an identical,
        unearned success."""
        residents_by_name = {r.name: r for r in residents}
        threads: dict = {}
        for task in tasks:
            if not task.other_resident or task.status == "open":
                continue
            pair_key = frozenset((task.target_resident, task.other_resident))
            # A pair's thread only reads as truly "left open" if every one
            # of its instances retired; a single resolution is the thread's
            # real outcome even if another building's instance retired.
            if pair_key in threads and threads[pair_key].status == "resolved":
                continue
            threads[pair_key] = task

        epilogue_lines: List[str] = []
        for task in threads.values():
            resident = residents_by_name.get(task.target_resident)
            other_name = task.other_resident
            if task.status == "resolved":
                backstory = resident.relationship_backstories.get(other_name, "") if resident and other_name else ""
                epilogue_lines.append(
                    f"{task.target_resident} & {other_name}: reconciled -- {backstory or 'their thread is mended.'}"
                )
            else:
                epilogue_lines.append(
                    f"{task.target_resident} & {other_name}: thread left open -- {task.retire_reason}"
                )
        all_settled = all(t.status != "open" for t in tasks)
        headline = (
            "GAME COMPLETION: the island has reached harmony -- every generated task has left the active list."
            if all_settled and tasks
            else "GAME COMPLETION: not yet reachable -- tasks remain open."
        )
        return {"headline": headline, "epilogue_lines": epilogue_lines, "harmony": all_settled and bool(tasks)}

    @staticmethod
    def to_jsonable(value):
        def conv(v):
            if hasattr(v, "__dataclass_fields__"):
                return asdict(v)
            if isinstance(v, list):
                return [conv(x) for x in v]
            if isinstance(v, dict):
                return {k: conv(x) for k, x in v.items()}
            return v

        return conv(value)
