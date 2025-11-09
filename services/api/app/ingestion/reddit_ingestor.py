"""
Reddit ingestor.
Pulls hot posts from Reddit's JSON API.
Example: https://www.reddit.com/r/worldnews/hot.json
"""

import requests
from typing import List
from datetime import datetime
from app.models.news import NewsArticleBase
from app.ingestion.base import BaseIngestor


class RedditIngestor(BaseIngestor):
    """
    Pulls hot posts from Reddit's JSON API.
    Example: https://old.reddit.com/r/worldnews/hot.json
    """

    BASE_URL = "https://old.reddit.com/r/{subreddit}/hot.json"

    def fetch(self, subreddit: str = "worldnews", limit: int = 10) -> List[NewsArticleBase]:
        """
        Fetch hot posts from a subreddit.

        Args:
            subreddit: Subreddit name (default: "worldnews")
            limit: Number of posts to fetch (default: 10)

        Returns:
            List of NewsArticleBase objects
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; ANIP-NewsBot/1.0; +https://github.com/anip)"
        }
        params = {"limit": limit}

        response = requests.get(
            self.BASE_URL.format(subreddit=subreddit),
            headers=headers,
            params=params,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        articles = []
        for post in data["data"]["children"]:
            info = post["data"]
            article = NewsArticleBase(
                title=info.get("title"),
                content=info.get("selftext", ""),
                source=f"r/{subreddit}",
                author=info.get("author"),
                url=f"https://www.reddit.com{info.get('permalink')}",
                published_at=datetime.utcfromtimestamp(info["created_utc"]),
                language="en",
                region=None
            )
            articles.append(article)

        return articles

