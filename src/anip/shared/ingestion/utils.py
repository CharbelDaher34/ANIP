"""
Utility functions for ingestion.
"""
from datetime import datetime, timezone
from typing import Dict, Any


def parse_datetime(dt_string: str) -> datetime:
    """Parse datetime string to datetime object."""
    try:
        return datetime.fromisoformat(dt_string.replace("Z", "+00:00"))
    except Exception:
        return datetime.now(timezone.utc)


def clean_article_data(article: Dict[str, Any]) -> Dict[str, Any]:
    """Clean and validate article data."""
    return {
        'title': article.get('title', 'No Title')[:500],
        'content': article.get('content', '')[:10000],
        'source': article.get('source', 'Unknown')[:200],
        'author': article.get('author', 'Unknown')[:200],
        'url': article.get('url', '')[:1000],
        'published_at': article.get('published_at'),
        'language': article.get('language', 'en')[:50],
        'region': article.get('region', 'US')[:100]
    }

