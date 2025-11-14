"""
Pydantic AI Agents for ANIP.

This module contains intelligent agents built with Pydantic AI for various tasks.
"""
from anip.agent.news_agent import (
    news_agent,
    search_news,
    NewsAgentDependencies,
    NewsAgentOutput,
    NewsSearchResult,
)

__all__ = [
    "news_agent",
    "search_news",
    "NewsAgentDependencies",
    "NewsAgentOutput",
    "NewsSearchResult",
]

