import asyncio
import argparse
from pathlib import Path
from research.coordinator import ResearchCoordinator
from research.query_generator import QueryGenerator
from research.web_searcher import WebSearcher
from research.content_processor import ContentProcessor
from research.research_refiner import ResearchRefiner
from research.report_generator import ReportGenerator
from models.model_interface import ModelInterface
from config import DEFAULT_CONFIG

async def main():
    parser = argparse.ArgumentParser(description="AI Research Assistant")
    parser.add_argument("query", help="Research query to investigate")
    parser.add_argument("--depth", type=int, default=DEFAULT_CONFIG["default_depth"], 
                        help="Research depth - number of iterations")
    parser.add_argument("--breadth", type=int, default=DEFAULT_CONFIG["default_breadth"], 
                        help="Research breadth - queries per iteration")
    parser.add_argument("--model", choices=["scout", "maverick"], default="maverick",
                        help="LLama 4 model to use")
    parser.add_argument("--output", help="Output file for the report (markdown)")
    
    args = parser.parse_args()
    
    # Initialize model
    model_config = DEFAULT_CONFIG["models"][args.model]
    model = ModelInterface(model_config["model_id"], DEFAULT_CONFIG)
    
    # Initialize components
    query_generator = QueryGenerator(model)
    web_searcher = WebSearcher(DEFAULT_CONFIG)
    content_processor = ContentProcessor(model, DEFAULT_CONFIG)
    research_refiner = ResearchRefiner(model)
    report_generator = ReportGenerator(model)
    
    # Create coordinator
    coordinator = ResearchCoordinator(
        query_generator,
        web_searcher,
        content_processor,
        research_refiner,
        report_generator
    )
    
    print(f"Starting research on: {args.query}")
    print(f"Using model: Llama 4 {args.model.capitalize()}")
    print(f"Depth: {args.depth}, Breadth: {args.breadth}")
    
    # Conduct research
    report = await coordinator.conduct_research(args.query, args.depth, args.breadth)
    
    # Save or display report
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(report)
        print(f"Report saved to {output_path}")
    else:
        print("\n" + "="*80 + "\n")
        print(report)
        print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    asyncio.run(main())