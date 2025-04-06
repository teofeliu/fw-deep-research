class ReportGenerator:
    def __init__(self, model_interface):
        self.model = model_interface
    
    async def generate_report(self, original_query, research_iterations, all_learnings, all_sources):
        """Generate a comprehensive markdown report of research findings."""
        # Prepare context for the report
        iteration_summaries = []
        
        for iteration in research_iterations:
            summary = f"## Iteration {iteration['iteration']}\n\n"
            summary += f"### Context\n{iteration['context']}\n\n"
            summary += f"### Queries\n"
            
            for q in iteration['queries']:
                summary += f"- {q}\n"
            
            summary += "\n### Key Findings\n"
            
            for finding in iteration['findings']:
                summary += f"#### From query: {finding['query']}\n"
                summary += "##### Learnings\n"
                for learning in finding['learnings']:
                    summary += f"- {learning}\n"
                
                summary += "\n"
            
            iteration_summaries.append(summary)
        
        # Deduplicate sources
        unique_sources = list(set(all_sources))
        
        # Prepare the condensed context for the LLM
        context = f"""
        Original research query: {original_query}
        
        Summary of iterations:
        {', '.join([f"Iteration {i+1}: {len(iter['findings'])} queries processed" 
                   for i, iter in enumerate(research_iterations)])}
        
        Total unique sources: {len(unique_sources)}
        Total learnings: {len(all_learnings)}
        """
        
        # Choose representative learnings if there are too many
        learning_samples = all_learnings[:50] if len(all_learnings) > 50 else all_learnings
        learning_text = "\n".join([f"- {l}" for l in learning_samples])
        
        prompt = f"""
        Create a comprehensive research report in markdown format based on the following research.
        
        RESEARCH QUERY:
        {original_query}
        
        RESEARCH CONTEXT:
        {context}
        
        KEY LEARNINGS:
        {learning_text}
        
        Generate a well-structured markdown report with the following sections:
        1. Executive Summary
        2. Key Findings
        3. Detailed Analysis
        4. Conclusions
        5. References
        
        Make the report informative, factual, and focused on the most important discoveries.
        """
        
        report_content = await self.model.generate(prompt)
        
        # Add source list to the report
        sources_section = "\n\n## Sources\n\n"
        for i, source in enumerate(unique_sources[:30]):  # Limit to first 30 sources
            sources_section += f"{i+1}. [{source}]({source})\n"
        
        if len(unique_sources) > 30:
            sources_section += f"\n... and {len(unique_sources) - 30} more sources"
        
        final_report = report_content + sources_section
        
        return final_report