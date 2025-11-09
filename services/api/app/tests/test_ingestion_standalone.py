#!/usr/bin/env python3
"""
Standalone test script for news ingestors.

Usage:
    # Test all ingestors
    python test_ingestion_standalone.py

    # Test specific ingestor
    python test_ingestion_standalone.py --reddit
    python test_ingestion_standalone.py --newsapi --key YOUR_KEY

Requirements:
    - Set NEWSAPI_KEY env var for NewsAPI testing
    - Internet connection for all tests
"""

import sys
import os
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
    load_dotenv(env_path)
except ImportError:
    pass  # dotenv not installed, will use system env vars

from app.ingestion.newsapi_ingestor import NewsAPIIngestor
from app.ingestion.reddit_ingestor import RedditIngestor
from app.ingestion.gdelt_ingestor import GDELTIngestor


def test_reddit(limit=3):
    """Test Reddit ingestor."""
    print("\n" + "="*60)
    print("📰 Testing Reddit Ingestor")
    print("="*60)

    try:
        ingestor = RedditIngestor()
        articles = ingestor.fetch(subreddit="technology", limit=limit)

        print(f"✅ Successfully fetched {len(articles)} articles from r/technology\n")

        for i, article in enumerate(articles, 1):
            print(f"{i}. {article.title[:60]}...")
            print(f"   Author: {article.author}")
            print(f"   URL: {article.url}")
            print()

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_newsapi(api_key, query="AI", limit=3):
    """Test NewsAPI ingestor."""
    print("\n" + "="*60)
    print("📰 Testing NewsAPI Ingestor")
    print("="*60)

    if not api_key:
        print("⚠️  No API key provided. Use --key YOUR_KEY or set NEWSAPI_KEY env var")
        print("   Get your key at: https://newsapi.org/")
        return False

    try:
        ingestor = NewsAPIIngestor(api_key)
        articles = ingestor.fetch(query=query, page_size=limit)

        print(f"✅ Successfully fetched {len(articles)} articles about '{query}'\n")

        for i, article in enumerate(articles, 1):
            print(f"{i}. {article.title}")
            print(f"   Source: {article.source}")
            print(f"   Published: {article.published_at}")
            print()

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_gdelt(limit=3):
    """Test GDELT ingestor."""
    print("\n" + "="*60)
    print("📰 Testing GDELT Ingestor")
    print("="*60)

    try:
        ingestor = GDELTIngestor()
        articles = ingestor.fetch(limit=limit)

        print(f"✅ Successfully fetched {len(articles)} GDELT events\n")

        for i, article in enumerate(articles, 1):
            print(f"{i}. {article.title}")
            print(f"   Source: {article.source}")
            print(f"   Region: {article.region}")
            print()

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Test news ingestors")
    parser.add_argument("--reddit", action="store_true", help="Test Reddit ingestor only")
    parser.add_argument("--newsapi", action="store_true", help="Test NewsAPI ingestor only")
    parser.add_argument("--gdelt", action="store_true", help="Test GDELT ingestor only")
    parser.add_argument("--key", type=str, help="NewsAPI key (overrides .env)")
    parser.add_argument("--limit", type=int, default=3, help="Number of articles to fetch")
    parser.add_argument("--query", type=str, default="AI", help="Query for NewsAPI")

    args = parser.parse_args()

    # If no specific test is selected, run all
    run_all = not (args.reddit or args.newsapi or args.gdelt)

    results = []

    if args.reddit or run_all:
        results.append(("Reddit", test_reddit(args.limit)))

    if args.newsapi or run_all:
        api_key = args.key or os.getenv("NEWSAPI_KEY")
        results.append(("NewsAPI", test_newsapi(api_key, query=args.query, limit=args.limit)))

    if args.gdelt or run_all:
        results.append(("GDELT", test_gdelt(args.limit)))

    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)

    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{name:15} {status}")

    print("="*60)


if __name__ == "__main__":
    main()

