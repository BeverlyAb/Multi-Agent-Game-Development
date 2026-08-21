"""
Integration demonstration showing how Style Guide Agent works in the pipeline.
"""

# Simulate content from NPC Dialogue Agent that needs to be checked
sample_npc_dialogue = "The goose loudly honked at Hazel and she jumped in surprise! 'Oh my goodness - you startled me!' she exclaimed with enthusiasm."

def demonstrate_pipeline_integration():
    print("=== Pipeline Integration Demo ===\n")
    
    print("1. Content from NPC Dialogue Agent:")
    print(f"   {sample_npc_dialogue}\n")
    
    print("2. Evaluator Agent Analysis:")
    print("   The evaluator would analyze this content against GDD rules...")
    print("   SCORE: 3/10")
    print("   REASON: Tone violation - overly enthusiastic dialogue ('Oh my goodness', 'exclaimed with enthusiasm') is inconsistent with GDD's 'dry and understated' tone. Also lacks proper GDD-specific references to Hazel as a baker.\n")
    
    print("3. Refiner Agent Transformation:")
    print("   The refiner uses evaluator feedback to rewrite content:")
    print("   'The goose honked near Hazel by the bakery. She looked up, recognized the goose, and gave a small nod in acknowledgment.'\n")
    
    print("4. Final Result:")
    print("   Content now scores 10/10 on GDD style guide rules")
    print("   - Maintains cozy, community-oriented tone")
    print("   - Uses specific character reference (Hazel the baker)")
    print("   - Follows proper GDD formatting conventions")

if __name__ == "__main__":
    demonstrate_pipeline_integration()