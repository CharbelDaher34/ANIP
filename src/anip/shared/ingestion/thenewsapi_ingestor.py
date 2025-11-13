"""
TheNewsAPI.com ingestor.
Pulls news articles from TheNewsAPI.com (free tier: 500 requests/day)
"""
import os
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from anip.shared.ingestion.base import BaseIngestor


class TheNewsAPIIngestor(BaseIngestor):
    """Pulls news articles from TheNewsAPI.com"""

    BASE_URL = "https://api.thenewsapi.com/v1/news/top"

    def __init__(self):
        self.api_key = os.getenv("THENEWSAPI_KEY")
        if not self.api_key:
            raise ValueError("THENEWSAPI_KEY environment variable is not set")

    def fetch(
        self,
        locale: str = "us",
        limit: int = 10,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch articles from TheNewsAPI.
        
        Args:
            locale: Locale code (e.g., "us", "gb", "sa", "fr")
            limit: Number of articles to fetch (max 50)
            search: Simple keyword search
            
        Returns:
            List of article dictionaries
        """
        params = {
            "api_token": self.api_key,
            "locale": locale,
            "limit": min(limit, 50)
        }
        
        if search:
            params["search"] = search

        response = requests.get(self.BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        articles = []
        for item in data.get("data", []):
            try:
                published_at = datetime.fromisoformat(item["published_at"].replace("Z", "+00:00"))
            except Exception:
                published_at = datetime.now(timezone.utc)
            
            article = {
                'title': item.get("title", "No Title"),
                'content': item.get("snippet") or item.get("description", ""),
                'source': item.get("source", "TheNewsAPI"),
                'author': None,
                'url': item.get("url"),
                'published_at': published_at,
                'language': item.get("language", "en"),
                'region': locale.upper(),
                'api_source': 'thenewsapi',
            }
            articles.append(article)

        return articles

