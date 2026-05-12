"""
Tools for fetching real-time disaster and crisis information from GDELT, EXA, and RSS feeds.
"""

import json
import requests
import logging
from datetime import datetime, timedelta
from typing import Optional
import os
import feedparser
from .rss_fetcher import fetch_rss_feeds

logger = logging.getLogger("TOOLS")


def fetch_gdelt_news(disaster_query: str, timespan: str = "24h", max_records: int = 50) -> dict:
    """
    Fetch the latest news articles about a disaster from GDELT.
    
    GDELT (Global Event, Language, and Tone) is a real-time database monitoring world news.
    It provides access to the latest news articles indexed from thousands of sources worldwide.
    
    Args:
        disaster_query: Search query (e.g., "us iran war", "earthquake turkey", "flood pakistan")
        timespan: Time span to search within (e.g., "24h", "7d", "30d")
        max_records: Maximum number of articles to return (default: 50)
    
    Returns:
        Dictionary containing:
        - articles: List of articles with URL, title, date, source country, language
        - query: The original query
        - source: "GDELT"
        - timestamp: When the data was fetched
        - article_count: Number of articles returned
    """
    logger.info(f"GDELT: Fetching news for query '{disaster_query}' (timespan: {timespan}, max: {max_records})")
    try:
        base_url = "https://api.gdeltproject.org/api/v2/doc/doc"
        
        # Construct query with OR operators for more comprehensive results
        formatted_query = f'("{disaster_query}")'
        
        params = {
            "query": formatted_query,
            "mode": "artlist",
            "format": "json",
            "sort": "datedesc",
            "timespan": timespan,
            "maxrecords": max_records,
        }
        
        logger.debug(f"GDELT API request - URL: {base_url}, params: {params}")
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        articles = data.get("articles", [])
        
        logger.info(f"GDELT: API returned {len(articles)} raw articles")
        
        # Process and structure the articles
        processed_articles = []
        for article in articles:
            processed_articles.append({
                "title": article.get("title", ""),
                "url": article.get("url", ""),
                "source_domain": article.get("domain", ""),
                "source_country": article.get("sourcecountry", ""),
                "language": article.get("language", ""),
                "publication_date": article.get("seendate", ""),
                "image": article.get("socialimage", ""),
            })
        
        logger.info(f"GDELT: Successfully processed {len(processed_articles)} articles")
        return {
            "articles": processed_articles,
            "query": disaster_query,
            "source": "GDELT",
            "timestamp": datetime.now().isoformat(),
            "article_count": len(processed_articles),
            "timespan_searched": timespan,
            "api_url": response.url,
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"GDELT: API request failed - {str(e)}")
        return {
            "error": f"GDELT API request failed: {str(e)}",
            "query": disaster_query,
            "source": "GDELT",
            "articles": [],
        }
    except json.JSONDecodeError as e:
        logger.error(f"GDELT: Failed to parse JSON response - {str(e)}")
        return {
            "error": f"Failed to parse GDELT response: {str(e)}",
            "query": disaster_query,
            "source": "GDELT",
            "articles": [],
        }


def fetch_exa_news(disaster_query: str, num_results: int = 10) -> dict:
    """
    Fetch the latest news about a disaster from EXA search API.
    
    EXA is a high-quality search engine providing access to real-time and recent news,
    web results, and research from across the internet.
    
    Args:
        disaster_query: Search query (e.g., "us iran war latest updates")
        num_results: Number of results to return (default: 10)
    
    Returns:
        Dictionary containing:
        - articles: List of relevant search results with titles, URLs, and metadata
        - query: The original query
        - source: "EXA"
        - timestamp: When the data was fetched
        - result_count: Number of results returned
    """
    logger.info(f"EXA: Fetching news for query '{disaster_query}' (num_results: {num_results})")
    try:
        from exa_py import Exa
        
        api_key = os.getenv("EXA_API_KEY")
        if not api_key:
            logger.error("EXA: API key not found in environment")
            return {
                "error": "EXA_API_KEY not found in environment variables",
                "query": disaster_query,
                "source": "EXA",
                "articles": [],
            }
        
        logger.debug("EXA: Initializing client and making search request...")
        client = Exa(api_key=api_key)
                
        results = client.search(
            query=f"{disaster_query} latest news updates",
            category="news",
            num_results=num_results,
            type="auto"
        )
        
        logger.info(f"EXA: API returned {len(results.results)} results")
        
        processed_results = []
        for result in results.results:
            processed_results.append({
                "title": getattr(result, "title", ""),
                "url": getattr(result, "url", ""),
                "snippet": getattr(result, "text", ""),
                "published_date": getattr(result, "published_date", ""),
                "author": getattr(result, "author", ""),
                "source": getattr(result, "source", ""),
            })
        
        logger.info(f"EXA: Successfully processed {len(processed_results)} results")
        return {
            "articles": processed_results,
            "query": disaster_query,
            "source": "EXA",
            "timestamp": datetime.now().isoformat(),
            "result_count": len(processed_results),
            "used_autoprompt": True,
        }
        
    except ImportError:
        logger.error("EXA: exa-py library not installed")
        return {
            "error": "exa-py library not installed. Install with: pip install exa-py",
            "query": disaster_query,
            "source": "EXA",
            "articles": [],
        }
    except Exception as e:
        logger.error(f"EXA: API request failed - {str(e)}")
        return {
            "error": f"EXA API request failed: {str(e)}",
            "query": disaster_query,
            "source": "EXA",
            "articles": [],
        }


def fetch_demo_rss_feed(timespan: str = "7d") -> dict:
    """
    Fetch from demo RSS feed at localhost:5000/feed.xml
    Filters articles by timestamp (last 7 days by default)
    
    Args:
        timespan: Time period to fetch (e.g., "7d" for 7 days, "1d" for 1 day)
    
    Returns:
        Dictionary with same structure as fetch_rss_feeds output
    """
    from datetime import timedelta
    import email.utils
    
    logger.info(f"DEMO RSS: Fetching from localhost:5000/feed.xml (timespan={timespan})")
    try:
        response = requests.get("http://localhost:5000/feed.xml", timeout=10)
        response.raise_for_status()
        
        parsed = feedparser.parse(response.content)
        
        if parsed.bozo:
            logger.warning(f"DEMO RSS: Feed has parsing issues - {parsed.bozo_exception}")
        
        # Parse timespan
        days = int(timespan.replace('d', '')) if 'd' in timespan else 7
        cutoff_time = datetime.now() - timedelta(days=days)
        
        articles = []
        for entry in parsed.get('entries', []):
            # Parse published date
            pub_date_str = entry.get('published', '')
            try:
                if pub_date_str:
                    # Try to parse RFC 2822 format
                    pub_tuple = email.utils.parsedate_to_datetime(pub_date_str)
                    pub_date = pub_tuple.replace(tzinfo=None)
                else:
                    pub_date = datetime.now()
            except:
                pub_date = datetime.now()
            
            # Filter by timespan
            if pub_date < cutoff_time:
                logger.debug(f"DEMO RSS: Skipping article from {pub_date} (before cutoff {cutoff_time})")
                continue
            
            article = {
                'title': entry.get('title', 'No title'),
                'description': entry.get('summary', entry.get('description', 'No description'))[:300],
                'url': entry.get('link', ''),
                'published_date': entry.get('published', 'Unknown'),
                'source_domain': 'Demo RSS',
                'source_country': 'Demo',
                'feed_source': 'DEMO_RSS',
                'feed_id': 'demo_feed',
                'language': 'en'
            }
            articles.append(article)
        
        logger.info(f"DEMO RSS: Fetched {len(articles)} articles (after filtering by {timespan})")
        
        return {
            "articles": articles,
            "query": "demo",
            "source": "DEMO_RSS",
            "timestamp": datetime.now().isoformat(),
            "article_count": len(articles),
            "feeds_checked": 1,
            "feeds_matched": 1,
            "feeds_fetched": 1
        }
    
    except requests.exceptions.RequestException as e:
        logger.error(f"DEMO RSS: Failed to fetch - {str(e)}")
        return {
            "error": f"Demo RSS fetch failed: {str(e)}",
            "query": "demo",
            "source": "DEMO_RSS",
            "articles": [],
        }
    except Exception as e:
        logger.error(f"DEMO RSS: Error parsing feed - {str(e)}")
        return {
            "error": f"Demo RSS parse failed: {str(e)}",
            "query": "demo",
            "source": "DEMO_RSS",
            "articles": [],
        }


def fetch_combined_disaster_news(disaster_query: str, demo_mode: bool = False) -> dict:
    """
    Fetch news from GDELT, EXA, and RSS feeds for comprehensive real-time information.
    
    This function queries multiple sources:
    - GDELT: Global event data
    - EXA: Curated news search
    - RSS: Regional/country-specific feeds
    
    In demo mode, only fetches from demo RSS feed at localhost:5000/feed.xml
    
    Args:
        disaster_query: The disaster or crisis to search for (e.g., "us iran war")
        demo_mode: If True, only fetch from demo RSS feed (localhost:5000/feed.xml)
    
    Returns:
        Dictionary containing:
        - gdelt_data: Articles from GDELT API (empty in demo mode)
        - exa_data: Articles from EXA API (empty in demo mode)
        - rss_data: Articles from RSS feeds or demo RSS
        - combined_article_count: Total number of unique articles
        - timestamp: When the data was fetched
    """
    logger.info(f"COMBINED FETCH: Starting fetch for '{disaster_query}' (demo_mode={demo_mode})")
    
    if demo_mode:
        logger.info("COMBINED FETCH: Demo mode enabled - fetching only from demo RSS feed")
        rss_data = fetch_demo_rss_feed()
        
        return {
            "gdelt_data": {"articles": [], "source": "GDELT", "article_count": 0},
            "exa_data": {"articles": [], "source": "EXA", "article_count": 0},
            "rss_data": rss_data,
            "combined_article_count": len(rss_data.get("articles", [])),
            "query": disaster_query,
            "timestamp": datetime.now().isoformat(),
            "sources_queried": ["DEMO_RSS"],
            "demo_mode": True,
        }
    
    # Real mode: Fetch from all sources
    logger.info("COMBINED FETCH: Real mode - calling all sources")
    logger.info("COMBINED FETCH: Calling GDELT...")
    gdelt_data = fetch_gdelt_news(disaster_query, timespan="7d", max_records=50)
    
    logger.info("COMBINED FETCH: Calling EXA...")
    exa_data = fetch_exa_news(disaster_query, num_results=15)
    
    logger.info("COMBINED FETCH: Calling RSS feed fetcher...")
    rss_data = fetch_rss_feeds(disaster_query)
    
    total_articles = (
        len(gdelt_data.get("articles", [])) + 
        len(exa_data.get("articles", [])) +
        len(rss_data.get("articles", []))
    )
    
    logger.info(f"COMBINED FETCH: All sources completed")
    logger.info(f"COMBINED FETCH: GDELT={len(gdelt_data.get('articles', []))} | EXA={len(exa_data.get('articles', []))} | RSS={len(rss_data.get('articles', []))} | TOTAL={total_articles}")
    
    return {
        "gdelt_data": gdelt_data,
        "exa_data": exa_data,
        "rss_data": rss_data,
        "combined_article_count": total_articles,
        "query": disaster_query,
        "timestamp": datetime.now().isoformat(),
        "sources_queried": ["GDELT", "EXA", "RSS"],
        "demo_mode": False,
    }


def format_articles_for_analysis(combined_data: dict) -> str:
    """
    Format the combined news data into a readable string for analysis by the AI agent.
    
    Args:
        combined_data: Output from fetch_combined_disaster_news()
    
    Returns:
        Formatted string with all articles ready for analysis
    """
    output = "=" * 80 + "\n"
    output += f"DISASTER NEWS SEARCH: {combined_data.get('query', 'Unknown')}\n"
    output += f"Fetched at: {combined_data.get('timestamp', 'Unknown')}\n"
    output += "=" * 80 + "\n\n"
    
    # GDELT articles
    gdelt_data = combined_data.get("gdelt_data", {})
    if gdelt_data.get("articles"):
        output += "GDELT NEWS SOURCES (Global Events Database):\n"
        output += "-" * 80 + "\n"
        for i, article in enumerate(gdelt_data.get("articles", [])[:15], 1):
            output += f"\n[{i}] {article.get('title', 'No title')}\n"
            output += f"    Source: {article.get('source_domain', 'Unknown')} ({article.get('source_country', 'Unknown')})\n"
            output += f"    Language: {article.get('language', 'Unknown')}\n"
            output += f"    Published: {article.get('publication_date', 'Unknown')}\n"
            output += f"    URL: {article.get('url', 'No URL')}\n"
        output += "\n"
    
    # EXA articles
    exa_data = combined_data.get("exa_data", {})
    if exa_data.get("articles"):
        output += "\nEXA NEWS SEARCH RESULTS:\n"
        output += "-" * 80 + "\n"
        for i, article in enumerate(exa_data.get("articles", [])[:10], 1):
            output += f"\n[{i}] {article.get('title', 'No title')}\n"
            output += f"    Source: {article.get('source', 'Unknown')}\n"
            output += f"    Published: {article.get('published_date', 'Unknown')}\n"
            snippet = article.get('snippet') or 'No snippet'
            output += f"    Snippet: {snippet[:200]}...\n"
            output += f"    URL: {article.get('url', 'No URL')}\n"
        output += "\n"
    
    # RSS articles
    rss_data = combined_data.get("rss_data", {})
    if rss_data.get("articles"):
        output += "\nRSS FEED ALERTS:\n"
        output += "-" * 80 + "\n"
        for i, article in enumerate(rss_data.get("articles", [])[:10], 1):
            output += f"\n[{i}] {article.get('title', 'No title')}\n"
            output += f"    Source: {article.get('source_domain', 'Unknown')} ({article.get('source_country', 'Unknown')})\n"
            output += f"    Feed: {article.get('feed_source', 'Unknown')}\n"
            output += f"    Published: {article.get('published_date', 'Unknown')}\n"
            description = article.get('description') or 'No description'
            output += f"    Description: {description[:200]}...\n"
            output += f"    URL: {article.get('url', 'No URL')}\n"
        output += "\n"
    
    output += "\n" + "=" * 80 + "\n"
    output += f"Total articles found: {combined_data.get('combined_article_count', 0)}\n"
    output += f"Sources: {', '.join(combined_data.get('sources_queried', []))}\n"
    output += "=" * 80 + "\n"
    
    return output
