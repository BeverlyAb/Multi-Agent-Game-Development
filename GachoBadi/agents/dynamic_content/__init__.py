"""Content-generation agents for Assignment #4's Dynamic Content Pipeline
(see ../../content_pipeline.py), one per file.

Three of these four agents are deliberately adapted from
UntitledGooseGame_Multi_Agent's agents rather than written from scratch --
each one is pointed at a real gap in GachoBadi's own code (an agent the
GDD describes but agents/runtime, agents/dev_time, and crew.py never
implemented, or a field the existing agents leave empty). The fourth, the
Consistency Critic Agent, exists because that borrowing is itself a risk:
Untitled Goose Game is a mischief/chaos game with a five-verb set Gacho
Badi doesn't share, so adapted content can leak the wrong tone or the
wrong verbs. See ../../Readme.md for the full mapping and a real,
reproducible catch.
"""
