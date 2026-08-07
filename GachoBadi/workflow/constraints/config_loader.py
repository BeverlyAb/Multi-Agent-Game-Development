"""Loads a per-agent YAML config -- the declarative half of a constraint
file (token_budget, priority_weights, max_retries), kept separate from
the Python half (gap_detectors) that needs real logic and reads this
config in.

Uses PyYAML when installed (full YAML syntax, including comments).
Falls back to a small hand-rolled parser for the flat / one-level-nested
subset this project's own configs actually use, so the workflow package
still runs with zero setup on a machine without PyYAML -- the same
"always produces output, no third-party package required" guarantee
api/llm_client.py makes for its own provider fallback.
"""
from __future__ import annotations

from typing import Any, Dict

try:
    import yaml  # type: ignore

    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False


def _parse_scalar(text: str) -> Any:
    text = text.strip()
    if text.lower() in ("true", "false"):
        return text.lower() == "true"
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        pass
    return text.strip('"').strip("'")


def _minimal_yaml_parse(text: str) -> Dict[str, Any]:
    """NOT a general YAML parser -- handles exactly the subset this
    project's constraint configs use: top-level keys, at most one level
    of nested 'key:' mapping, scalar values, '#' comments. If a config
    ever needs lists or deeper nesting, install PyYAML rather than
    extending this."""
    root: Dict[str, Any] = {}
    stack = [(0, root)]
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        key, _, value = line.strip().partition(":")
        value = value.strip()
        while len(stack) > 1 and indent < stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if value == "":
            child: Dict[str, Any] = {}
            parent[key] = child
            stack.append((indent + 1, child))
        else:
            parent[key] = _parse_scalar(value)
    return root


def load_constraint_config(path: str) -> Dict[str, Any]:
    with open(path) as f:
        text = f.read()
    if _HAS_YAML:
        return yaml.safe_load(text) or {}
    return _minimal_yaml_parse(text)
