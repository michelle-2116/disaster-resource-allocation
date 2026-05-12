import os
import sys
import json
import logging
import re
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from .tools import fetch_combined_disaster_news, format_articles_for_analysis
from .tool_definitions import (
    get_verified_news_tool_definition,
    execute_verified_news_tool,
    format_verified_news_as_json
)
from .allocator_config import GEMINI_MODEL

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("AGENT")

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY not found in .env file")
    print("Please create a .env file with your API keys (see .env.example)")
    sys.exit(1)

logger.info("Initializing Gemini client...")
client = genai.Client(api_key=GEMINI_API_KEY)
logger.info("Gemini client initialized successfully")


SYSTEM_PROMPT = """You are a CRISIS ANALYST. Analyze the incident data provided and call the verified_news tool to report your findings.

IMPORTANT: You MUST call the verified_news tool for EACH distinct incident you find in the provided news data. Do not combine multiple incidents into one tool call.

Be accurate. Use only information from the provided sources. Rate severity on a 1-10 scale where 1=minor, 10=catastrophic.

Always call the verified_news tool with your analysis. Do not generate JSON text - use the tool function calling."""


def create_disaster_agent():
    """
    Create and configure the Gemini-based disaster news analysis agent.
    
    Returns:
        Configured Gemini client instance
    """
    return client


def analyze_disaster(disaster_query: str, agent_client, demo_mode: bool = False, incident_name: str = None) -> dict:
    """
    Analyze a disaster and return structured incident report(s).
    
    Args:
        disaster_query: User's query about a disaster (e.g., "us iran war")
        agent_client: Configured Gemini client instance
        demo_mode: If True, only fetch from demo RSS feed
        incident_name: Optional incident name to generate consistent incident_id
    
    Returns:
        Dictionary with verified incident report, or list of reports if multiple tool calls
    """
    logger.info(f"Processing query: '{disaster_query}' (demo_mode={demo_mode}, incident_name={incident_name})")
    print()
    
    # Fetch the latest news
    logger.info("Starting news fetch from sources...")
    fetch_start = datetime.now()
    combined_data = fetch_combined_disaster_news(disaster_query, demo_mode=demo_mode)
    fetch_duration = (datetime.now() - fetch_start).total_seconds()
    
    # Log detailed fetch results
    gdelt_count = len(combined_data.get("gdelt_data", {}).get("articles", []))
    exa_count = len(combined_data.get("exa_data", {}).get("articles", []))
    rss_count = len(combined_data.get("rss_data", {}).get("articles", []))
    total_count = combined_data.get("combined_article_count", 0)
    
    logger.info(f"News fetch completed in {fetch_duration:.2f}s")
    logger.info(f"GDELT results: {gdelt_count} articles")
    logger.info(f"EXA results: {exa_count} articles")
    logger.info(f"RSS results: {rss_count} articles")
    logger.info(f"Total articles for analysis: {total_count}")
    
    # Check if we found any articles
    if total_count == 0:
        logger.warning("No articles found from any source - results may be limited")
        print("Warning: No articles found. Results may be limited.")
    else:
        print(f"Found {total_count} articles ({gdelt_count} GDELT, {exa_count} EXA, {rss_count} RSS)")
    
    # Format articles for analysis
    logger.debug("Formatting articles for AI analysis...")
    formatted_articles = format_articles_for_analysis(combined_data)
    
    # Create the analysis prompt
    analysis_prompt = f"""INCIDENT DATA ANALYSIS

Query: {disaster_query}
Time: {combined_data['timestamp']}
Sources: {', '.join(combined_data.get('sources_queried', []))}
{f'Incident Name: {incident_name}' if incident_name else ''}

NEWS DATA:
{formatted_articles}

TASK: Analyze this incident data and call the verified_news tool to report your findings.

CRITICAL INSTRUCTIONS:
1. Identify ALL distinct incidents in the news data
2. For EACH incident, call the verified_news tool ONCE with complete details
3. Do NOT combine multiple incidents into a single tool call
4. Be concise and accurate
{f'5. Use incident_id format based on incident name: {incident_name.upper().replace(" ", "_")}_' + datetime.now().strftime("%Y%m%d") if incident_name else ''}"""
    
    logger.info(f"Sending data to Gemini for analysis (model: {GEMINI_MODEL})...")
    analysis_start = datetime.now()
    print("Analyzing incident...")
    
    # Get the tool definition
    tool = get_verified_news_tool_definition()
    
    # Generate analysis with tool calling
    from google.genai import types
    
    try:
        response = agent_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=analysis_prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=[tool],
                temperature=0.7,
                max_output_tokens=4000,
                top_p=0.95,
                top_k=40,
            ),
        )
        
        analysis_duration = (datetime.now() - analysis_start).total_seconds()
        logger.info(f"Response received from Gemini in {analysis_duration:.2f}s")
        
        # Handle response safely
        if response is None:
            logger.error("No response received from Gemini API")
            raise ValueError("No response received from Gemini API")
        
        # Extract tool calls from response
        if not hasattr(response, 'candidates') or not response.candidates:
            logger.error("No candidates in Gemini response")
            raise ValueError("No candidates in Gemini response")
        
        candidate = response.candidates[0]
        if not hasattr(candidate, 'content') or not candidate.content:
            logger.error("No content in candidate")
            raise ValueError("No content in candidate")
        
        # Look for function calls in parts
        tool_calls = []
        for part in candidate.content.parts:
            if hasattr(part, 'function_call') and part.function_call:
                tool_calls.append(part.function_call)
        
        if not tool_calls:
            logger.warning("No tool calls found in response")
            logger.debug(f"Response content: {candidate.content}")
            return {"error": "Model did not call verified_news tool"}
        
        logger.info(f"Found {len(tool_calls)} tool call(s) from Gemini")
        
        # Execute all tool calls and aggregate results
        verified_reports = []
        for i, func_call in enumerate(tool_calls, 1):
            logger.info(f"Processing tool call {i}/{len(tool_calls)}: {func_call.name}")
            
            if func_call.name == "verified_news":
                # Convert function call args to dict
                tool_args = {k: v for k, v in func_call.args.items()}
                logger.debug(f"Tool args: {tool_args}")
                
                # Execute the tool
                verified_report = execute_verified_news_tool(tool_args)
                verified_reports.append(verified_report)
                logger.info(f"Tool call {i} executed successfully")
        
        logger.info(f"Analysis completed: {len(verified_reports)} incident(s) reported")
        
        # Return single report or list depending on count
        if len(verified_reports) == 1:
            return verified_reports[0]
        elif len(verified_reports) > 1:
            return {"incidents": verified_reports, "timestamp": datetime.now().isoformat()}
        else:
            return {"error": "No incidents extracted from tool calls"}
    
    except Exception as e:
        logger.error(f"Error during analysis generation: {str(e)}", exc_info=True)
        raise


def main():
    """Main entry point for the disaster analysis agent."""
    logger.info("=" * 80)
    logger.info("GLOBAL DISASTER NEWS ANALYSIS AGENT - Starting")
    logger.info("Powered by Google Gemini 3.1 Flash + GDELT + EXA + RSS")
    logger.info("=" * 80)
    
    print()
    print("Global Disaster News Analysis Agent")
    print()
    
    # Create the agent
    agent_client = create_disaster_agent()
    logger.info("Agent ready for queries")
    
    # Interactive loop
    query_count = 0
    while True:
        try:
            disaster_query = input("Enter query (or 'quit' to exit): ").strip()
            
            if disaster_query.lower() in ['quit', 'exit', 'q']:
                logger.info("Agent shutdown requested")
                print("Shutting down.")
                break
            
            if not disaster_query:
                print("Please enter a valid query.")
                continue
            
            query_count += 1
            logger.info("=" * 80)
            logger.info(f"QUERY #{query_count}: {disaster_query}")
            logger.info("=" * 80)
            
            print()
            # Analyze the disaster and get verified report
            verified_report = analyze_disaster(disaster_query, agent_client)
            
            # Display verified report as JSON only
            print("="*80)
            print("VERIFIED INCIDENT REPORT")
            print("="*80)
            print()
            report_json = format_verified_news_as_json(verified_report)
            print(report_json)
            logger.info(f"Report JSON:\n{report_json}")
            print()
            print("="*80)
            print()
            
        except KeyboardInterrupt:
            logger.info("Agent interrupted by user")
            print()
            print("Interrupted. Exiting.")
            break
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}", exc_info=True)
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()
            print()
    
    logger.info("=" * 80)
    logger.info("Agent shutdown complete")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
