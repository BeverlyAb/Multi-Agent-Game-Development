"""Entry point: runs the Gacho Badi crew end-to-end -- personality,
relationships, dev-time content, item interaction, and a full playthrough
of the lifetime task catalog through Game Completion -- and writes every
generated piece to its own file under output/crew/, one file per
generated piece plus a manifest.json indexing all of them in order.

Usage (from anywhere -- output/ is always resolved relative to this
project's root, not the caller's working directory):
    python3 executable/main.py

No API key or third-party package is required -- set ANTHROPIC_API_KEY or
OPENAI_API_KEY (and install the matching SDK) to have agents call a real
model instead of the deterministic local fallback. Either way this script
is guaranteed to finish and produce output; see the try/except in main().
"""
from __future__ import annotations

import itertools
import json
import os
import re
import sys
from dataclasses import asdict

# This file now lives in executable/, one level below the project root --
# api/, definitions/, agents/, and output/ are siblings of executable/, not
# children of it. Add the root to sys.path so `definitions.models` and
# `api.llm_client` (and, transitively, `agents.*` inside crew.py) resolve
# no matter what directory this script is invoked from. `crew` itself
# needs no such help -- crew.py lives right next to this file in
# executable/, which Python already puts on sys.path for a directly-run
# script.
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from crew import GachoBadiCrew
from definitions.models import Building, Item, Resident, Sliders

OUTPUT_DIR = os.path.join(ROOT_DIR, "output", "crew")


def slugify(text: str, max_words: int = 4) -> str:
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())[:max_words]
    return "-".join(words) or "untitled"


def build_island_seed():
    """A small island snapshot pulled straight from the GDD's examples.

    Deliberately smaller than the shipped 6-resident/6-building roster
    (gdd.txt's own Scope & First Playable Slice section: the full roster
    is explicitly deferred past the first playable slice) -- but every
    mechanic below (sets, the 75% threshold, retirement, the backlog,
    completion) is the same code path the full roster would run, just
    over a smaller catalog.
    """
    residents = [
        Resident(name="Hazel", role="baker", sliders=Sliders(movement=30, speech=70, energy=60, intelligence=55)),
        Resident(name="Otto", role="teacher", sliders=Sliders(movement=20, speech=40, energy=35, intelligence=90)),
        Resident(name="Vic", role="gym instructor", sliders=Sliders(movement=90, speech=80, energy=95, intelligence=45)),
    ]
    buildings = [
        Building(name="Hazel's Bakery", kind="shop", interactive_feature="oven that can overheat and puff flour"),
        Building(name="Front Gate", kind="structure", interactive_feature="gate that can open and close"),
        Building(name="Garden Hose Stand", kind="prop", interactive_feature="hose that can spout water"),
    ]
    items = [
        Item(name="a family memento", kind="memento"),
    ]
    return residents, buildings, items


class OutputWriter:
    """Writes one JSON file per generated piece and builds the manifest
    entries describing where each one landed."""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.entries = []
        self._next = 1

    def write(self, content_type: str, detail: str, payload) -> str:
        filename = f"{self._next:02d}_{content_type}_{slugify(detail)}.json"
        self._next += 1
        with open(os.path.join(self.output_dir, filename), "w") as f:
            json.dump(payload, f, indent=2)
        self.entries.append({"content_type": content_type, "file": filename})
        return filename


def main() -> int:
    print("Gacho Badi (Goose Buddy) -- AI Architecture Crew")
    print("=" * 55)

    try:
        residents, buildings, items = build_island_seed()
        crew = GachoBadiCrew(seed=7)

        residents = crew.run_personality_pass(residents)
        residents = crew.run_relationship_pass(residents)
        dev_time_result = crew.run_dev_time_pass(residents, buildings)
        item_interaction_result = crew.run_item_interaction_pass(buildings, items)
        playthrough = crew.run_playthrough(residents, buildings)

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        for existing in os.listdir(OUTPUT_DIR):
            os.remove(os.path.join(OUTPUT_DIR, existing))
        out = OutputWriter(OUTPUT_DIR)

        # Character Personality Agent -- one file per resident.
        for resident in residents:
            out.write(
                "personality",
                resident.name,
                {
                    "name": resident.name,
                    "role": resident.role,
                    "sliders": asdict(resident.sliders),
                    "traits": resident.traits,
                    "personality_summary": resident.personality_summary,
                },
            )

        # Relationship Agent -- one file per unordered pair (label + backstory).
        for a, b in itertools.combinations(residents, 2):
            out.write(
                "relationship",
                f"{a.name}-{b.name}",
                {
                    "residents": [a.name, b.name],
                    "label": a.relationships.get(b.name, ""),
                    "backstory": a.relationship_backstories.get(b.name, ""),
                },
            )

        # Dev-Time Content Pipeline -- Island Layout, Building Designer, Character Appearance.
        out.write("island_layout", "layout", {"spec": dev_time_result["layout"]})
        for building, spec in zip(buildings, dev_time_result["building_specs"]):
            out.write("building_design", building.name, {"building": building.name, "spec": spec})
        for resident, spec in zip(residents, dev_time_result["appearances"]):
            out.write("appearance", resident.name, {"resident": resident.name, "spec": spec})

        # Item Interaction / World Affordance Agent -- one file per building, one per item.
        for building, spec in zip(buildings, item_interaction_result["building_specs"]):
            out.write(
                "item_interaction_building",
                building.name,
                {
                    "building": building.name,
                    "goose_actions": building.goose_actions,
                    "possible_outcomes": [asdict(o) for o in building.possible_outcomes],
                    "spec": spec,
                },
            )
        for item, spec in zip(items, item_interaction_result["item_specs"]):
            out.write(
                "item_interaction_item",
                item.name,
                {
                    "item": item.name,
                    "goose_actions": item.goose_actions,
                    "possible_outcomes": [asdict(o) for o in item.possible_outcomes],
                    "reset_rule": item.reset_rule,
                    "spec": spec,
                },
            )

        # Task Creator Agent -- one file per set, the pre-resolution premises it selected.
        for snapshot in playthrough["set_task_snapshots"]:
            out.write("task_set", f"set-{snapshot['set_id']}", snapshot)

        # Goose Solution Planner + Writer + Director + Newscaster -- one file per task.
        for tick in playthrough["ticks"]:
            task = tick["task"]
            out.write(
                "tick",
                f"task-{task.task_id:02d}-{task.status}",
                GachoBadiCrew.to_jsonable(tick),
            )

        # Game Completion -- one file, the epilogue.
        out.write("completion", "harmony" if playthrough["completion"]["harmony"] else "incomplete", playthrough["completion"])

        manifest = {
            "game": "Gacho Badi (Goose Buddy)",
            "catalog_size": playthrough["catalog_size"],
            "sets": playthrough["sets"],
            "records": out.entries,
        }
        manifest_path = os.path.join(OUTPUT_DIR, "manifest.json")
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        resolved = sum(1 for t in playthrough["final_tasks"] if t.status == "resolved")
        retired = sum(1 for t in playthrough["final_tasks"] if t.status == "retired")

        print("\n=== SUMMARY ===")
        print(f"Residents processed  : {len(playthrough['personalities'])}")
        print(f"Lifetime catalog size: {playthrough['catalog_size']}")
        print(f"Task sets played     : {len(playthrough['sets'])}")
        print(f"Tasks resolved       : {resolved}")
        print(f"Tasks retired        : {retired}")
        print(f"Harmony reached      : {playthrough['completion']['harmony']}")
        print(f"Output files written : {len(out.entries)} + manifest.json")
        print(f"LLM provider in use  : {crew.llm.provider} "
              f"({'live API calls' if crew.llm.provider != 'mock' else 'local deterministic fallback'})")
        print(f"Manifest written to  : {os.path.abspath(manifest_path)}")
        return 0
    except Exception as exc:  # last-resort guard: never let the crew crash silently
        print(f"\n[FATAL] Crew run failed unexpectedly: {exc!r}", file=sys.stderr)
        print("This should not happen -- please file a bug with the traceback above.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
