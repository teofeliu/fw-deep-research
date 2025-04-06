class ResearchCoordinator:
    def __init__(self, query_generator, web_searcher, content_processor, research_refiner, report_generator):
        self.query_generator = query_generator
        self.web_searcher = web_searcher
        self.content_processor = content_processor
        self.research_refiner = research_refiner
        self.report_generator = report_generator
        
        self.all_learnings = []
        self.all_sources = []
    
    async def conduct_research(self, query, depth=3, breadth=3):
        """Conduct iterative research on a topic."""
        original_query = query
        current_context = f"Initial research query: {query}"
        research_iterations = []
        
        for iteration in range(depth):
            print(f"Research iteration {iteration+1}/{depth}...")
            
            # Generate search queries
            queries = await self.query_generator.generate_queries(current_context, breadth)
            
            iteration_results = {
                "iteration": iteration + 1,
                "context": current_context,
                "queries": queries,
                "findings": []
            }
            
            # Process each query
            for q in queries:
                print(f"  Processing query: {q}")
                try:
                    search_results = await self.web_searcher.search(q)
                    print(f"    Found {len(search_results)} papers from arXiv")
                    
                    if len(search_results) == 0:
                        print(f"    WARNING: No results found for query: {q}")
                        continue
                    
                    # Print the first result title for debugging
                    if search_results:
                        print(f"    First paper: {search_results[0].get('title', 'No title')}")
                    
                    # Fetch content for each result
                    enriched_results = []
                    for result in search_results[:breadth]:  # Limit to breadth parameter
                        try:
                            content = await self.web_searcher.fetch_content(result)
                            enriched_results.append(content)
                        except Exception as e:
                            print(f"    Error fetching content: {e}")
                    
                    # Process the results
                    processed = await self.content_processor.process_search_results(
                        q, enriched_results, current_context
                    )
                    
                    self.all_learnings.extend(processed["learnings"])
                    self.all_sources.extend(processed["sources"])
                    
                    iteration_results["findings"].append({
                        "query": q,
                        "learnings": processed["learnings"],
                        "directions": processed["directions"],
                        "sources": processed["sources"]
                    })
                except Exception as e:
                    print(f"    ERROR processing query: {e}")
            
            research_iterations.append(iteration_results)
            
            # If this is the last iteration, break
            if iteration == depth - 1:
                break
                
            # Otherwise, refine research direction
            all_directions = []
            for finding in iteration_results["findings"]:
                all_directions.extend(finding["directions"])
            
            refinement = await self.research_refiner.refine_research(
                original_query, 
                current_context,
                self.all_learnings[-10:] if len(self.all_learnings) > 10 else self.all_learnings,
                all_directions
            )
            
            # Update context for next iteration
            current_context = f"""
            Original query: {original_query}
            Current iteration: {iteration + 1}
            Recent learnings: {', '.join(self.all_learnings[-5:])}
            Next direction: {refinement['direction']}
            Goal: {refinement['goal']}
            """
        
        # Generate final report
        report = await self.report_generator.generate_report(
            original_query,
            research_iterations,
            self.all_learnings,
            self.all_sources
        )
        
        return report