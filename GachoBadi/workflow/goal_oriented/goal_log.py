"""Append-only audit trail for the goal-oriented agent's own OUTER loop
(run -> verify -> adjust constraints.yaml -> repeat) -- separate from
generic/changelog.py, which logs the INNER loop's individual generate()
attempts. One JSON line per cycle: what was unresolved, what (if
anything) changed in that agent's constraints.yaml, and why.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
LOG_PATH = os.path.join(LOG_DIR, "goal_log.jsonl")


def append_goal_log(entry: dict, log_path: str = LOG_PATH) -> dict:
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    record = {"timestamp": datetime.now(timezone.utc).isoformat(), **entry}
    with open(log_path, "a") as f:
        f.write(json.dumps(record) + "\n")
    return record


def read_goal_log(log_path: str = LOG_PATH):
    if not os.path.exists(log_path):
        return []
    with open(log_path) as f:
        return [json.loads(line) for line in f if line.strip()]


def clear_goal_log(log_path: str = LOG_PATH) -> None:
    if os.path.exists(log_path):
        os.remove(log_path)
