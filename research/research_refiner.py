class ResearchRefiner:
    def __init__(self, model_interface):
        self.model = model_interface
    
    async def refine_research(self, original_query, current_context, learnings, directions):
        """Determine the next research direction based on findings."""
        prompt = f"""
        Based on the original research query, current context, and recent findings,
        determine the most promising direction to continue this research.
        
        ORIGINAL QUERY:
        {original_query}
        
        CURRENT RESEARCH CONTEXT:
        {current_context}
        
        KEY LEARNINGS SO FAR:
        {", ".join(learnings)}
        
        POSSIBLE NEXT DIRECTIONS:
        {", ".join(directions)}
        
        OUTPUT FORMAT:
        NEXT DIRECTION: [Clear statement of the next research direction]
        REASONING: [Brief explanation of why this direction is valuable]
        SPECIFIC GOAL: [Specific information to look for]
        """
        
        response = await self.model.generate(prompt)
        
        # Parse the response to extract the next direction
        next_direction = ""
        reasoning = ""
        goal = ""
        
        for line in response.split("\n"):
            if line.startswith("NEXT DIRECTION:"):
                next_direction = line.replace("NEXT DIRECTION:", "").strip()
            elif line.startswith("REASONING:"):
                reasoning = line.replace("REASONING:", "").strip()
            elif line.startswith("SPECIFIC GOAL:"):
                goal = line.replace("SPECIFIC GOAL:", "").strip()
        
        return {
            "direction": next_direction,
            "reasoning": reasoning,
            "goal": goal
        }