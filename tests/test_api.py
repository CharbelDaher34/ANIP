#!/usr/bin/env python
"""
Test script for the ANIP API endpoints.

Run with: python tests/test_api.py
Or with: uv run python tests/test_api.py

Make sure the API service is running:
    docker-compose up -d api
"""
import requests
import sys
from typing import Dict, Any, List


# API URL
API_URL = "http://localhost:18000"


def test_root_endpoint() -> bool:
    """Test the root endpoint."""
    try:
        response = requests.get(f"{API_URL}/", timeout=5)
        response.raise_for_status()
        data = response.json()
        
        print("✅ Root Endpoint:")
        print(f"   Message: {data.get('message')}")
        print(f"   Version: {data.get('version')}")
        print(f"   Status: {data.get('status')}")
        
        assert data.get('status') == 'running', "API should be running"
        return True
    except Exception as e:
        print(f"❌ Root Endpoint Failed: {e}")
        return False


def test_health_check() -> bool:
    """Test the health check endpoint."""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        response.raise_for_status()
        data = response.json()
        
        print("\n✅ Health Check:")
        print(f"   Status: {data.get('status')}")
        print(f"   Database: {data.get('database')}")
        
        assert data.get('status') == 'healthy', "API should be healthy"
        return True
    except Exception as e:
        print(f"❌ Health Check Failed: {e}")
        return False


def test_get_articles() -> bool:
    """Test getting articles with pagination."""
    try:
        # Test basic retrieval
        response = requests.get(f"{API_URL}/api/articles?limit=5", timeout=10)
        response.raise_for_status()
        articles = response.json()
        
        print("\n✅ Get Articles:")
        print(f"   Retrieved: {len(articles)} articles")
        
        if len(articles) > 0:
            first_article = articles[0]
            print(f"   First article:")
            print(f"     - ID: {first_article.get('id')}")
            print(f"     - Title: {first_article.get('title')[:60]}...")
            print(f"     - Topic: {first_article.get('topic')}")
            print(f"     - Sentiment: {first_article.get('sentiment')}")
            print(f"     - Source: {first_article.get('source')}")
            
            # Validate structure
            required_fields = ['id', 'title', 'url', 'created_at']
            for field in required_fields:
                assert field in first_article, f"Missing field: {field}"
        else:
            print("   ⚠️  No articles found (database might be empty)")
        
        return True
    except Exception as e:
        print(f"❌ Get Articles Failed: {e}")
        return False


def test_get_articles_with_filters() -> bool:
    """Test getting articles with filters."""
    try:
        # Test topic filter
        response = requests.get(f"{API_URL}/api/articles?limit=3&topic=Technology", timeout=10)
        response.raise_for_status()
        tech_articles = response.json()
        
        print("\n✅ Get Articles with Filters:")
        print(f"   Technology articles: {len(tech_articles)}")
        
        # Test sentiment filter
        response = requests.get(f"{API_URL}/api/articles?limit=3&sentiment=positive", timeout=10)
        response.raise_for_status()
        positive_articles = response.json()
        print(f"   Positive sentiment articles: {len(positive_articles)}")
        
        # Validate filtering works
        for article in positive_articles:
            if article.get('sentiment'):
                assert article['sentiment'] == 'positive', "Sentiment filter should work"
        
        # Test pagination
        response = requests.get(f"{API_URL}/api/articles?limit=2&offset=0", timeout=10)
        page1 = response.json()
        response = requests.get(f"{API_URL}/api/articles?limit=2&offset=2", timeout=10)
        page2 = response.json()
        
        print(f"   Pagination:")
        print(f"     - Page 1: {len(page1)} articles")
        print(f"     - Page 2: {len(page2)} articles")
        
        if len(page1) > 0 and len(page2) > 0:
            # Pages should be different
            assert page1[0]['id'] != page2[0]['id'], "Pagination should return different results"
        
        return True
    except Exception as e:
        print(f"❌ Get Articles with Filters Failed: {e}")
        return False


def test_get_single_article() -> bool:
    """Test getting a single article by ID."""
    try:
        # First get an article to know a valid ID
        response = requests.get(f"{API_URL}/api/articles?limit=1", timeout=10)
        response.raise_for_status()
        articles = response.json()
        
        if len(articles) == 0:
            print("\n⚠️  Get Single Article: Skipped (no articles in database)")
            return True
        
        article_id = articles[0]['id']
        
        # Get single article
        response = requests.get(f"{API_URL}/api/articles/{article_id}", timeout=10)
        response.raise_for_status()
        article = response.json()
        
        print("\n✅ Get Single Article:")
        print(f"   Article ID: {article.get('id')}")
        print(f"   Title: {article.get('title')[:60]}...")
        print(f"   URL: {article.get('url')[:50]}...")
        print(f"   Topic: {article.get('topic')}")
        print(f"   Sentiment: {article.get('sentiment')} ({article.get('sentiment_score')})")
        
        assert article['id'] == article_id, "Should return correct article"
        
        # Test 404 for non-existent article
        response = requests.get(f"{API_URL}/api/articles/999999999", timeout=10)
        assert response.status_code == 404, "Should return 404 for non-existent article"
        print("   ✓ 404 error for non-existent article works correctly")
        
        return True
    except Exception as e:
        print(f"❌ Get Single Article Failed: {e}")
        return False


def test_topic_stats() -> bool:
    """Test topic statistics endpoint."""
    try:
        response = requests.get(f"{API_URL}/api/stats/topics", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        topics = data.get('topics', [])
        
        print("\n✅ Topic Statistics:")
        print(f"   Total topics: {len(topics)}")
        
        if len(topics) > 0:
            print("   Top 5 topics:")
            for i, topic_data in enumerate(topics[:5], 1):
                print(f"     {i}. {topic_data.get('topic')}: {topic_data.get('count')} articles")
        else:
            print("   ⚠️  No topics found (ML processing might not be complete)")
        
        return True
    except Exception as e:
        print(f"❌ Topic Statistics Failed: {e}")
        return False


def test_sentiment_stats() -> bool:
    """Test sentiment statistics endpoint."""
    try:
        response = requests.get(f"{API_URL}/api/stats/sentiments", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        sentiments = data.get('sentiments', [])
        
        print("\n✅ Sentiment Statistics:")
        print(f"   Sentiment distribution:")
        
        total = sum(s.get('count', 0) for s in sentiments)
        for sentiment_data in sentiments:
            sentiment = sentiment_data.get('sentiment', 'unknown')
            count = sentiment_data.get('count', 0)
            avg_score = sentiment_data.get('avg_score')
            percentage = (count / total * 100) if total > 0 else 0
            
            print(f"     - {sentiment.capitalize()}: {count} ({percentage:.1f}%)")
            if avg_score:
                print(f"       Avg score: {avg_score:.3f}")
        
        if total == 0:
            print("   ⚠️  No sentiment data (ML processing might not be complete)")
        
        return True
    except Exception as e:
        print(f"❌ Sentiment Statistics Failed: {e}")
        return False


def test_source_stats() -> bool:
    """Test source statistics endpoint."""
    try:
        response = requests.get(f"{API_URL}/api/stats/sources", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        sources = data.get('sources', [])
        
        print("\n✅ Source Statistics:")
        print(f"   Total sources: {len(sources)}")
        
        if len(sources) > 0:
            print("   Top 5 sources:")
            for i, source_data in enumerate(sources[:5], 1):
                source = source_data.get('source', 'Unknown')
                count = source_data.get('count', 0)
                print(f"     {i}. {source}: {count} articles")
        else:
            print("   ⚠️  No sources found")
        
        return True
    except Exception as e:
        print(f"❌ Source Statistics Failed: {e}")
        return False


def test_api_source_stats() -> bool:
    """Test API source statistics endpoint."""
    try:
        response = requests.get(f"{API_URL}/api/stats/api-sources", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        api_sources = data.get('api_sources', [])
        
        print("\n✅ API Source Statistics:")
        print(f"   Active API sources: {len(api_sources)}")
        
        total = sum(s.get('count', 0) for s in api_sources)
        for source_data in api_sources:
            api_source = source_data.get('api_source', 'unknown')
            count = source_data.get('count', 0)
            percentage = (count / total * 100) if total > 0 else 0
            print(f"     - {api_source}: {count} articles ({percentage:.1f}%)")
        
        return True
    except Exception as e:
        print(f"❌ API Source Statistics Failed: {e}")
        return False


def test_missing_ml_stats() -> bool:
    """Test missing ML fields statistics endpoint."""
    try:
        response = requests.get(f"{API_URL}/api/stats/missing-ml", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        print("\n✅ Missing ML Fields Statistics:")
        print(f"   Total articles: {data.get('total_articles', 0)}")
        print(f"   Missing topic: {data.get('missing_topic', 0)}")
        print(f"   Missing sentiment: {data.get('missing_sentiment', 0)}")
        print(f"   Missing embedding: {data.get('missing_embedding', 0)}")
        print(f"   Complete: {data.get('complete', 0)}")
        
        completion_rate = data.get('completion_rate', 0)
        print(f"   Completion rate: {completion_rate:.1f}%")
        
        if completion_rate < 100:
            print(f"   ⚠️  {100 - completion_rate:.1f}% of articles need ML processing")
        
        return True
    except Exception as e:
        print(f"❌ Missing ML Stats Failed: {e}")
        return False


def test_semantic_search() -> bool:
    """Test semantic search endpoint."""
    try:
        # First check if there are articles with embeddings
        response = requests.get(f"{API_URL}/api/stats/missing-ml", timeout=10)
        response.raise_for_status()
        stats = response.json()
        
        total = stats.get('total_articles', 0)
        missing_embedding = stats.get('missing_embedding', 0)
        articles_with_embeddings = total - missing_embedding
        
        if articles_with_embeddings == 0:
            print("\n⚠️  Semantic Search: Skipped (no articles with embeddings)")
            print(f"   Total articles: {total}, Missing embeddings: {missing_embedding}")
            return True
        
        # Test semantic search
        query = "artificial intelligence and machine learning"
        response = requests.get(
            f"{API_URL}/api/search/similar",
            params={"question": query, "limit": 3},  # Note: API expects 'question' not 'query'
            timeout=15
        )
        response.raise_for_status()
        
        results = response.json()
        
        print("\n✅ Semantic Search:")
        print(f"   Query: '{query}'")
        print(f"   Results: {len(results)}")
        
        for i, result in enumerate(results, 1):
            similarity = result.get('similarity_score', 0)
            title = result.get('title', '')[:60]
            topic = result.get('topic', 'N/A')
            
            print(f"\n   Result {i} (similarity: {similarity:.4f}):")
            print(f"     - Title: {title}...")
            print(f"     - Topic: {topic}")
        
        # Validate results are sorted by similarity
        if len(results) > 1:
            scores = [r.get('similarity_score', 0) for r in results]
            assert scores == sorted(scores, reverse=True), "Results should be sorted by similarity"
            print("\n   ✓ Results are correctly sorted by similarity")
        
        return True
    except Exception as e:
        print(f"❌ Semantic Search Failed: {e}")
        return False


def test_error_handling() -> bool:
    """Test API error handling."""
    try:
        print("\n✅ Error Handling:")
        
        # Test invalid sentiment value
        response = requests.get(f"{API_URL}/api/articles?sentiment=invalid", timeout=10)
        assert response.status_code == 400, "Should return 400 for invalid sentiment"
        print("   ✓ Invalid sentiment parameter returns 400")
        
        # Test invalid article ID
        response = requests.get(f"{API_URL}/api/articles/abc", timeout=10)
        assert response.status_code == 422, "Should return 422 for invalid ID type"
        print("   ✓ Invalid article ID returns 422")
        
        # Test invalid limit (too high)
        response = requests.get(f"{API_URL}/api/articles?limit=1000", timeout=10)
        assert response.status_code == 422, "Should return 422 for limit > 100"
        print("   ✓ Limit > 100 returns 422")
        
        # Test invalid limit (negative)
        response = requests.get(f"{API_URL}/api/articles?limit=-1", timeout=10)
        assert response.status_code == 422, "Should return 422 for negative limit"
        print("   ✓ Negative limit returns 422")
        
        return True
    except Exception as e:
        print(f"❌ Error Handling Test Failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 70)
    print("🧪 Testing ANIP API Endpoints")
    print("=" * 70)
    print(f"API URL: {API_URL}")
    print("=" * 70)
    
    tests = [
        ("Root Endpoint", test_root_endpoint),
        ("Health Check", test_health_check),
        ("Get Articles", test_get_articles),
        ("Get Articles with Filters", test_get_articles_with_filters),
        ("Get Single Article", test_get_single_article),
        ("Topic Statistics", test_topic_stats),
        ("Sentiment Statistics", test_sentiment_stats),
        ("Source Statistics", test_source_stats),
        ("API Source Statistics", test_api_source_stats),
        ("Missing ML Statistics", test_missing_ml_stats),
        ("Semantic Search", test_semantic_search),
        ("Error Handling", test_error_handling),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Test Summary")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("=" * 70)
    print(f"Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("=" * 70)
    
    # Exit with appropriate code
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()

