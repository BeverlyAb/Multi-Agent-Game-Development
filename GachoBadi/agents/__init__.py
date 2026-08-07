"""Every agent this project defines, one file per agent, grouped by when
it runs:

- agents/runtime/      -- the seven Runtime Gameplay Agents from gdd.txt's
  AI Architecture section (Assignment #3's crew; see ../crew.py). The
  original 8-agent list didn't track how residents felt about each other
  and didn't guarantee a task was actually solvable with the goose's own
  moves -- Relationship Agent and Goose Solution Planner Agent close
  those two gaps, borrowed respectively from this repo's Tomodachi Life
  and Untitled Goose Game reference crews.
- agents/dev_time/      -- the four Dev-Time Content Pipeline agents
  (Scene Orchestrator and its three sub-agents), used to author the fixed
  residents, buildings, and island layout before the game ships.
- agents/dynamic_content/ -- the four agents for Assignment #4's Dynamic
  Content Pipeline (see ../content_pipeline.py). Three are adapted from
  UntitledGooseGame_Multi_Agent's own agents, each pointed at a real gap
  between the GDD and this crew's code; the fourth, the Consistency
  Critic Agent, exists because that borrowing is itself a tone/lore risk.

agents/base.py holds the one BaseAgent shape every agent in every
subpackage shares.
"""
