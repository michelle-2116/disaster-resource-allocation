"""
RSS Feed Fetcher - Generic feed discovery and retrieval system.

Supports tag-based feed discovery for any country/region.
Feeds are configured in data/rss_feeds.json.
"""

import json
import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import asyncio
import aiohttp
import feedparser
from rapidfuzz import fuzz
import logging

logger = logging.getLogger("RSS")


class RSSFeedRegistry:
    """Load and manage RSS feed registry from JSON"""
    
    def __init__(self, config_path: str = "data/rss_feeds.json"):
        """Load feed registry from JSON file"""
        if not os.path.exists(config_path):
            logger.error(f"RSS feeds config not found: {config_path}")
            self.feeds = {}
            return
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                self.feeds = config.get('feeds', {})
                logger.info(f"RSS Registry: Loaded {len(self.feeds)} feeds from {config_path}")
        except Exception as e:
            logger.error(f"RSS Registry: Failed to load config - {e}")
            self.feeds = {}
    
    def get_all_feeds(self) -> Dict:
        """Get all feeds"""
        return self.feeds
    
    def get_feed_urls(self, feed_ids: List[str]) -> Dict[str, str]:
        """Get URLs for specific feed IDs"""
        return {
            fid: self.feeds[fid]['url'] 
            for fid in feed_ids 
            if fid in self.feeds
        }


def extract_query_tokens(query: str) -> List[str]:
    """Extract meaningful tokens from query for tag matching"""
    # Simple tokenization - can be enhanced
    tokens = query.lower().split()
    # Remove common words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'in', 'on', 'at', 'to', 'for'}
    tokens = [t for t in tokens if t not in stop_words and len(t) > 2]
    return tokens


def find_relevant_feeds(
    query: str, 
    registry: RSSFeedRegistry,
    min_score: int = 50,
    max_feeds: int = 5
) -> List[tuple]:
    """
    Find relevant feeds using fuzzy tag matching.
    
    Returns list of tuples: (feed_id, feed_metadata, match_score)
    """
    
    query_tokens = extract_query_tokens(query)
    logger.info(f"RSS Discovery: Query tokens extracted: {query_tokens}")
    
    if not query_tokens:
        logger.warning(f"RSS Discovery: No meaningful tokens extracted from query: '{query}'")
        return []
    
    scores = {}
    
    for feed_id, feed_metadata in registry.get_all_feeds().items():
        feed_tags = feed_metadata.get('tags', [])
        
        # Calculate best match score for this feed
        best_score = 0
        for q_token in query_tokens:
            for f_tag in feed_tags:
                # Fuzzy match with partial ratio (handles substrings)
                score = fuzz.partial_ratio(q_token, f_tag)
                best_score = max(best_score, score)
        
        if best_score >= min_score:
            scores[feed_id] = (best_score, feed_metadata)
            logger.debug(f"RSS Discovery: Feed '{feed_id}' matched with score {best_score}")
    
    # Sort by score and return top N
    ranked = sorted(scores.items(), key=lambda x: x[1][0], reverse=True)
    result = [
        (feed_id, metadata, score)
        for feed_id, (score, metadata) in ranked[:max_feeds]
    ]
    
    logger.info(f"RSS Discovery: Found {len(result)} relevant feeds (checked {len(registry.get_all_feeds())} total)")
    for feed_id, metadata, score in result:
        logger.debug(f"RSS Discovery: - {feed_id} ({metadata.get('region', 'Unknown')}) score={score}")
    
    return result


async def fetch_single_feed(
    session: aiohttp.ClientSession,
    feed_id: str,
    feed_url: str,
    timeout: int = 10
) -> Dict:
    """Fetch and parse a single RSS feed"""
    
    try:
        async with session.get(feed_url, timeout=timeout) as response:
            if response.status == 200:
                content = await response.text()
                parsed = feedparser.parse(content)
                
                if parsed.bozo:
                    logger.warning(f"RSS Fetch: Feed '{feed_id}' has parsing issues - {parsed.bozo_exception}")
                
                entries = parsed.get('entries', [])
                logger.info(f"RSS Fetch: Feed '{feed_id}' - fetched {len(entries)} entries")
                
                return {
                    'feed_id': feed_id,
                    'feed_url': feed_url,
                    'entries': entries,
                    'success': True,
                    'error': None
                }
            else:
                logger.warning(f"RSS Fetch: Feed '{feed_id}' returned HTTP {response.status}")
                return {
                    'feed_id': feed_id,
                    'feed_url': feed_url,
                    'entries': [],
                    'success': False,
                    'error': f"HTTP {response.status}"
                }
    
    except asyncio.TimeoutError:
        logger.warning(f"RSS Fetch: Feed '{feed_id}' timed out (>{timeout}s)")
        return {
            'feed_id': feed_id,
            'feed_url': feed_url,
            'entries': [],
            'success': False,
            'error': "Timeout"
        }
    
    except Exception as e:
        logger.error(f"RSS Fetch: Feed '{feed_id}' error - {str(e)}")
        return {
            'feed_id': feed_id,
            'feed_url': feed_url,
            'entries': [],
            'success': False,
            'error': str(e)
        }


async def fetch_multiple_feeds(
    feed_urls: Dict[str, str],
    timeout: int = 10
) -> List[Dict]:
    """Fetch multiple feeds in parallel"""
    
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_single_feed(session, feed_id, url, timeout)
            for feed_id, url in feed_urls.items()
        ]
        results = await asyncio.gather(*tasks)
    
    return results


def filter_entries_by_recency(
    entries: List,
    hours: int = 48
) -> List:
    """Filter entries published in last N hours"""
    
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    filtered = []
    
    for entry in entries:
        try:
            # Try to get published date
            pub_date = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                pub_date = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                pub_date = datetime(*entry.updated_parsed[:6])
            
            if pub_date and pub_date >= cutoff_time:
                filtered.append(entry)
        except Exception as e:
            logger.debug(f"Error parsing entry date: {e}")
            # Include entry if date parsing fails
            filtered.append(entry)
    
    return filtered


def extract_article_data(entry, feed_id: str, feed_metadata: Dict) -> Dict:
    """Extract standardized article data from feed entry"""
    
    return {
        'title': entry.get('title', 'No title'),
        'description': entry.get('summary', entry.get('description', 'No description'))[:300],
        'url': entry.get('link', ''),
        'published_date': entry.get('published', 'Unknown'),
        'source_domain': feed_metadata.get('region', 'Unknown'),
        'source_country': feed_metadata.get('country', 'Unknown'),
        'feed_source': feed_metadata.get('source', 'RSS'),
        'feed_id': feed_id,
        'language': 'en'  # Default, can be detected if needed
    }


def fetch_rss_feeds(query: str, config_path: str = "data/rss_feeds.json") -> Dict:
    """
    Main entry point: Fetch RSS feeds relevant to query
    
    Returns dict with structure matching GDELT/EXA output
    """
    
    logger.info(f"RSS: Starting feed fetch for query '{query}'")
    
    # Load feed registry
    registry = RSSFeedRegistry(config_path)
    
    if not registry.get_all_feeds():
        logger.warning("RSS: No RSS feeds configured")
        return {
            "articles": [],
            "query": query,
            "source": "RSS",
            "timestamp": datetime.now().isoformat(),
            "article_count": 0,
            "error": "No feeds configured"
        }
    
    # Find relevant feeds
    logger.info(f"RSS: Searching for relevant feeds...")
    relevant_feeds = find_relevant_feeds(query, registry, min_score=50, max_feeds=5)
    
    if not relevant_feeds:
        logger.info(f"RSS: No relevant feeds found for query '{query}'")
        return {
            "articles": [],
            "query": query,
            "source": "RSS",
            "timestamp": datetime.now().isoformat(),
            "article_count": 0,
            "feeds_checked": len(registry.get_all_feeds()),
            "feeds_matched": 0
        }
    
    # Get URLs to fetch
    feed_urls = {
        feed_id: registry.feeds[feed_id]['url']
        for feed_id, metadata, score in relevant_feeds
    }
    
    logger.info(f"RSS: Fetching {len(feed_urls)} relevant feeds...")
    
    # Fetch all feeds in parallel
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        fetch_results = loop.run_until_complete(fetch_multiple_feeds(feed_urls))
        loop.close()
    except RuntimeError:
        # Handle case where event loop already exists
        try:
            fetch_results = asyncio.run(fetch_multiple_feeds(feed_urls))
        except RuntimeError:
            # Fallback to synchronous fetching
            logger.warning("RSS: Using synchronous feed fetching (slower)")
            fetch_results = []
            for feed_id, url in feed_urls.items():
                import requests
                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        parsed = feedparser.parse(response.content)
                        fetch_results.append({
                            'feed_id': feed_id,
                            'feed_url': url,
                            'entries': parsed.get('entries', []),
                            'success': True,
                            'error': None
                        })
                except Exception as e:
                    logger.error(f"RSS: Error fetching '{feed_id}' - {e}")
    
    # Process results
    articles = []
    successful_feeds = 0
    for feed_result in fetch_results:
        if not feed_result['success']:
            logger.warning(f"RSS: Failed to fetch '{feed_result['feed_id']}': {feed_result['error']}")
            continue
        
        successful_feeds += 1
        feed_id = feed_result['feed_id']
        feed_metadata = next(
            (m for fid, m, _ in relevant_feeds if fid == feed_id),
            {}
        )
        
        # Filter by recency
        recent_entries = filter_entries_by_recency(feed_result['entries'], hours=48)
        logger.debug(f"RSS: Feed '{feed_id}' - {len(recent_entries)} recent entries (48h)")
        
        # Extract article data (limit to 3 per feed)
        articles_from_feed = 0
        for entry in recent_entries[:3]:
            articles.append(extract_article_data(entry, feed_id, feed_metadata))
            articles_from_feed += 1
        
        logger.info(f"RSS: Feed '{feed_id}' ({feed_metadata.get('region', 'Unknown')}) - extracted {articles_from_feed} articles")
    
    logger.info(f"RSS: Completed - {successful_feeds}/{len(feed_urls)} feeds successful, {len(articles)} articles extracted")
    
    return {
        "articles": articles,
        "query": query,
        "source": "RSS",
        "timestamp": datetime.now().isoformat(),
        "article_count": len(articles),
        "feeds_checked": len(registry.get_all_feeds()),
        "feeds_matched": len(relevant_feeds),
        "feeds_fetched": successful_feeds
    }


if __name__ == "__main__":
    # Test
    result = fetch_rss_feeds("bihar floods")
    print(f"Found {result['article_count']} articles")
    for article in result['articles'][:3]:
        print(f"  - {article['title']}")
