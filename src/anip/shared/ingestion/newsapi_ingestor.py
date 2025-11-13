"""
NewsAPI.org ingestor.
Pulls news articles from the /v2/everything endpoint (free-tier compatible).
"""

import os
import requests
from typing import List, Dict, Any
from datetime import datetime, timezone
from anip.shared.ingestion.base import BaseIngestor


class NewsAPIIngestor(BaseIngestor):
    """Pulls news articles from NewsAPI.org (free tier)."""

    BASE_URL = "https://newsapi.org/v2/everything"

    def __init__(self):
        self.api_key = os.getenv("NEWSAPI_KEY")
        if not self.api_key:
            raise ValueError("NEWSAPI_KEY environment variable is not set")

    def fetch(
        self,
        query: str = "artificial intelligence news",
        page_size: int = 10,
        page: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Fetch articles from NewsAPI using the free-tier compatible endpoint (/everything).

        Args:
            query: Search query (default: artificial intelligence news)
            page_size: Number of articles to fetch (max 100)
            page: Page number

        Returns:
            List of article dictionaries.
        """

        params = {
            "q": query,
            "pageSize": min(page_size, 100),
            "page": page,
            "apiKey": self.api_key
        }

        response = requests.get(self.BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Debug print (optional)
        # import json
        # print(json.dumps(data, indent=4))

        articles = []
        for item in data.get("articles", []):
            article = {
                "title": item.get("title", "No Title"),
                "content": item.get("content") or item.get("description", ""),
                "source": item.get("source", {}).get("name", "NewsAPI"),
                "author": item.get("author"),
                "url": item.get("url"),
                "published_at": datetime.fromisoformat(
                    item["publishedAt"].replace("Z", "+00:00")
                ) if item.get("publishedAt") else datetime.now(timezone.utc),
                "language": item.get("language", "en"),
                "region": "GLOBAL",
            }
            articles.append(article)

        return articles


# Manual test
if __name__ == "__main__":
    ingestor = NewsAPIIngestor()
    articles = ingestor.fetch()
    from pprint import pprint
    pprint(articles[:3])
