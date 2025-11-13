"""
NewsData.io ingestor.
Pulls news articles from NewsData.io (free tier: 200 calls/day)
"""
import os
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from anip.shared.ingestion.base import BaseIngestor
from anip.shared.ingestion.utils import normalize_language_code


class NewsDataIngestor(BaseIngestor):
    """Pulls news articles from NewsData.io"""

    BASE_URL = "https://newsdata.io/api/1/news"

    def __init__(self):
        self.api_key = os.getenv("NEWSDATA_KEY")
        if not self.api_key:
            raise ValueError("NEWSDATA_KEY environment variable is not set")

    def fetch(
        self,
        country: str = "us",
        language: str = "en",
        q: Optional[str] = None,
        category: str = "top",
        page: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch articles from NewsData.io.
        
        Args:
            country: 2-letter country code (e.g., "us", "ae", "sa", "fr")
            language: Language code (e.g., "en", "ar", "fr")
            q: Simple keyword search
            category: Category (e.g., "business", "sports", "top"). Default: "top"
            page: Page cursor from previous response (optional, for pagination)
            
        Returns:
            List of article dictionaries
            
        Note:
            - Free tier requires a primary key (pri_xxx), not public key (pub_xxx)
            - Page parameter uses cursor strings from API responses, not integers
            - Some parameter combinations may not work on free tier
        """
        params = {
            "apikey": self.api_key,
            # "country": country,
            # "language": language,
            # "category": category
        }
        
        if q:
            params["q"] = q
        if page:
            params["page"] = page

        response = requests.get(self.BASE_URL, params=params, timeout=10)
        
        # Better error handling for 422
        if response.status_code == 422:
            error_msg = f"NewsData API Error 422: {response.text}"
            raise ValueError(
                f"{error_msg}\n"
                "Common causes:\n"
                "1. You may be using a public key (pub_xxx) - try primary key (pri_xxx)\n"
                "2. Your plan may not support pagination or certain parameters\n"
                "3. Try removing optional parameters or changing country/language combination"
            )
        
        response.raise_for_status()
        data = response.json()

        articles = []
        for item in data.get("results", []):
            pub_date = item.get("pubDate", "")
            try:
                if " " in pub_date:
                    published_at = datetime.strptime(pub_date, "%Y-%m-%d %H:%M:%S")
                    published_at = published_at.replace(tzinfo=timezone.utc)
                else:
                    published_at = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
            except Exception:
                published_at = datetime.now(timezone.utc)
            
            article = {
                'title': item.get("title", "No Title"),
                'content': item.get("content") or item.get("description", ""),
                'source': item.get("source_id", "NewsData"),
                'author': item.get("creator", [None])[0] if item.get("creator") else None,
                'url': item.get("link"),
                'published_at': published_at,
                'language': normalize_language_code(item.get("language", "en")),
                'region': country.upper()
            }
            articles.append(article)

        return articles

