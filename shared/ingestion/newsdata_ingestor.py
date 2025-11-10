"""
NewsData.io ingestor.
Pulls news articles from NewsData.io
"""
import requests
from typing import List, Dict, Any
from datetime import datetime, timezone
from shared.ingestion.base import BaseIngestor


class NewsDataIngestor(BaseIngestor):
    """Pulls news articles from NewsData.io"""

    BASE_URL = "https://newsdata.io/api/1/news"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def fetch(self, query: str = "technology", country: str = "us", page_size: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch articles from NewsData.io.
        
        Args:
            query: Search query
            country: 2-letter country code
            page_size: Number of articles to fetch
            
        Returns:
            List of article dictionaries
        """
        params = {
            "q": query,
            "country": country,
            "language": "en",
            "apikey": self.api_key
        }

        response = requests.get(self.BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        articles = []
        for item in data.get("results", []):
            article = {
                'title': item.get("title", "No Title"),
                'content': item.get("content") or item.get("description", ""),
                'source': item.get("source_id", "NewsData"),
                'author': item.get("creator", [None])[0] if item.get("creator") else None,
                'url': item.get("link"),
                'published_at': datetime.fromisoformat(item["pubDate"].replace("Z", "+00:00"))
                if item.get("pubDate") else datetime.now(timezone.utc),
                'language': item.get("language", "en"),
                'region': country.upper()
            }
            articles.append(article)

        return articles

