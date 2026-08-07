"""Entry point for Assignment #4's Dynamic Content Pipeline.

Usage:
    python3 run_content_pipeline.py

Reads gdd.txt as the knowledge base, generates three GDD-grounded content
outputs (an item affordance spec, a relationship backstory, and a task
premise), and runs each through the Consistency Critic Agent before
writing output/content_pipeline_run.json. No API key required -- see
llm_client.py; this always produces output via the deterministic local
fallback if no provider is configured.
"""
from __future__ import annotations

import json
import os
import sys

from content_agents import ConsistencyCriticAgent
from content_pipeline import ContentPipeline


def main() -> int:
    print("Gacho Badi (Goose Buddy) -- Dynamic Content Pipeline (Assignment #4)")
    print("=" * 70)
    try:
        pipeline = ContentPipeline(gdd_path="gdd.txt", seed=7)
        print(f"Knowledge base loaded: {len(pipeline.kb.chunks)} chunks from gdd.txt")

        records = [
            pipeline.generate_item_affordance("a lost memento", "memento"),
            pipeline.generate_relationship_backstory("Hazel", "Otto", "drifted apart"),
            pipeline.generate_task_premise("Hazel", "Otto", "drifted apart", "Hazel's Bakery", "mend_fallout"),
        ]

        output = {
            "game": "Gacho Badi (Goose Buddy)",
            # web/game.js drives its scene entirely off this array (each
            # record's `meta`) plus this verb whitelist -- one source of
            # truth instead of a second copy of the allowed verbs in JS.
            "allowed_verbs": sorted(ConsistencyCriticAgent.ALLOWED_VERBS),
            "records": ContentPipeline.to_jsonable(records),
        }

        os.makedirs("output", exist_ok=True)
        out_path = os.path.join("output", "content_pipeline_run.json")
        with open(out_path, "w") as f:
            json.dump(output, f, indent=2)

        print("\n=== SUMMARY ===")
        for r in records:
            status = "passed critic" if r.passed_critic else f"corrected ({len(r.critic_violations)} issue(s))"
            print(f"  {r.content_type:22s} {status}")
        print(f"LLM provider in use  : {pipeline.llm.provider} "
              f"({'live API calls' if pipeline.llm.provider != 'mock' else 'local deterministic fallback'})")
        print(f"Full run written to  : {os.path.abspath(out_path)}")
        return 0
    except Exception as exc:  # last-resort guard: never let the pipeline crash silently
        print(f"\n[FATAL] Content pipeline failed unexpectedly: {exc!r}", file=sys.stderr)
        print("This should not happen -- please file a bug with the traceback above.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
