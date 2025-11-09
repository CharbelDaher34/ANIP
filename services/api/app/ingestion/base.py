"""Abstract base class for all news ingestors."""

from abc import ABC, abstractmethod
from typing import List
from app.models.news import NewsArticleBase


class BaseIngestor(ABC):
    """Abstract base class for all news ingestors."""

    @abstractmethod
    def fetch(self, **kwargs) -> List[NewsArticleBase]:
        """Fetch and return a list of NewsArticleBase objects."""
        ...

