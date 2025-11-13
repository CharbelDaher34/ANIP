"""
GDELT DOC API Ingestor (Clean Version)
--------------------------------------
- No language filtering
- No query cleaning
- No modifications to the user query
- Fully stable with GDELT doc/doc endpoint
"""

import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from anip.shared.ingestion.base import BaseIngestor
from anip.shared.ingestion.utils import normalize_language_code, normalize_country_code


class GDELTIngestor(BaseIngestor):
    """Pulls news articles from the GDELT Doc API."""

    BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

    def fetch(
        self,
        query: str = "technology",
        max_records: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Fetch articles from GDELT.

        Args:
            query (str): Raw user query. Passed exactly as-is.
            max_records (int): Maximum number of articles.

        Returns:
            List[Dict[str, Any]]: Normalized article objects.
        """

        # Ensure query is not empty (GDELT rejects empty queries)
        if not query or not query.strip():
            query = "news"

        params = {
            "query": query,          # RAW QUERY (no modification)
            "mode": "artlist",
            "maxrecords": max_records,
            "format": "json"
        }

        response = requests.get(self.BASE_URL, params=params, timeout=10)

        # Raise HTTP errors (429, 500, etc.)
        response.raise_for_status()

        # GDELT often returns HTML when errors occur → avoid crash
        try:
            data = response.json()
        except ValueError:
            print("❗ GDELT returned non-JSON output:")
            print(response.text[:500])
            return []

        # Parse the "articles" list safely
        articles = []
        for item in data.get("articles", []):
            articles.append(self._build_article(item))

        return articles

    # -----------------------------------------------------------
    # Build article schema
    # -----------------------------------------------------------
    def _build_article(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize GDELT article object into ANIP schema."""
        
        # GDELT doesn't provide full content, use social image URL or empty
        # Note: In production, you may want to scrape the URL for content
        content = item.get("socialimage", "")

        return {
            "title": item.get("title", "No Title"),
            "content": content if content and not content.startswith("http") else "",
            "source": item.get("domain", "GDELT"),
            "author": None,
            "url": item.get("url"),
            "published_at": self._parse_gdelt_date(item.get("seendate")),
            "language": normalize_language_code(item.get("language", "en")),
            "region": normalize_country_code(item.get("sourcecountry", "WORLD")),
        }

    # -----------------------------------------------------------
    # Handle GDELT timestamp formats
    # -----------------------------------------------------------
    def _parse_gdelt_date(self, s: Optional[str]) -> datetime:
        """
        GDELT timestamps:
        - YYYYMMDDHHMMSS
        - YYYYMMDD
        """

        if not s:
            return datetime.now(timezone.utc)

        try:
            return datetime.strptime(s, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
        except:
            try:
                return datetime.strptime(s[:8], "%Y%m%d").replace(tzinfo=timezone.utc)
            except:
                return datetime.now(timezone.utc)


# Manual test
if __name__ == "__main__":
    ingestor = GDELTIngestor()
    results = ingestor.fetch(query="technology", max_records=1)
    from pprint import pprint
    pprint(results)
