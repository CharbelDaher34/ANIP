"""
Test ingestion modules independently.
Run with: python -m app.tests.test_ingestion
"""

import os
from app.ingestion.newsapi_ingestor import NewsAPIIngestor
from app.ingestion.reddit_ingestor import RedditIngestor
from app.ingestion.gdelt_ingestor import GDELTIngestor


def test_newsapi():
    """Test NewsAPI Ingestor."""
    print("\n" + "=" * 60)
    print("Testing NewsAPI Ingestor...")
    print("=" * 60)

    api_key = os.getenv("NEWSAPI_KEY", "YOUR_NEWSAPI_KEY_HERE")

    if api_key == "YOUR_NEWSAPI_KEY_HERE":
        print("⚠️  Set NEWSAPI_KEY environment variable to test NewsAPI")
        print("   Get your key at: https://newsapi.org/")
        return

    try:
        ingestor = NewsAPIIngestor(api_key)
        articles = ingestor.fetch(query="AI", page_size=3)

        print(f"✅ Fetched {len(articles)} articles from NewsAPI\n")
        for i, article in enumerate(articles, 1):
            print(f"{i}. {article.title}")
            print(f"   Source: {article.source}")
            print(f"   URL: {article.url}")
            print(f"   Published: {article.published_at}")
            print()

    except Exception as e:
        print(f"❌ Error: {e}")


def test_reddit():
    """Test Reddit Ingestor."""
    print("\n" + "=" * 60)
    print("Testing Reddit Ingestor...")
    print("=" * 60)

    try:
        ingestor = RedditIngestor()
        articles = ingestor.fetch(subreddit="technology", limit=3)

        print(f"✅ Fetched {len(articles)} posts from Reddit\n")
        for i, article in enumerate(articles, 1):
            print(f"{i}. {article.title}")
            print(f"   Source: {article.source}")
            print(f"   Author: {article.author}")
            print(f"   URL: {article.url}")
            print()

    except Exception as e:
        print(f"❌ Error: {e}")


def test_gdelt():
    """Test GDELT Ingestor."""
    print("\n" + "=" * 60)
    print("Testing GDELT Ingestor...")
    print("=" * 60)

    try:
        ingestor = GDELTIngestor()
        articles = ingestor.fetch(limit=3)

        print(f"✅ Fetched {len(articles)} events from GDELT\n")
        for i, article in enumerate(articles, 1):
            print(f"{i}. {article.title}")
            print(f"   Source: {article.source}")
            print(f"   URL: {article.url}")
            print()

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("\n🧪 Testing News Ingestors")
    print("=" * 60)

    test_newsapi()
    test_reddit()
    test_gdelt()

    print("\n" + "=" * 60)
    print("✅ Testing complete!")
    print("=" * 60)

