"""Entry point: runs the Tomodachi-Life-style island crew end-to-end and
writes output/run.json.

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

from crew import TomodachiLifeCrew
from models import Apartment, Mii, PersonalityDials


def build_island_seed():
    """A small island snapshot in Tomodachi Life's own spirit: quiz-built Miis and facilities."""
    miis = [
        Mii(
            name="Chip",
            role="aspiring chef",
            dials=PersonalityDials(expressiveness=70, diligence=80, confidence=55, mischief=20),
        ),
        Mii(
            name="Dot",
            role="poet",
            dials=PersonalityDials(expressiveness=85, diligence=35, confidence=30, mischief=45),
        ),
        Mii(
            name="Rex",
            role="gym rat",
            dials=PersonalityDials(expressiveness=60, diligence=90, confidence=90, mischief=75),
        ),
    ]
    apartments = [
        Apartment(name="Cafe Deja Brew", kind="cafe", feature="a jukebox that plays a Mii's own song"),
        Apartment(name="Threads Boutique", kind="clothes shop", feature="a fitting-room mirror that gossips"),
        Apartment(name="Snapshot Studio", kind="photo studio", feature="a backdrop that changes with a Mii's mood"),
    ]
    return miis, apartments


def main() -> int:
    print("Tomodachi Life -- Island Event Generation Crew")
    print("=" * 55)

    try:
        miis, apartments = build_island_seed()
        crew = TomodachiLifeCrew(seed=7)

        miis = crew.run_personality_pass(miis)
        miis = crew.run_relationship_pass(miis)
        prep_result = crew.run_prep_pass(miis, apartments)
        tick_result = crew.run_event_tick(miis, apartments)

        output = {
            "game": "Tomodachi Life",
            "prep_pass": prep_result,
            "event_tick": TomodachiLifeCrew.to_jsonable(tick_result),
        }

        os.makedirs("output", exist_ok=True)
        out_path = os.path.join("output", "run.json")
        with open(out_path, "w") as f:
            json.dump(output, f, indent=2)

        print("\n=== SUMMARY ===")
        print(f"Miis processed        : {len(tick_result['miis'])}")
        print(f"Events generated      : {len(tick_result['events'])}")
        if tick_result["skit"]:
            print(f"Skit lines            : {len(tick_result['skit'].lines)}")
            print(f"Staged moments        : {len(tick_result['staged_moments'])}")
        if tick_result["news"]:
            print(f"News headline         : {tick_result['news'].headline}")
        print(f"LLM provider in use   : {crew.llm.provider} "
              f"({'live API calls' if crew.llm.provider != 'mock' else 'local deterministic fallback'})")
        print(f"Full run written to   : {os.path.abspath(out_path)}")
        return 0
    except Exception as exc:  # last-resort guard: never let the crew crash silently
        print(f"\n[FATAL] Crew run failed unexpectedly: {exc!r}", file=sys.stderr)
        print("This should not happen -- please file a bug with the traceback above.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
