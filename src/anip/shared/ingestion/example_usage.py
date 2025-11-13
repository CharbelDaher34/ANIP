"""
Example usage of all news API ingestors.
This demonstrates how to use each of the 5 news API ingestors.

To run this script with plain Python (no uv, no installation):
1. Make sure you have a .env file in the project root with your API keys:
   NEWSAPI_KEY="your_key"
   NEWSDATA_KEY="your_key"
   MEDIASTACK_KEY="your_key"
   THENEWSAPI_KEY="your_key"
   WORLDNEWS_KEY="your_key"

2. Run from the project root directory:
   cd /storage/hussein/anip
   PYTHONPATH=/storage/hussein/anip/src python src/anip/shared/ingestion/example_usage.py

Note: This requires 'requests' library. If not installed:
   pip install requests python-dotenv
"""
import sys
from pathlib import Path

# Add src directory to path if package is not installed
project_root = Path(__file__).parent.parent.parent.parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Check for required dependencies
try:
    import requests
except ImportError:
    print("❌ Error: 'requests' library is required but not installed.")
    print("   Install it with: pip install requests")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None
    print("⚠️  Warning: 'python-dotenv' not installed. .env file won't be loaded automatically.")
    print("   Install it with: pip install python-dotenv")
    print("   Or set environment variables manually.\n")

try:
    from anip.shared.ingestion import (
        NewsAPIIngestor,
        NewsDataIngestor,
        MediastackIngestor,
        TheNewsAPIIngestor,
        WorldNewsAPIIngestor,
        GDELTIngestor,
    )
except ImportError as e:
    print(f"❌ Error importing ingestors: {e}")
    print("   Make sure you're running from the project root with PYTHONPATH set:")
    print("   PYTHONPATH=/storage/hussein/anip/src python src/anip/shared/ingestion/example_usage.py")
    sys.exit(1)

# Load .env file from project root
if load_dotenv:
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    else:
        print(f"⚠️  Warning: .env file not found at {env_file}")
        print("   Make sure to set API keys as environment variables or create a .env file\n")


def print_article(api_name: str, article: dict):
    """Print a single article in a readable format."""
    print(f"\n{'='*60}")
    print(f"API: {api_name}")
    print(f"{'='*60}")
    print(f"Title: {article.get('title', 'N/A')}")
    print(f"Source: {article.get('source', 'N/A')}")
    print(f"Author: {article.get('author', 'N/A')}")
    print(f"Published: {article.get('published_at', 'N/A')}")
    print(f"Language: {article.get('language', 'N/A')}")
    print(f"Region: {article.get('region', 'N/A')}")
    print(f"URL: {article.get('url', 'N/A')}")
    content = article.get('content', '')
    if content:
        content_preview = content[:200] + "..." if len(content) > 200 else content
        print(f"Content: {content_preview}")
    print(f"{'='*60}\n")


def example_newsapi():
    """Example: NewsAPI.org (free tier - 500 requests/day)"""
    ingestor = NewsAPIIngestor()
    
    # Fetch 1 top headline from US in technology category
    articles = ingestor.fetch(query="tomato soup", page_size=1)
    if articles:
        print_article("NewsAPI.org", articles[0])
    else:
        print("NewsAPI: No articles found")
    return articles


def example_newsdata():
    """Example: NewsData.io (free tier - 200 requests/day)"""
    ingestor = NewsDataIngestor()
    
    # Fetch news from US with minimal parameters (no page parameter for free tier)
    articles = ingestor.fetch(q="technology")
    if articles:
        print_article("NewsData.io", articles[0])
    else:
        print("NewsData: No articles found")
    return articles

def example_gdelt():
    """Example: GDELT (free tier - 1000 requests/day)"""
    ingestor = GDELTIngestor()
    articles = ingestor.fetch(query="technology", max_records=1)
    if articles:
        print_article("GDELT", articles[0])
    else:
        print("GDELT: No articles found")
    return articles

def example_mediastack():
    """Example: Mediastack (free tier - 500 requests/month)"""
    ingestor = MediastackIngestor()
    
    # Fetch news with minimal parameters for free tier compatibility
    articles = ingestor.fetch(countries="us", limit=1)
    if articles:
        print_article("Mediastack", articles[0])
    else:
        print("Mediastack: No articles found")
    return articles


def example_thenewsapi():
    """Example: TheNewsAPI.com (free tier - 500 requests/day)"""
    ingestor = TheNewsAPIIngestor()
    
    # Fetch 1 top news article from US
    articles = ingestor.fetch(locale="us", limit=1)
    if articles:
        print_article("TheNewsAPI.com", articles[0])
    else:
        print("TheNewsAPI: No articles found")
    return articles


def example_worldnewsapi():
    """Example: WorldNewsAPI.com (free tier - 100 requests/day)"""
    ingestor = WorldNewsAPIIngestor()
    
    # Fetch 1 world news article
    articles = ingestor.fetch(text="world", language="en", number=1)
    if articles:
        print_article("WorldNewsAPI.com", articles[0])
    else:
        print("WorldNewsAPI: No articles found")
    return articles


if __name__ == "__main__":
    print("=== News API Ingestor Examples ===\n")
    
    # Run all examples
    try:
        example_newsapi()
    except Exception as e:
        print(f"NewsAPI error: {e}\n")
    
    # try:
    #     example_newsdata()
    # except Exception as e:
    #     print(f"NewsData error: {e}\n")
    # try:
    #     example_gdelt()
    # except Exception as e:
    #     print(f"GDELT error: {e}\n")
    # try:
    #     example_mediastack()
    # except Exception as e:
    #     print(f"Mediastack error: {e}\n")
    
    # try:
    #     example_thenewsapi()
    # except Exception as e:
    #     print(f"TheNewsAPI error: {e}\n")
    
    # try:
    #     example_worldnewsapi()
    # except Exception as e:
    #     print(f"WorldNewsAPI error: {e}\n")

