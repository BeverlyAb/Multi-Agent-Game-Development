"""
Style Guide Evaluator Agent for Gachō Badi
This agent evaluates generated content against the game's style guide rules.
"""

from crewai import Agent
from textwrap import dedent

def create_evaluator_agent():
    return Agent(
        role='Style Guide Evaluator',
        goal=dedent("""
            Analyze generated content against Gachō Badi's specific tone, vocabulary, and formatting conventions.
            Determine if content adheres to the community-oriented, cozy tone where the goose is a quiet community-builder 
            rather than mischief-maker. Check for accurate use of GDD-established terms and proper formatting conventions.
        """),
        backstory=dedent("""
            You are an expert evaluator who ensures all game content maintains consistency with Gachō Badi's unique 
            community-building narrative. Your job is to catch any violations of the specific tone, vocabulary, and 
            formatting conventions described in the GDD. You must be able to distinguish between different types of 
            violations (tone, vocabulary, format) and provide specific feedback.
        """),
        verbose=True,
        allow_delegation=False,
        tools=[],
        step_callback=None
    )