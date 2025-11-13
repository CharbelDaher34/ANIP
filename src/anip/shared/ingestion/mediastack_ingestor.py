"""
Mediastack ingestor.
Pulls news articles from Mediastack (free tier: 500 requests/month)
"""
import os
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from anip.shared.ingestion.base import BaseIngestor


class MediastackIngestor(BaseIngestor):
    """Pulls news articles from Mediastack"""

    BASE_URL = "http://api.mediastack.com/v1/news"  # HTTP required for free tier

    def __init__(self):
        self.api_key = os.getenv("MEDIASTACK_KEY")
        if not self.api_key:
            raise ValueError("MEDIASTACK_KEY environment variable is not set")

    def fetch(
        self,
        countries: str = "us",
        languages: Optional[str] = None,
        limit: int = 10,
        keywords: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch articles from Mediastack.
        
        Args:
            countries: Comma-separated country codes (e.g., "us", "fr", "sa")
            languages: Comma-separated language codes (optional, e.g., "en", "ar")
            limit: Number of articles to fetch
            keywords: Simple keywords to search for
            
        Returns:
            List of article dictionaries
            
        Note:
            - Free tier only works over HTTP (not HTTPS)
            - Free tier may have limited parameter support
            - Minimal working request needs: access_key, countries, limit
        """
        # Minimal parameters for free tier compatibility
        params = {
            "access_key": self.api_key,
            "countries": countries,
            "limit": limit
        }
        
        # Only add optional parameters if provided
        if languages:
            params["languages"] = languages
        if keywords:
            params["keywords"] = keywords

        response = requests.get(self.BASE_URL, params=params, timeout=10)
        
        # Better error handling for 401
        if response.status_code == 401:
            error_msg = f"Mediastack API Error 401: {response.text}"
            raise ValueError(
                f"{error_msg}\n"
                "Common causes:\n"
                "1. API key is invalid or expired - check your dashboard\n"
                "2. Make sure you're using HTTP (not HTTPS) for free tier\n"
                "3. Verify your key is correct: {self.api_key[:10]}..."
            )
        
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
                'content': item.get("description", ""),
                'source': item.get("source", "Mediastack"),
                'author': item.get("author"),
                'url': item.get("url"),
                'published_at': published_at,
                'language': item.get("language", "en"),
                'region': item.get("country", "us").upper(),
                'api_source': 'mediastack',
            }
            articles.append(article)

        return articles

