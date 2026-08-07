"""Entry point for Assignment #4's Dynamic Content Pipeline.

Usage:
    python3 run_content_pipeline.py

Reads gdd.txt as the knowledge base, generates GDD-grounded content
(item affordance specs, a relationship backstory, task premises) and
runs each through the Consistency Critic Agent, then writes every output
to its own file under output/content_pipeline/ -- see build_manifest()
below for exactly what gets written and how each file is named.
No API key required -- see llm_client.py; this always produces output
via the deterministic local fallback if no provider is configured.
"""
from __future__ import annotations

import json
import os
import re
import sys

from agents.dynamic_content.consistency_critic_agent import ConsistencyCriticAgent
from content_pipeline import ContentPipeline

OUTPUT_DIR = os.path.join("output", "content_pipeline")


def slugify(text: str, max_words: int = 4) -> str:
    """'a chipped garden trowel' -> 'a-chipped-garden'. Just enough of the
    text to make a filename self-describing when browsing the directory;
    not meant to be unique on its own (the numeric prefix handles that)."""
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())[:max_words]
    return "-".join(words) or "untitled"


def record_label(record) -> str:
    """The short, human-readable detail that makes each record's filename
    distinguishable from another record of the same content_type."""
    if record.content_type == "item_affordance":
        return record.meta.get("item_name", "item")
    if record.content_type == "relationship_backstory":
        return f"{record.meta.get('resident_a', '')}-{record.meta.get('resident_b', '')}"
    if record.content_type == "task_premise":
        return record.meta.get("connection_kind", "task")
    return record.content_type


def write_records(records) -> list:
    """Writes one JSON file per record and returns the manifest entries
    (content_type + filename) describing where each one landed."""
    manifest_entries = []
    for i, record in enumerate(records, start=1):
        filename = f"{i:02d}_{record.content_type}_{slugify(record_label(record))}.json"
        path = os.path.join(OUTPUT_DIR, filename)
        with open(path, "w") as f:
            json.dump(ContentPipeline.to_jsonable([record])[0], f, indent=2)
        manifest_entries.append({"content_type": record.content_type, "file": filename})
    return manifest_entries


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
        # check below has more than one task to compare (a single-task
        # check can't see redundancy that only shows up once the catalog
        # is read as a whole).
        second_item_record = pipeline.generate_item_affordance("a chipped garden trowel", "garden tool")
        second_task_record = pipeline.generate_task_premise(
            "Vic", "Hazel", "close friends", "Garden Hose Stand", "welcome_isolated",
            item_name=second_item_record.meta["item_name"],
        )

        catalog_violations = pipeline.check_catalog([task_record, second_task_record])
        catalog_check = {
            "checked_tasks": [r.meta.get("connection_kind") for r in (task_record, second_task_record)],
            "violations": catalog_violations,
        }

        records = [item_record, backstory_record, task_record, second_item_record, second_task_record]

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        # Remove any files left over from a previous run with a different
        # record count/order (e.g. re-running after editing this script) so
        # the directory never accumulates stale, orphaned output files.
        for existing in os.listdir(OUTPUT_DIR):
            os.remove(os.path.join(OUTPUT_DIR, existing))

        manifest_entries = write_records(records)

        catalog_check_path = os.path.join(OUTPUT_DIR, "catalog_check.json")
        with open(catalog_check_path, "w") as f:
            json.dump(catalog_check, f, indent=2)

        manifest = {
            "game": "Gacho Badi (Goose Buddy)",
            # web/game.js fetches this file first, then fetches each
            # referenced file -- one source of truth for the allowed verbs
            # and for which files exist, instead of a second copy in JS.
            "allowed_verbs": sorted(ConsistencyCriticAgent.ALLOWED_VERBS),
            "records": manifest_entries,
            "catalog_check_file": "catalog_check.json",
        }
        manifest_path = os.path.join(OUTPUT_DIR, "manifest.json")
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        print("\n=== SUMMARY ===")
        for r, entry in zip(records, manifest_entries):
            status = "passed critic" if r.passed_critic else f"corrected ({len(r.critic_violations)} issue(s))"
            print(f"  {entry['file']:55s} {status}")
        catalog_status = "clean" if not catalog_violations else f"{len(catalog_violations)} issue(s)"
        print(f"  {'catalog_check.json':55s} {catalog_status}")
        print(f"LLM provider in use  : {pipeline.llm.provider} "
              f"({'live API calls' if pipeline.llm.provider != 'mock' else 'local deterministic fallback'})")
        print(f"Manifest written to  : {os.path.abspath(manifest_path)}")
        return 0
    except Exception as exc:  # last-resort guard: never let the pipeline crash silently
        print(f"\n[FATAL] Content pipeline failed unexpectedly: {exc!r}", file=sys.stderr)
        print("This should not happen -- please file a bug with the traceback above.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
