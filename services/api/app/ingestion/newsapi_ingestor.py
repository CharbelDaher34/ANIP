"""
NewsAPI.org ingestor.
Pulls news articles from NewsAPI.org
Docs: https://newsapi.org/docs/endpoints/top-headlines
"""

import requests
from typing import List
from datetime import datetime
from app.models.news import NewsArticleBase
from app.ingestion.base import BaseIngestor


class NewsAPIIngestor(BaseIngestor):
    """
    Pulls news articles from NewsAPI.org
    Docs: https://newsapi.org/docs/endpoints/top-headlines
    """

    BASE_URL = "https://newsapi.org/v2/top-headlines"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def fetch(self, query: str = "technology", country: str = "us", page_size: int = 10) -> List[NewsArticleBase]:
        """
        Fetch articles from NewsAPI.

        Args:
            query: Search query (default: "technology")
            country: 2-letter country code (default: "us")
            page_size: Number of articles to fetch (default: 10)

        Returns:
            List of NewsArticleBase objects
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
            article = NewsArticleBase(
                title=item.get("title", "No Title"),
                content=item.get("content") or item.get("description", ""),
                source=item.get("source", {}).get("name"),
                author=item.get("author"),
                url=item.get("url"),
                published_at=datetime.fromisoformat(item["publishedAt"].replace("Z", "+00:00"))
                if item.get("publishedAt") else None,
                language="en",
                region=country.upper()
            )
            articles.append(article)

        return articles

