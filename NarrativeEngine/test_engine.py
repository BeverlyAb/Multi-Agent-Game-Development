#!/usr/bin/env python3
"""Test script for Narrative Engine"""
import sys
import json

# Add narrative engine to path
sys.path.insert(0, '/mnt/c/Users/N_TAIL_COMP0/Desktop/Code/MultiAgentGameDevelopment/Multi-Agent-Game-Development/NarrativeEngine')

from narrative_engine import NarrativeEngine

print("Testing Narrative Engine...")

# Create engine
engine = NarrativeEngine()

# Start interactive session
engine.start_session()