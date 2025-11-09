"""
News ingestion module.
Contains modular, testable ingestors for various news sources.
"""

from app.ingestion.base import BaseIngestor
from app.ingestion.newsapi_ingestor import NewsAPIIngestor
from app.ingestion.reddit_ingestor import RedditIngestor
from app.ingestion.gdelt_ingestor import GDELTIngestor

__all__ = [
    "BaseIngestor",
    "NewsAPIIngestor",
    "RedditIngestor",
    "GDELTIngestor",
]

