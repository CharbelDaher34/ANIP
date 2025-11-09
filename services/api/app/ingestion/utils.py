"""
Utility functions for ingestion.
"""

from typing import List
from app.models.news import NewsArticleBase


def deduplicate_articles(articles: List[NewsArticleBase]) -> List[NewsArticleBase]:
    """
    Remove duplicate articles based on URL.

    Args:
        articles: List of NewsArticleBase objects

    Returns:
        Deduplicated list of articles
    """
    seen_urls = set()
    unique_articles = []

    for article in articles:
        if article.url and article.url not in seen_urls:
            seen_urls.add(article.url)
            unique_articles.append(article)
        elif not article.url:
            unique_articles.append(article)

    return unique_articles


def filter_by_language(articles: List[NewsArticleBase], language: str = "en") -> List[NewsArticleBase]:
    """
    Filter articles by language.

    Args:
        articles: List of NewsArticleBase objects
        language: Language code to filter by (default: "en")

    Returns:
        Filtered list of articles
    """
    return [article for article in articles if article.language == language]

