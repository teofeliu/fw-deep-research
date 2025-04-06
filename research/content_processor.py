class ContentProcessor:
    def __init__(self, model_interface, config):
        self.model = model_interface
        self.config = config
    
    async def process_search_results(self, query, results, context):
        """Process search results to extract key learnings and new directions."""
        content_items = []
        
        # Combine content from results, respecting max length
        max_length = self.config.get("max_content_length", 15000)
        total_length = 0
        
        for result in results:
            if "content" in result and result["content"]:
                excerpt = result["content"][:2000]  # Limit each result
                if total_length + len(excerpt) <= max_length:
                    content_items.append(f"Source: {result['url']}\nTitle: {result['title']}\n\n{excerpt}\n")
                    total_length += len(excerpt)
        
        combined_content = "\n---\n".join(content_items)
        
        prompt = f"""
        Based on the following search results for the query "{query}" and the current research context,
        identify:
        1. Key learnings and facts that address the research goals
        2. New research directions or questions to explore further
        
        CURRENT RESEARCH CONTEXT:
        {context}
        
        SEARCH RESULTS:
        {combined_content}
        
        OUTPUT FORMAT:
        LEARNINGS:
        - [Key learning 1]
        - [Key learning 2]
        ...
        
        NEW DIRECTIONS:
        - [New research direction/question 1]
        - [New research direction/question 2]
        ...
        """
        
        response = await self.model.generate(prompt)
        
        # Parse response to extract learnings and directions
        learnings = []
        directions = []
        
        current_section = None
        
        for line in response.split("\n"):
            if "LEARNINGS:" in line:
                current_section = "learnings"
            elif "NEW DIRECTIONS:" in line:
                current_section = "directions"
            elif line.strip().startswith("- ") and current_section:
                item = line.strip()[2:].strip()
                if current_section == "learnings":
                    learnings.append(item)
                else:
                    directions.append(item)
        
        return {
            "learnings": learnings,
            "directions": directions,
            "sources": [r.get("url") for r in results if "url" in r]
        }