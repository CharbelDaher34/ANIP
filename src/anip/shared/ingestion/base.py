"""
Base ingestor class for all news sources.
"""
from typing import List, Dict, Any
from abc import ABC, abstractmethod


class BaseIngestor(ABC):
    """Base class for all news ingestors."""
    
    @abstractmethod
    def fetch(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Fetch articles from the news source.
        
        Returns:
            List of article dictionaries
        """
        pass

