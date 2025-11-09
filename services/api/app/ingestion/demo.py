#!/usr/bin/env python3
"""
Demo script showing how to use the news ingestors.

Usage:
    # From inside the Docker container:
    docker-compose exec -T api python app/ingestion/demo.py
    
    # Or from the host:
    docker-compose exec -T api bash -c "cd /app && python -m app.ingestion.demo"
"""

import os
import sys
from pathlib import Path

# Add app directory to path
app_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(app_dir))

from app.ingestion import NewsAPIIngestor, RedditIngestor, GDELTIngestor
from app.ingestion.utils import deduplicate_articles, filter_by_language


def demo_newsapi():
    """Demonstrate NewsAPI ingestor."""
    print("\n" + "="*60)
    print("📰 NewsAPI Demo")
    print("="*60)
    
    api_key = os.getenv("NEWSAPI_KEY")
    if not api_key:
        print("⚠️  Set NEWSAPI_KEY environment variable")
        return
    
    ingestor = NewsAPIIngestor(api_key)
    
    # Fetch articles about AI
    articles = ingestor.fetch(query="artificial intelligence", page_size=5)
    
    print(f"\n✅ Fetched {len(articles)} articles\n")
    
    for i, article in enumerate(articles, 1):
        print(f"{i}. {article.title}")
        print(f"   📰 {article.source}")
        print(f"   🔗 {article.url}")
        print(f"   📅 {article.published_at}")
        print()


def demo_reddit():
    """Demonstrate Reddit ingestor."""
    print("\n" + "="*60)
    print("📰 Reddit Demo")
    print("="*60)
    
    ingestor = RedditIngestor()
    
    # Fetch from multiple subreddits
    subreddits = ["worldnews", "technology", "science"]
    all_articles = []
    
    for sub in subreddits:
        try:
            articles = ingestor.fetch(subreddit=sub, limit=3)
            all_articles.extend(articles)
            print(f"✅ Fetched {len(articles)} from r/{sub}")
        except Exception as e:
            print(f"❌ Error fetching r/{sub}: {e}")
    
    print(f"\n📊 Total articles: {len(all_articles)}\n")
    
    # Show first 5
    for i, article in enumerate(all_articles[:5], 1):
        print(f"{i}. {article.title[:60]}...")
        print(f"   👤 {article.author}")
        print(f"   🔗 {article.url}")
        print()


def demo_utilities():
    """Demonstrate utility functions."""
    print("\n" + "="*60)
    print("🛠️  Utility Functions Demo")
    print("="*60)
    
    api_key = os.getenv("NEWSAPI_KEY")
    if not api_key:
        print("⚠️  Set NEWSAPI_KEY environment variable")
        return
    
    # Fetch some articles
    ingestor = NewsAPIIngestor(api_key)
    articles = ingestor.fetch(query="technology", page_size=10)
    
    print(f"\n📥 Original articles: {len(articles)}")
    
    # Deduplicate
    unique = deduplicate_articles(articles)
    print(f"✨ After deduplication: {len(unique)}")
    
    # Filter by language
    english = filter_by_language(unique, "en")
    print(f"🌐 English articles: {len(english)}")
    
    print("\n📋 Sample articles:")
    for article in english[:3]:
        print(f"  • {article.title[:50]}...")


def demo_combined():
    """Demonstrate combining multiple sources."""
    print("\n" + "="*60)
    print("🔄 Combined Sources Demo")
    print("="*60)
    
    all_articles = []
    
    # Try NewsAPI
    api_key = os.getenv("NEWSAPI_KEY")
    if api_key:
        try:
            ingestor = NewsAPIIngestor(api_key)
            articles = ingestor.fetch(query="AI", page_size=5)
            all_articles.extend(articles)
            print(f"✅ NewsAPI: {len(articles)} articles")
        except Exception as e:
            print(f"❌ NewsAPI error: {e}")
    
    # Try Reddit
    try:
        ingestor = RedditIngestor()
        articles = ingestor.fetch(subreddit="technology", limit=5)
        all_articles.extend(articles)
        print(f"✅ Reddit: {len(articles)} articles")
    except Exception as e:
        print(f"❌ Reddit error: {e}")
    
    # Try GDELT
    try:
        ingestor = GDELTIngestor()
        articles = ingestor.fetch(limit=5)
        all_articles.extend(articles)
        print(f"✅ GDELT: {len(articles)} articles")
    except Exception as e:
        print(f"❌ GDELT error: {e}")
    
    print(f"\n📊 Total from all sources: {len(all_articles)}")
    
    # Deduplicate
    unique = deduplicate_articles(all_articles)
    print(f"✨ Unique articles: {len(unique)}")
    
    # Group by source
    sources = {}
    for article in unique:
        source = article.source or "Unknown"
        sources[source] = sources.get(source, 0) + 1
    
    print("\n📈 Articles by source:")
    for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
        print(f"  {source}: {count}")


def main():
    """Run all demos."""
    print("\n" + "="*60)
    print("🚀 ANIP News Ingestion Demo")
    print("="*60)
    
    try:
        demo_newsapi()
    except Exception as e:
        print(f"Error in NewsAPI demo: {e}")
    
    try:
        demo_utilities()
    except Exception as e:
        print(f"Error in utilities demo: {e}")
    
    try:
        demo_combined()
    except Exception as e:
        print(f"Error in combined demo: {e}")
    
    print("\n" + "="*60)
    print("✅ Demo complete!")
    print("="*60)


if __name__ == "__main__":
    main()

