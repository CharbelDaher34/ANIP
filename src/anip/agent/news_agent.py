"""
Pydantic AI Agent for News Intelligence.

This agent can search for news using DuckDuckGo and query the internal news database
with semantic search capabilities.
"""
import logging
from dataclasses import dataclass
from typing import Optional, List

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from ddgs import DDGS

from anip.shared.database import get_db_session

logger = logging.getLogger(__name__)


@dataclass
class NewsAgentDependencies:
    """
    Dependencies for the News Agent.
    
    These are injected into tools and dynamic instructions to provide
    access to the database and external APIs. Also tracks tool outputs.
    """
    user_query: str
    max_results: int = 5
    search_provider: str = "duckduckgo"  # or "database"
    
    # Tool result tracking (populated by tools)
    duckduckgo_results: List[dict] = None
    database_results: List[dict] = None
    
    def __post_init__(self):
        """Initialize result tracking lists."""
        if self.duckduckgo_results is None:
            self.duckduckgo_results = []
        if self.database_results is None:
            self.database_results = []


class NewsSearchResult(BaseModel):
    """Single news article result."""
    title: str = Field(description="Article title")
    url: str = Field(description="Article URL")
    content: Optional[str] = Field(None, description="Article content")
    source: Optional[str] = Field(None, description="News source")
    published_at: Optional[str] = Field(None, description="Publication date")
    topic: Optional[str] = Field(None, description="Article topic/category")
    sentiment: Optional[str] = Field(None, description="Article sentiment")
    relevance_score: Optional[float] = Field(None, description="Relevance score (0-1)")


class AgentAnalysis(BaseModel):
    """
    LLM-generated analysis from the News Agent.
    
    This model contains ONLY the fields that the LLM should generate.
    Actual search results are populated programmatically from tool outputs.
    """
    summary: str = Field(description="Brief summary of findings from all sources")
    answer: str = Field(description="Comprehensive answer to the user's question synthesizing all search results")
    query_intent: str = Field(
        description="Interpreted intent of the user query (e.g., 'Breaking news search', 'Historical research')"
    )


class NewsAgentOutput(BaseModel):
    """
    Structured output from the News Agent.
    
    This model defines the final response format that the agent will return
    after processing the user's query.
    """
    summary: str = Field(description="Comprehensive summary of all findings from both DuckDuckGo and database")
    answer: str = Field(description="Complete answer to the user's question based on all search results")
    duckduckgo_results: List[NewsSearchResult] = Field(
        description="Results from DuckDuckGo search",
        default_factory=list
    )
    database_results: List[NewsSearchResult] = Field(
        description="Results from internal database search",
        default_factory=list
    )
    sources_used: List[str] = Field(
        description="List of sources searched (e.g., 'DuckDuckGo', 'Internal Database')",
        default_factory=list
    )
    query_intent: str = Field(
        description="Interpreted intent of the user query (e.g., 'Breaking news search', 'Historical research')"
    )
    total_results: int = Field(description="Total number of results found", ge=0)
    duckduckgo_count: int = Field(description="Number of results from DuckDuckGo", ge=0, default=0)
    database_count: int = Field(description="Number of results from database", ge=0, default=0)


# Initialize the News Agent
news_agent = Agent(
    'openai:gpt-4o',  # Can be changed to other models
    deps_type=NewsAgentDependencies,
    output_type=AgentAnalysis,
    instructions=(
        'You are an intelligent news research assistant. Your role is to help users find '
        'relevant news articles by searching both external sources (DuckDuckGo) and the '
        'internal news database. '
        '\n\n'
        'WORKFLOW:\n'
        '1. ALWAYS use BOTH search tools: search_duckduckgo() AND search_news_database()\n'
        '2. For database search, extract relevant keywords and topics from the user query\n'
        '3. Analyze all results from both sources\n'
        '\n'
        'YOUR OUTPUT (3 fields only):\n'
        '1. "summary": Brief overview of what was found across all sources\n'
        '2. "answer": Comprehensive answer synthesizing information from ALL search results\n'
        '3. "query_intent": Your interpretation of what the user is looking for\n'
        '\n'
        'IMPORTANT:\n'
        '- Do NOT include the raw search results in your output\n'
        '- The actual search results will be preserved programmatically\n'
        '- Focus on providing insightful analysis and synthesis\n'
        '\n'
        'SEARCH STRATEGY:\n'
        '- For real-time/breaking news: Use DuckDuckGo\n'
        '- For analyzed articles with topics/sentiment: Use database with relevant filters\n'
        '- ALWAYS try both sources to provide complete information'
    ),
)


@news_agent.instructions
async def add_search_context(ctx: RunContext[NewsAgentDependencies]) -> str:
    """Add dynamic context about the user's search preferences."""
    return (
        f"User is searching for: {ctx.deps.user_query}\n"
        f"Maximum results requested: {ctx.deps.max_results}\n"
        f"Preferred search provider: {ctx.deps.search_provider}"
    )


@news_agent.tool
async def search_duckduckgo(
    ctx: RunContext[NewsAgentDependencies],
    query: str,
    max_results: Optional[int] = None
) -> List[dict]:
    """
    Search for news articles using DuckDuckGo.
    
    Use this tool when:
    - Looking for breaking news or recent events
    - Searching for articles not in the internal database
    - Need real-time/up-to-date information
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return (default: from dependencies)
    
    Returns:
        List of news articles from DuckDuckGo with title, url, and snippet
    """
    import asyncio
    
    limit = max_results or ctx.deps.max_results
    
    def _search_sync():
        """Synchronous search wrapped for async execution."""
        try:
            parsed_results = []
            
            with DDGS() as ddgs:
                raw_results = ddgs.text(
                    query=query,
                    max_results=limit
                )
                
                for item in raw_results:
                    parsed_results.append({
                        "title": item.get("title", ""),
                        "url": item.get("href", ""),
                        "content": item.get("body", ""),
                        "source": "DuckDuckGo",
                        "published_at": None,
                        "topic": None,
                        "sentiment": None,
                        "sentiment_score": None,
                        "relevance_score": None,
                    })
            
            return parsed_results if parsed_results else [{
                "title": f"No results found for: {query}",
                "url": f"https://duckduckgo.com/?q={query.replace(' ', '+')}",
                "content": "Try searching directly on DuckDuckGo.",
                "source": "DuckDuckGo",
                "published_at": None,
                "topic": None,
                "sentiment": None,
                "sentiment_score": None,
                "relevance_score": None,
            }]
            
        except Exception as e:
            return [{
                "title": f"Search error for: {query}",
                "url": f"https://duckduckgo.com/?q={query.replace(' ', '+')}",
                "content": f"Error: {str(e)}. Try searching directly on DuckDuckGo.",
                "source": "DuckDuckGo",
                "published_at": None,
                "topic": None,
                "sentiment": None,
                "sentiment_score": None,
                "relevance_score": None,
            }]
    
    # Run synchronous function in thread pool to avoid blocking
    results = await asyncio.to_thread(_search_sync)
    
    # Track results in dependencies
    ctx.deps.duckduckgo_results.extend(results)
    
    return results


@news_agent.tool
async def search_news_database(
    ctx: RunContext[NewsAgentDependencies],
    query: str,
    topic: Optional[str] = None,
    sentiment: Optional[str] = None,
    max_results: Optional[int] = None,
    similarity_threshold: float = 0.4
) -> List[dict]:
    """
    Search the internal news database using semantic search with embeddings.
    
    IMPORTANT: This searches YOUR database with ML-analyzed articles using semantic similarity.
    Always try this tool to find relevant articles from your collection.
    
    Uses pgvector's optimized cosine similarity for fast, accurate results.
    
    Use this tool when:
    - Looking for articles with specific topics (Technology, Politics, Business, Health, World, etc.)
    - Filtering by sentiment (positive, negative, neutral)
    - Searching analyzed content with ML predictions
    - Need semantically similar articles based on meaning, not just keywords
    
    Args:
        query: Search query for semantic similarity matching (natural language question)
        topic: Filter by topic - Available: Technology, Politics, Business, Health, World, Sports, Entertainment
        sentiment: Filter by sentiment ('positive', 'negative', 'neutral')
        max_results: Maximum number of results to return (default: from dependencies)
        similarity_threshold: Minimum similarity score (0.0-1.0, default: 0.4 = moderately similar)
    
    Returns:
        List of relevant news articles from the database with similarity scores >= threshold
        Sorted by relevance (highest similarity first)
        Returns empty list [] if no matches found (this is OK, not an error)
    """
    limit = max_results or ctx.deps.max_results
    
    logger.info(f"🔍 Database search - Query: '{query}', Threshold: {similarity_threshold}, Topic: {topic}, Sentiment: {sentiment}")
    
    try:
        with get_db_session() as session:
            # Use shared similarity search function (same as API for consistent results)
            from anip.shared.utils.similarity_search import search_similar_articles
            
            similar_articles = search_similar_articles(
                query=query,
                session=session,
                limit=limit,
                similarity_threshold=similarity_threshold,
                topic=topic,
                sentiment=sentiment
            )
            
            if not similar_articles:
                logger.info("⚠️  No articles found matching criteria - returning empty results")
                return []
            
            # Convert to agent-compatible format
            results = []
            for article in similar_articles:
                results.append({
                    "title": article["title"],
                    "url": article["url"],
                    "content": article.get("content"),
                    "source": article.get("source") or "Internal Database",
                    "published_at": article["published_at"].isoformat() if article.get("published_at") else None,
                    "topic": article.get("topic"),
                    "sentiment": article.get("sentiment"),
                    "sentiment_score": article.get("sentiment_score"),
                    "relevance_score": article["similarity_score"],
                })
            
            # Track results in dependencies
            ctx.deps.database_results.extend(results)
            
            logger.info(f"🎯 Returning {len(results)} database results")
            return results
            
    except Exception as e:
        logger.error(f"❌ Database search error: {str(e)}", exc_info=True)
        return []  # Return empty list on error, don't fail the entire agent


# Example usage function
async def search_news(
    query: str,
    max_results: int = 5,
    search_provider: str = "both"
) -> NewsAgentOutput:
    """
    Search for news using the News Agent.
    
    Args:
        query: User's search query
        max_results: Maximum number of results to return
        search_provider: "duckduckgo", "database", or "both"
    
    Returns:
        Structured news search results with LLM analysis and actual tool results
    """
    deps = NewsAgentDependencies(
        user_query=query,
        max_results=max_results,
        search_provider=search_provider
    )
    
    # Run agent - this populates deps with tool results and returns LLM analysis
    result = await news_agent.run(query, deps=deps)
    llm_analysis: AgentAnalysis = result.output
    
    # Construct final output by combining LLM analysis with actual tool results
    sources_used = []
    if deps.duckduckgo_results:
        sources_used.append("DuckDuckGo")
    if deps.database_results:
        sources_used.append("Internal Database")
    
    return NewsAgentOutput(
        # LLM-generated fields
        summary=llm_analysis.summary,
        answer=llm_analysis.answer,
        query_intent=llm_analysis.query_intent,
        # Programmatically populated from actual tool outputs
        duckduckgo_results=[NewsSearchResult(**r) for r in deps.duckduckgo_results],
        database_results=[NewsSearchResult(**r) for r in deps.database_results],
        # Metadata
        sources_used=sources_used,
        total_results=len(deps.duckduckgo_results) + len(deps.database_results),
        duckduckgo_count=len(deps.duckduckgo_results),
        database_count=len(deps.database_results)
    )


# Example for running the agent
if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Example 1: Search for AI news
        print("=" * 70)
        print("Example 1: Searching for AI news")
        print("=" * 70)
        result = await search_news("artificial intelligence breakthroughs", max_results=3)
        print(f"\nSummary: {result.summary}")
        print(f"Intent: {result.query_intent}")
        print(f"Sources: {', '.join(result.sources_used)}")
        print(f"\nFound {result.total_results} articles:")
        
        # Show DuckDuckGo results
        if result.duckduckgo_results:
            print(f"\nDuckDuckGo Results ({len(result.duckduckgo_results)}):")
            for i, article in enumerate(result.duckduckgo_results, 1):
                print(f"\n{i}. {article.title}")
                print(f"   Source: {article.source}")
                print(f"   URL: {article.url}")
        
        # Show database results
        if result.database_results:
            print(f"\nDatabase Results ({len(result.database_results)}):")
            for i, article in enumerate(result.database_results, 1):
                print(f"\n{i}. {article.title}")
                print(f"   Source: {article.source}")
                print(f"   URL: {article.url}")
                if article.relevance_score:
                    print(f"   Relevance: {article.relevance_score:.2%}")
        
        # Example 2: Search database for technology news
        print("\n" + "=" * 70)
        print("Example 2: Searching database for technology news")
        print("=" * 70)
        result = await search_news(
            "machine learning innovations",
            max_results=3,
            search_provider="database"
        )
        print(f"\nSummary: {result.summary}")
        print(f"Answer: {result.answer}")
        print(f"Found {result.total_results} articles from database")
    
    asyncio.run(main())

