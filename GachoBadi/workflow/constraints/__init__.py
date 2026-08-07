"""One folder per agent -- <agent>/constraints.py + <agent>/constraints.yaml
-- the agent-SPECIFIC half of the workflow (see base.py for the shared
shape every spec implements, and ../generic/guardrails.py for the
agent-AGNOSTIC half).

Each agent gets its own subpackage (e.g. goose_solution_planner/,
task_creator/, chain_reaction/) specifically so nothing here can ever be
mistaken for the actual agent module it constrains -- the full import
path, workflow.constraints.goose_solution_planner.constraints, reads
unambiguously against agents/runtime/goose_solution_planner_agent.py --
and so config_loader.py's per-file os.path.dirname(__file__) lookup for
"constraints.yaml" always finds the one file meant for that agent, never
a same-named sibling's.

Split within each pair: the .yaml holds declarative VALUES (token
budget, priority weights, max_retries); the .py holds gap-detection
LOGIC (regex extraction, word-overlap, etc.) and loads the .yaml's
values in via config_loader.py (one level up, shared by every agent's
folder). See ../README.md's "Why the YAML/Python split" for the
reasoning.

To add guardrailed verification for another agent in this crew:
  1. Create constraints/<agent>/ with an __init__.py, then copy
     goose_solution_planner/constraints.{py,yaml} (if that agent calls
     self.llm.generate() -- input side) or
     chain_reaction/constraints.{py,yaml} (if it doesn't -- output side,
     via ../generic/guarded_output.py) into it as a template.
  2. In constraints.yaml: set token_budget from gdd.txt's Technical
     Strategy table, and any priority_weights that need to outrank the
     default.
  3. In constraints.py: write gap_detectors -- functions of (output_text,
     context) -> List[Finding] that check things ONLY true for that
     agent's domain. Don't override priority_score() in Python unless a
     rule needs ranking logic a flat weight table can't express. Import
     shared pieces with three dots (from ...generic.guardrails import
     TokenBudget, from ..base import AgentConstraints, etc.) -- one more
     level than a flat file would need, since each agent now sits in its
     own subfolder.
  4. Wrap that agent's LLMClient with GuardedLLMClient(base,
     constraints=...), or call verify_output() on its return value --
     either way, no change to the agent's own file.
"""
