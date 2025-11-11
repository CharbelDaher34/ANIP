"""
NewsAPI.org ingestor.
Pulls news articles from NewsAPI.org
"""
import requests
from typing import List, Dict, Any
from datetime import datetime, timezone
from anip.shared.ingestion.base import BaseIngestor


class NewsAPIIngestor(BaseIngestor):
    """Pulls news articles from NewsAPI.org"""

    BASE_URL = "https://newsapi.org/v2/top-headlines"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def fetch(self, query: str = "technology", country: str = "us", page_size: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch articles from NewsAPI.
        
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
            "pageSize": page_size,
            "apiKey": self.api_key
        }

        response = requests.get(self.BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        articles = []
        for item in data.get("articles", []):
            article = {
                'title': item.get("title", "No Title"),
                'content': item.get("content") or item.get("description", ""),
                'source': item.get("source", {}).get("name", "NewsAPI"),
                'author': item.get("author"),
                'url': item.get("url"),
                'published_at': datetime.fromisoformat(item["publishedAt"].replace("Z", "+00:00"))
                if item.get("publishedAt") else datetime.now(timezone.utc),
                'language': "en",
                'region': country.upper()
            }
            articles.append(article)

        return articles

