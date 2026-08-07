"""Append-only audit trail: one JSON line per generate() attempt any
GuardedLLMClient makes, recording what was accepted/rejected and why.
Generic by construction -- it logs whatever CallRecord it's given, with
no knowledge of which agent or domain produced it.
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict
from datetime import datetime, timezone

from .verification_models import CallRecord

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
LOG_PATH = os.path.join(LOG_DIR, "changelog.jsonl")


def _justify(record: CallRecord) -> str:
    """One human-readable sentence explaining why this attempt was
    accepted or retried -- the "justification" half of the changelog,
    not just a pass/fail bit."""
    if record.accepted:
        if record.attempt == 1:
            return "accepted on first attempt: no blocking guardrail violations or findings"
        return f"accepted on attempt {record.attempt}: prior attempt's blocking issues were resolved"
    issues = record.blocking_issues()
    return f"retrying (attempt {record.attempt} rejected): " + "; ".join(issues)


def append_changelog(record: CallRecord, log_path: str = LOG_PATH) -> dict:
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent": record.agent_name,
        "call_id": record.call_id,
        "attempt": record.attempt,
        "accepted": record.accepted,
        "justification": _justify(record),
        "input_tokens_est": record.input_tokens_est,
        "output_tokens_est": record.output_tokens_est,
        "guardrail_violations": [asdict(v) for v in record.guardrail_violations],
        "findings": [asdict(f) for f in record.findings],
        "output_preview": record.output[:200],
    }
    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def read_changelog(log_path: str = LOG_PATH):
    if not os.path.exists(log_path):
        return []
    with open(log_path) as f:
        return [json.loads(line) for line in f if line.strip()]


def clear_changelog(log_path: str = LOG_PATH) -> None:
    if os.path.exists(log_path):
        os.remove(log_path)
