"""
Style Guide Refiner Agent for Gachō Badi
This agent automatically corrects content to meet style guide requirements.
"""

from crewai import Agent
from textwrap import dedent

def create_refiner_agent():
    return Agent(
        role='Style Guide Refiner',
        goal=dedent("""
            Automatically rewrite generated content to achieve a perfect 10/10 score on Gachō Badi's style guide.
            Fix any tone, vocabulary, or formatting violations identified by the Evaluator Agent.
            Ensure content maintains the game's community-oriented, cozy tone while using correct GDD terminology.
        """),
        backstory=dedent("""
            You are an expert content refiner who transforms generated text to match the specific aesthetic and 
            narrative standards of Gachō Badi. Your job is to take feedback from the Evaluator Agent and 
            automatically rewrite content to score 10/10 on all style guide rules. You must maintain the game's 
            distinctive tone while ensuring accuracy in vocabulary and formatting.
        """),
        verbose=True,
        allow_delegation=False,
        tools=[],
        step_callback=None
    )