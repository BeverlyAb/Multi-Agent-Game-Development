"""Entry point: runs the Gacho Badi crew end-to-end -- personality,
relationships, dev-time content, item interaction, and a full playthrough
of the lifetime task catalog through Game Completion -- and writes
output/run.json.

Usage:
    python3 main.py

No API key or third-party package is required -- set ANTHROPIC_API_KEY or
OPENAI_API_KEY (and install the matching SDK) to have agents call a real
model instead of the deterministic local fallback. Either way this script
is guaranteed to finish and produce output; see the try/except in main().
"""
from __future__ import annotations

import json
import os
import sys

from crew import GachoBadiCrew
from models import Building, Item, Resident, Sliders


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

        output = {
            "game": "Gacho Badi (Goose Buddy)",
            "dev_time_pass": dev_time_result,
            "item_interaction_pass": item_interaction_result,
            "playthrough": GachoBadiCrew.to_jsonable(playthrough),
        }

        os.makedirs("output", exist_ok=True)
        out_path = os.path.join("output", "run.json")
        with open(out_path, "w") as f:
            json.dump(output, f, indent=2)

        resolved = sum(1 for t in playthrough["final_tasks"] if t.status == "resolved")
        retired = sum(1 for t in playthrough["final_tasks"] if t.status == "retired")

        print("\n=== SUMMARY ===")
        print(f"Residents processed  : {len(playthrough['personalities'])}")
        print(f"Lifetime catalog size: {playthrough['catalog_size']}")
        print(f"Task sets played     : {len(playthrough['sets'])}")
        print(f"Tasks resolved       : {resolved}")
        print(f"Tasks retired        : {retired}")
        print(f"Harmony reached      : {playthrough['completion']['harmony']}")
        print(f"LLM provider in use  : {crew.llm.provider} "
              f"({'live API calls' if crew.llm.provider != 'mock' else 'local deterministic fallback'})")
        print(f"Full run written to  : {os.path.abspath(out_path)}")
        return 0
    except Exception as exc:  # last-resort guard: never let the crew crash silently
        print(f"\n[FATAL] Crew run failed unexpectedly: {exc!r}", file=sys.stderr)
        print("This should not happen -- please file a bug with the traceback above.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
