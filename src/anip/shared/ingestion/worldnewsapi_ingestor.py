"""
WorldNewsAPI.com ingestor.
Pulls news articles from WorldNewsAPI.com (free tier: 100 requests/day)
"""
import os
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from anip.shared.ingestion.base import BaseIngestor


class WorldNewsAPIIngestor(BaseIngestor):
    """Pulls news articles from WorldNewsAPI.com"""

    BASE_URL = "https://api.worldnewsapi.com/search-news"

    def __init__(self):
        self.api_key = os.getenv("WORLDNEWS_KEY")
        if not self.api_key:
            raise ValueError("WORLDNEWS_KEY environment variable is not set")

    def fetch(
        self,
        text: str = "world",
        language: str = "en",
        number: int = 10,
        source_countries: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch articles from WorldNewsAPI.
        
        Args:
            text: Keyword search text
            language: Language code (e.g., "en", "ar", "fr")
            number: Number of articles to fetch (max 100)
            source_countries: Comma-separated country codes to restrict by
            
        Returns:
            List of article dictionaries
        """
        params = {
            "api-key": self.api_key,
            "text": text,
            "language": language,
            "number": min(number, 100)
        }
        
        if source_countries:
            params["source-countries"] = source_countries

        response = requests.get(self.BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        articles = []
        for item in data.get("news", []):
            try:
                published_at = datetime.fromisoformat(item["published"].replace("Z", "+00:00"))
            except Exception:
                published_at = datetime.now(timezone.utc)
            
            article = {
                'title': item.get("title", "No Title"),
                'content': item.get("summary") or item.get("text", ""),
                'source': "WorldNewsAPI",
                'author': item.get("author"),
                'url': item.get("url"),
                'published_at': published_at,
                'language': item.get("language", "en"),
                'region': item.get("source_country", "world").upper()
            }
            articles.append(article)

        return articles

