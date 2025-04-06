import streamlit as st
import asyncio
import os
from pathlib import Path
import json
import time
from research.coordinator import ResearchCoordinator
from research.query_generator import QueryGenerator
from research.web_searcher import WebSearcher
from research.content_processor import ContentProcessor
from research.research_refiner import ResearchRefiner
from research.report_generator import ReportGenerator
from models.model_interface import ModelInterface
from config import DEFAULT_CONFIG

# Page configuration
st.set_page_config(
    page_title="ArXiv Research Assistant",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a cleaner look and animated spinner
st.markdown("""
<style>
    .current-step {
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
        border-left: 4px solid #4b6fff;
        background-color: rgba(75, 111, 255, 0.1);
    }
    .progress-step {
        padding: 8px;
        border-radius: 4px;
        margin: 5px 0;
        border-left: 3px solid #4b6fff;
        background-color: rgba(75, 111, 255, 0.05);
    }
    .paper-card {
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 15px;
        border: 1px solid rgba(128, 128, 128, 0.2);
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .query {
        font-weight: bold;
    }
    .learning {
        margin: 5px 0;
        padding-left: 20px;
    }
    .source {
        font-size: 0.8em;
        color: #4b6fff;
    }
    .stExpander {
        border: none !important;
        box-shadow: none !important;
    }
    
    /* Animated spinner */
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    .spinner {
        display: inline-block;
        width: 18px;
        height: 18px;
        border: 3px solid rgba(75, 111, 255, 0.3);
        border-radius: 50%;
        border-top: 3px solid #4b6fff;
        animation: spin 1s linear infinite;
        margin-right: 10px;
        vertical-align: middle;
    }
    .active-process {
        display: flex;
        align-items: center;
        padding: 12px 15px;
        border-radius: 5px;
        background-color: rgba(75, 111, 255, 0.1);
        margin-bottom: 15px;
        line-height: 1.4;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state variables
if 'research_complete' not in st.session_state:
    st.session_state.research_complete = False
if 'report' not in st.session_state:
    st.session_state.report = ""
if 'progress' not in st.session_state:
    st.session_state.progress = []
if 'iterations' not in st.session_state:
    st.session_state.iterations = []
if 'api_key' not in st.session_state:
    st.session_state.api_key = os.environ.get("FIREWORKS_API_KEY", "")
if 'current_step' not in st.session_state:
    st.session_state.current_step = ""
if 'research_running' not in st.session_state:
    st.session_state.research_running = False
if 'paper_details' not in st.session_state:
    st.session_state.paper_details = {}

# Header
st.title("🔬 ArXiv Research Assistant")
st.markdown("Powered by Fireworks AI and Llama 4 models")

# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    
    # API Key input
    api_key = st.text_input("Fireworks API Key", value=st.session_state.api_key, type="password")
    st.session_state.api_key = api_key
    
    # Model selection
    model_option = st.selectbox(
        "Select Model",
        ["Llama 4 Maverick", "Llama 4 Scout", "Other (Custom)"]
    )
    
    if model_option == "Other (Custom)":
        custom_model = st.text_input("Enter model name", value="llama-v3-70b-instruct")
        model_id = f"accounts/fireworks/models/{custom_model}"
    elif model_option == "Llama 4 Maverick":
        model_id = "accounts/fireworks/models/llama4-maverick-instruct-basic"
    else:  # Llama 4 Scout
        model_id = "accounts/fireworks/models/llama4-scout-instruct-basic"
    
    st.markdown(f"**Selected model:** `{model_id}`")
    
    # Research parameters
    st.subheader("Research Parameters")
    depth = st.slider("Research Depth", min_value=1, max_value=5, value=2, 
                    help="Number of research iterations")
    breadth = st.slider("Research Breadth", min_value=1, max_value=5, value=3,
                     help="Number of queries per iteration")
    
    # Parameter explanations
    with st.expander("What do these parameters mean?"):
        st.markdown("""
        **Research Depth**: The number of research iterations to perform. Each iteration refines understanding and explores new directions based on previous findings.
        
        **Research Breadth**: The number of different queries to explore in each iteration, and how many papers to analyze per query.
        
        Higher values provide more comprehensive research but take longer to complete.
        """)
    
    # About section
    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    This research assistant performs in-depth academic research by searching arXiv papers, 
    extracting key insights, and synthesizing findings into a comprehensive report.
    """)

# Main content area
query = st.text_area("Enter your research topic", height=100, 
                    placeholder="e.g., 'Recent advances in transformer architecture efficiency'")

# Check if API key is provided
if not api_key:
    st.warning("Please enter your Fireworks API key in the sidebar to proceed.")

# Create a placeholder for the current step display
current_step_placeholder = st.empty()

# Start research button
start_button = st.button("Start Research", disabled=(not api_key or not query))

# Define the research process
async def run_research(query, model_id, depth, breadth):
    # Reset state
    st.session_state.research_complete = False
    st.session_state.report = ""
    st.session_state.progress = []
    st.session_state.iterations = []
    st.session_state.research_running = True
    st.session_state.paper_details = {}
    
    # Update config with API key
    config = DEFAULT_CONFIG.copy()
    config["fireworks_api_key"] = api_key
    
    # Add progress update and update the current step display
    def add_progress(message, detail=None):
        timestamp = time.strftime('%H:%M:%S')
        full_message = f"{timestamp} - {message}"
        st.session_state.progress.append(full_message)
        st.session_state.current_step = message
        
        # Update the current step display with more detailed information
        current_step_placeholder.markdown(
            f"""<div class="active-process">
                <div class="spinner"></div>
                <div>{message}{f"<br><small>{detail}</small>" if detail else ""}</div>
               </div>""", 
            unsafe_allow_html=True
        )
    
    try:
        # Initialize model with research-specific explanation
        add_progress(
            f"Initializing {model_option} for research on '{query}'", 
            f"Setting up a powerful LLM ({model_id.split('/')[-1]}) to help analyze academic papers and generate insights."
        )
        model = ModelInterface(model_id, config)
        
        # Initialize components
        add_progress(
            "Preparing research framework", 
            f"Creating a multi-stage research pipeline with {depth} iterations, each exploring {breadth} different aspects of the topic."
        )
        
        query_generator = QueryGenerator(model)
        web_searcher = WebSearcher(config)
        content_processor = ContentProcessor(model, config)
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
        
        # Override the conduct_research method to capture progress
        async def conduct_research_with_updates(query, depth=depth, breadth=breadth):
            original_query = query
            current_context = f"Initial research query: {query}"
            research_iterations = []
            
            for iteration in range(depth):
                iteration_data = {
                    "iteration": iteration + 1,
                    "context": current_context,
                    "queries": [],
                    "findings": []
                }
                
                add_progress(
                    f"Starting research iteration {iteration+1}/{depth} on '{query}'", 
                    f"Each iteration builds upon previous findings to explore the topic more deeply. We're now in iteration {iteration+1}."
                )
                
                # Generate search queries
                add_progress(
                    f"Generating specialized search queries for '{query}'", 
                    f"Creating {breadth} targeted academic search terms to find the most relevant papers on arXiv."
                )
                queries = await query_generator.generate_queries(current_context, breadth)
                iteration_data["queries"] = queries
                
                # Process each query
                for query_index, q in enumerate(queries):
                    add_progress(
                        f"Searching arXiv for papers on: '{q}'", 
                        f"Query {query_index+1}/{len(queries)} - Searching academic database for relevant research papers."
                    )
                    try:
                        search_results = await web_searcher.search(q)
                        
                        if len(search_results) == 0:
                            add_progress(
                                f"No papers found for '{q}'", 
                                "Moving to next query to find more relevant research."
                            )
                            continue
                        
                        papers_info = f"Found {len(search_results)} papers including: "
                        papers_info += ", ".join([f"'{result.get('title', 'Untitled')}'" for result in search_results[:3]])
                        if len(search_results) > 3:
                            papers_info += f" and {len(search_results)-3} more"
                        
                        add_progress(
                            f"Found {len(search_results)} relevant papers on '{q}'", 
                            papers_info
                        )
                        
                        # Store paper titles for later reference
                        st.session_state.paper_details[q] = [
                            {
                                "title": result.get('title', 'Untitled'),
                                "authors": result.get('authors', []),
                                "year": result.get('published', '')[:4] if result.get('published') else 'Unknown'
                            }
                            for result in search_results[:breadth]
                        ]
                        
                        # Fetch content for each result
                        enriched_results = []
                        for i, result in enumerate(search_results[:breadth]):
                            try:
                                paper_title = result.get('title', 'Untitled')
                                paper_authors = ", ".join(result.get('authors', []))[:50]
                                if paper_authors and len(result.get('authors', [])) > 2:
                                    paper_authors += f" et al."
                                
                                add_progress(
                                    f"Analyzing paper ({i+1}/{min(breadth, len(search_results))}): '{paper_title}'", 
                                    f"Authors: {paper_authors} | Reading and extracting key insights from this academic paper."
                                )
                                content = await web_searcher.fetch_content(result)
                                enriched_results.append(content)
                            except Exception as e:
                                add_progress(f"Error processing paper: {str(e)}")
                        
                        # Process the results
                        add_progress(
                            f"Synthesizing findings from {len(enriched_results)} papers on '{q}'", 
                            f"Identifying key concepts, extracting insights, and connecting information across multiple academic sources."
                        )
                        processed = await content_processor.process_search_results(
                            q, enriched_results, current_context
                        )
                        
                        # Show a sample of what was found
                        if processed["learnings"]:
                            learning_sample = processed["learnings"][0]
                            add_progress(
                                f"Found key insight about '{q}'", 
                                f"Example finding: {learning_sample}"
                            )
                        
                        coordinator.all_learnings.extend(processed["learnings"])
                        coordinator.all_sources.extend(processed["sources"])
                        
                        finding_data = {
                            "query": q,
                            "learnings": processed["learnings"],
                            "directions": processed["directions"],
                            "sources": processed["sources"]
                        }
                        
                        iteration_data["findings"].append(finding_data)
                        
                    except Exception as e:
                        add_progress(f"ERROR processing query: {str(e)}")
                
                research_iterations.append(iteration_data)
                st.session_state.iterations.append(iteration_data)
                
                # If this is the last iteration, break
                if iteration == depth - 1:
                    break
                    
                # Otherwise, refine research direction
                all_directions = []
                for finding in iteration_data["findings"]:
                    all_directions.extend(finding["directions"])
                
                add_progress(
                    f"Refining research focus for iteration {iteration+2}", 
                    f"Based on {len(coordinator.all_learnings)} insights gathered so far, determining most promising directions to explore next."
                )
                refinement = await research_refiner.refine_research(
                    original_query, 
                    current_context,
                    coordinator.all_learnings[-10:] if len(coordinator.all_learnings) > 10 else coordinator.all_learnings,
                    all_directions
                )
                
                # Update context for next iteration
                current_context = f"""
                Original query: {original_query}
                Current iteration: {iteration + 1}
                Recent learnings: {', '.join(coordinator.all_learnings[-5:])}
                Next direction: {refinement['direction']}
                Goal: {refinement['goal']}
                """
                
                add_progress(
                    f"New research direction identified", 
                    f"Next focus area: {refinement['direction']}"
                )
            
            # Generate final report
            total_papers = sum(len(findings.get("sources", [])) for iteration in research_iterations for findings in iteration.get("findings", []))
            add_progress(
                f"Generating comprehensive research report on '{query}'", 
                f"Synthesizing {len(coordinator.all_learnings)} key findings from approximately {total_papers} academic papers across {depth} research iterations."
            )
            report = await report_generator.generate_report(
                original_query,
                research_iterations,
                coordinator.all_learnings,
                coordinator.all_sources
            )
            
            return report
        
        # Replace the method
        coordinator.conduct_research = conduct_research_with_updates
        
        # Start research
        add_progress(
            f"Beginning comprehensive research on '{query}'", 
            f"Using {model_option} to explore academic literature with {depth} iterations and {breadth} queries per iteration."
        )
        report = await coordinator.conduct_research(query, depth, breadth)
        
        # Store the final report
        st.session_state.report = report
        st.session_state.research_complete = True
        
        # Count total papers and findings
        total_papers = sum(len(findings.get("sources", [])) for iteration in st.session_state.iterations for findings in iteration.get("findings", []))
        total_learnings = len(coordinator.all_learnings)
        
        add_progress(
            f"Research complete on '{query}'!", 
            f"Analyzed {total_papers} papers across {depth} iterations, extracting {total_learnings} key insights."
        )
        
        # Update the current step display to show completion
        current_step_placeholder.markdown(
            f"""<div class="active-process" style="background-color: rgba(40, 167, 69, 0.1); border-left: 4px solid #28a745;">
                <div>✅ Research complete on '{query}'!<br>
                <small>Analyzed {total_papers} papers across {depth} iterations, extracting {total_learnings} key insights.</small></div>
               </div>""", 
            unsafe_allow_html=True
        )
        
    except Exception as e:
        error_message = f"ERROR: {str(e)}"
        add_progress(error_message)
        
        # Update the current step display to show error
        current_step_placeholder.markdown(
            f"""<div class="active-process" style="background-color: rgba(220, 53, 69, 0.1); border-left: 4px solid #dc3545;">
                <div>❌ {error_message}</div>
               </div>""", 
            unsafe_allow_html=True
        )
    
    finally:
        st.session_state.research_running = False

# Execute research when button is clicked
if start_button:
    if api_key and query:
        # Display initial processing message
        current_step_placeholder.markdown(
            f"""<div class="active-process">
                <div class="spinner"></div>
                <div>Initializing research on '{query}'...<br>
                <small>Preparing to explore academic literature using {model_option}.</small></div>
               </div>""", 
            unsafe_allow_html=True
        )
        # Run the async function without using st.spinner
        asyncio.run(run_research(query, model_id, depth, breadth))

# Display collapsible progress history
if st.session_state.progress:
    with st.expander("Show detailed research log", expanded=False):
        for step in st.session_state.progress:
            st.markdown(f"<div class='progress-step'>{step}</div>", unsafe_allow_html=True)

# Display iterations with paper details
if st.session_state.iterations:
    for i, iteration in enumerate(st.session_state.iterations):
        with st.expander(f"Iteration {iteration['iteration']} Results", expanded=False):
            st.markdown(f"**Queries explored in this iteration:**")
            for q in iteration['queries']:
                st.markdown(f"- {q}")
            
            st.markdown("---")
            
            for finding in iteration["findings"]:
                st.markdown(f"<div class='paper-card'>", unsafe_allow_html=True)
                st.markdown(f"<p class='query'>Query: {finding['query']}</p>", unsafe_allow_html=True)
                
                # Show papers analyzed for this query
                if finding['query'] in st.session_state.paper_details:
                    papers = st.session_state.paper_details[finding['query']]
                    if papers:
                        st.markdown("**Papers analyzed:**")
                        for paper in papers:
                            authors = paper.get('authors', [])
                            if len(authors) > 2:
                                author_text = f"{authors[0]} et al."
                            else:
                                author_text = ", ".join(authors)
                            
                            st.markdown(f"- **{paper['title']}** ({paper['year']}) - {author_text}")
                
                if finding["learnings"]:
                    st.markdown("**Key Insights:**")
                    for learning in finding["learnings"]:
                        st.markdown(f"<p class='learning'>• {learning}</p>", unsafe_allow_html=True)
                
                if finding["sources"]:
                    st.markdown("**Sources:**")
                    for source in finding["sources"]:
                        st.markdown(f"<p class='source'>{source}</p>", unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)

# Display final report
if st.session_state.research_complete:
    with st.expander("Final Research Report", expanded=True):
        st.markdown(st.session_state.report)