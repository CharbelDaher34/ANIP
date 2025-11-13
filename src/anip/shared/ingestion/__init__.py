# Ingestion package initialization

from anip.shared.ingestion.base import BaseIngestor
from anip.shared.ingestion.gdelt_ingestor import GDELTIngestor
from anip.shared.ingestion.newsapi_ingestor import NewsAPIIngestor
from anip.shared.ingestion.newsdata_ingestor import NewsDataIngestor
from anip.shared.ingestion.mediastack_ingestor import MediastackIngestor
from anip.shared.ingestion.thenewsapi_ingestor import TheNewsAPIIngestor
from anip.shared.ingestion.worldnewsapi_ingestor import WorldNewsAPIIngestor

__all__ = [
    "BaseIngestor",
    "GDELTIngestor",
    "NewsAPIIngestor",
    "NewsDataIngestor",
    "MediastackIngestor",
    "TheNewsAPIIngestor",
    "WorldNewsAPIIngestor",
]
