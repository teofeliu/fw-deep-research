class QueryGenerator:
    def __init__(self, model_interface):
        self.model = model_interface
    
    async def generate_queries(self, context, breadth=3):
        """Generate search queries based on research context."""
        prompt = f"""
        Based on the following research context, generate {breadth} specific search queries 
        for searching academic papers on arXiv. These should be concise search terms without any 
        formatting, explanations, or special characters.

        RESEARCH CONTEXT:
        {context}
        
        GUIDELINES FOR ARXIV SEARCH QUERIES:
        1. Keep queries short and focused (3-7 words)
        2. Use quotes for exact phrases, e.g., "quantum computing"
        3. No asterisks, bolding, or other formatting 
        4. No explanations or descriptions
        5. Use standard arXiv search operators like AND, OR when needed
        6. Focus on technical scientific terms that would appear in academic papers
        
        EXAMPLE GOOD QUERIES:
        - quantum computing algorithms
        - "neural networks" AND optimization
        - transformer attention mechanisms
        
        OUTPUT FORMAT:
        1. [First search query]
        2. [Second search query]
        ...
        """
        
        response = await self.model.generate(prompt)
        
        # Parse response into list of queries
        queries = []
        for line in response.split("\n"):
            if line.strip() and (line.strip()[0].isdigit() and ". " in line):
                query = line.split(". ", 1)[1].strip()
                # Remove any remaining markdown formatting or explanations
                if "**" in query:
                    query = query.replace("**", "")
                if ":" in query:
                    # Take only what's before the colon if it's an explanation
                    parts = query.split(":", 1)
                    if len(parts[0].split()) < 8:  # If first part is short, it's likely a label
                        query = parts[1].strip()
                queries.append(query)
        
        return queries[:breadth]  # Ensure we only return the requested number