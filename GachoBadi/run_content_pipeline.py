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

from agents.dynamic_content.consistency_critic_agent import ConsistencyCriticAgent
from content_pipeline import ContentPipeline


def main() -> int:
    print("Gacho Badi (Goose Buddy) -- Dynamic Content Pipeline (Assignment #4)")
    print("=" * 70)
    try:
        pipeline = ContentPipeline(gdd_path="gdd.txt", seed=7)
        print(f"Knowledge base loaded: {len(pipeline.kb.chunks)} chunks from gdd.txt")

        item_record = pipeline.generate_item_affordance("a lost memento", "memento")
        backstory_record = pipeline.generate_relationship_backstory("Hazel", "Otto", "drifted apart")
        # Chains the item agent's own output into the task premise call
        # (instead of a second, independent "a lost memento" literal) so
        # the task's goose-verb steps target the actual generated item.
        task_record = pipeline.generate_task_premise(
            "Hazel", "Otto", "drifted apart", "Hazel's Bakery", "mend_fallout",
            item_name=item_record.meta["item_name"],
        )

        # A second, independently-authored task -- different item, different
        # connection kind, different pair -- so the catalog-level critic
        # check below has more than one task to compare (Cycle 2: a
        # single-task check can't see redundancy that only shows up once
        # the catalog is read as a whole).
        second_item_record = pipeline.generate_item_affordance("a chipped garden trowel", "garden tool")
        second_task_record = pipeline.generate_task_premise(
            "Vic", "Hazel", "close friends", "Garden Hose Stand", "welcome_isolated",
            item_name=second_item_record.meta["item_name"],
        )

        catalog_violations = pipeline.check_catalog([task_record, second_task_record])

        records = [item_record, backstory_record, task_record, second_item_record, second_task_record]

        output = {
            "game": "Gacho Badi (Goose Buddy)",
            # web/game.js drives its scene entirely off this array (each
            # record's `meta`) plus this verb whitelist -- one source of
            # truth instead of a second copy of the allowed verbs in JS.
            "allowed_verbs": sorted(ConsistencyCriticAgent.ALLOWED_VERBS),
            "records": ContentPipeline.to_jsonable(records),
            "catalog_check": {
                "checked_tasks": [r.meta.get("connection_kind") for r in (task_record, second_task_record)],
                "violations": catalog_violations,
            },
        }

        os.makedirs("output", exist_ok=True)
        out_path = os.path.join("output", "content_pipeline_run.json")
        with open(out_path, "w") as f:
            json.dump(output, f, indent=2)

        print("\n=== SUMMARY ===")
        for r in records:
            status = "passed critic" if r.passed_critic else f"corrected ({len(r.critic_violations)} issue(s))"
            print(f"  {r.content_type:22s} {status}")
        catalog_status = "clean" if not catalog_violations else f"{len(catalog_violations)} issue(s)"
        print(f"  {'catalog check':22s} {catalog_status}")
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
