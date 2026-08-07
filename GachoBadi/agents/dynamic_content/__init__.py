"""Content-generation agents for Assignment #4's Dynamic Content Pipeline
(see ../../content_pipeline.py), one per file.

Three of these four agents are deliberately adapted from
UntitledGooseGame_Multi_Agent's agents rather than written from scratch --
each one was originally pointed at a real gap in GachoBadi's own code (an
agent the GDD describes but agents/runtime, agents/dev_time, and crew.py
didn't implement yet, or a field the existing agents left empty). Those
specific gaps have since been closed directly in agents/runtime/ (see
../../Readme.md's Content Fit table); these agents remain for Assignment
#4's own purpose -- RAG-grounded, critic-checked content generation --
independent of the runtime crew. The fourth, the
Consistency Critic Agent, exists because that borrowing is itself a risk:
Untitled Goose Game is a mischief/chaos game with a five-verb set Gacho
Badi doesn't share, so adapted content can leak the wrong tone or the
wrong verbs. See ../../Readme.md for the full mapping and a real,
reproducible catch.
"""
