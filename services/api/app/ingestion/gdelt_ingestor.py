"""
GDELT ingestor.
Pulls latest GDELT event data (CSV feed).
Docs: https://blog.gdeltproject.org/gdelt-2-0-our-global-world-in-realtime/
"""

import requests
import pandas as pd
from typing import List
from datetime import datetime
from app.models.news import NewsArticleBase
from app.ingestion.base import BaseIngestor


class GDELTIngestor(BaseIngestor):
    """
    Pulls latest GDELT event data (CSV feed).
    Docs: https://blog.gdeltproject.org/gdelt-2-0-our-global-world-in-realtime/
    """

    URL = "http://data.gdeltproject.org/gdeltv2/lastupdate.txt"

    def fetch(self, limit: int = 10) -> List[NewsArticleBase]:
        """
        Fetch latest GDELT events.

        Args:
            limit: Number of events to fetch (default: 10)

        Returns:
            List of NewsArticleBase objects
        """
        # Get latest CSV file from the GDELT index
        resp = requests.get(self.URL, timeout=10)
        csv_url = resp.text.strip().split("\n")[-1].split(" ")[-1]

        df = pd.read_csv(csv_url, sep="\t", header=None, nrows=limit)

        articles = []
        for _, row in df.iterrows():
            # Helper function to safely get string values
            def safe_str(value, default=""):
                if pd.isna(value):
                    return default
                return str(value)
            
            # Skip if title is missing
            title = safe_str(row[5] if len(row) > 5 else None, "GDELT Event")
            if not title or title == "GDELT Event":
                continue
            
            article = NewsArticleBase(
                title=title,
                content=safe_str(row[6] if len(row) > 6 else None, ""),
                source=safe_str(row[3] if len(row) > 3 else None, "GDELT"),
                author=None,
                url=safe_str(row[57] if len(row) > 57 else None, None) or None,
                published_at=datetime.utcnow(),
                language="en",
                region=safe_str(row[51] if len(row) > 51 else None, None) or None
            )
            articles.append(article)

        return articles

