"""Every agent this project defines, one file per agent, grouped by when
it runs:

- agents/runtime/      -- the nine Runtime Gameplay Agents from gdd.txt's
  AI Architecture section (see ../crew.py). The original 8-agent list
  didn't track how residents felt about each other, didn't guarantee a
  task was actually solvable with the goose's own moves, and stopped at
  the goose's own action with no follow-through -- Relationship Agent,
  Goose Solution Planner Agent, and Chain Reaction Agent close those
  three gaps.
- agents/dev_time/      -- the four Dev-Time Content Pipeline agents
  (Scene Orchestrator and its three sub-agents), used to author the fixed
  residents, buildings, and island layout before the game ships.

agents/base.py holds the one BaseAgent shape every agent in every
subpackage shares.
"""
