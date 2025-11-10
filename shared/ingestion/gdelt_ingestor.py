"""
GDELT ingestor.
Pulls news articles from GDELT Project
"""
import requests
from typing import List, Dict, Any
from datetime import datetime, timezone
from shared.ingestion.base import BaseIngestor


class GDELTIngestor(BaseIngestor):
    """Pulls news articles from GDELT Project"""

    BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

    def fetch(self, query: str = "technology", max_records: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch articles from GDELT.
        
        Args:
            query: Search query
            max_records: Maximum number of articles to fetch
            
        Returns:
            List of article dictionaries
        """
        params = {
            "query": query,
            "mode": "artlist",
            "maxrecords": max_records,
            "format": "json"
        }

        response = requests.get(self.BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        articles = []
        for item in data.get("articles", []):
            article = {
                'title': item.get("title", "No Title"),
                'content': item.get("seendate", ""),  # GDELT doesn't provide full content
                'source': item.get("domain", "GDELT"),
                'author': None,
                'url': item.get("url"),
                'published_at': datetime.fromisoformat(item["seendate"][:8])
                if item.get("seendate") else datetime.now(timezone.utc),
                'language': item.get("language", "en"),
                'region': "WORLD"
            }
            articles.append(article)

        return articles

