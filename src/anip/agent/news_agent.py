"""
Pydantic AI Agent for News Intelligence.

This agent can search for news using DuckDuckGo and query the internal news database
with semantic search capabilities.
"""
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from ddgs import DDGS

from anip.shared.database import get_db_session
from anip.shared.models.news import NewsArticle
from anip.ml.embedding import generate_embedding

logger = logging.getLogger(__name__)


@dataclass
class NewsAgentDependencies:
    """
    Dependencies for the News Agent.
    
    These are injected into tools and dynamic instructions to provide
    access to the database and external APIs.
    """
    user_query: str
    max_results: int = 5
    search_provider: str = "duckduckgo"  # or "database"


class NewsSearchResult(BaseModel):
    """Single news article result."""
    title: str = Field(description="Article title")
    url: str = Field(description="Article URL")
    snippet: Optional[str] = Field(None, description="Article snippet or summary")
    source: Optional[str] = Field(None, description="News source")
    published_at: Optional[str] = Field(None, description="Publication date")
    topic: Optional[str] = Field(None, description="Article topic/category")
    sentiment: Optional[str] = Field(None, description="Article sentiment")
    relevance_score: Optional[float] = Field(None, description="Relevance score (0-1)")


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
    output_type=NewsAgentOutput,
    instructions=(
        'You are an intelligent news research assistant. Your role is to help users find '
        'relevant news articles by searching both external sources (DuckDuckGo) and the '
        'internal news database. '
        '\n\n'
        'When responding to queries:\n'
        '1. ALWAYS use BOTH search tools: search_duckduckgo() AND search_news_database()\n'
        '2. For database search, extract relevant keywords and topics from the user query\n'
        '3. Organize results strictly by source - DO NOT mix them\n'
        '4. Provide TWO outputs:\n'
        '   - "summary": Brief overview of what was found\n'
        '   - "answer": Complete, detailed answer synthesizing information from ALL results\n'
        '\n'
        'CRITICAL OUTPUT STRUCTURE:\n'
        '- "duckduckgo_results": ONLY results from search_duckduckgo() tool\n'
        '- "database_results": ONLY results from search_news_database() tool\n'
        '- "duckduckgo_count": Count of DuckDuckGo results\n'
        '- "database_count": Count of database results\n'
        '- "total_results": Sum of both counts\n'
        '- "sources_used": List which sources you actually searched\n'
        '- "answer": Comprehensive answer using information from BOTH sources\n'
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
                        "snippet": item.get("body", ""),
                        "source": "DuckDuckGo",
                        "published_at": None,
                    })
            
            return parsed_results if parsed_results else [{
                "title": f"No results found for: {query}",
                "url": f"https://duckduckgo.com/?q={query.replace(' ', '+')}",
                "snippet": "Try searching directly on DuckDuckGo.",
                "source": "DuckDuckGo",
                "published_at": None,
            }]
            
        except Exception as e:
            return [{
                "title": f"Search error for: {query}",
                "url": f"https://duckduckgo.com/?q={query.replace(' ', '+')}",
                "snippet": f"Error: {str(e)}. Try searching directly on DuckDuckGo.",
                "source": "DuckDuckGo",
                "published_at": None,
            }]
    
    # Run synchronous function in thread pool to avoid blocking
    return await asyncio.to_thread(_search_sync)


@news_agent.tool
async def search_news_database(
    ctx: RunContext[NewsAgentDependencies],
    query: str,
    topic: Optional[str] = None,
    sentiment: Optional[str] = None,
    max_results: Optional[int] = None,
    similarity_threshold: float = 0.2
) -> List[dict]:
    """
    Search the internal news database using semantic search with embeddings.
    
    IMPORTANT: This searches YOUR database with ML-analyzed articles using semantic similarity.
    Always try this tool to find relevant articles from your collection.
    
    Uses cosine similarity on embeddings to find semantically similar articles.
    
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
        similarity_threshold: Minimum cosine similarity (0.0-1.0, default: 0.5 = moderate match)
    
    Returns:
        List of relevant news articles from the database with similarity scores >= threshold
        Sorted by relevance (highest similarity first)
        Returns empty list [] if no matches found (this is OK, not an error)
    """
    limit = max_results or ctx.deps.max_results
    
    logger.info(f"🔍 Database search - Query: '{query}', Threshold: {similarity_threshold}, Topic: {topic}, Sentiment: {sentiment}")
    
    try:
        with get_db_session() as session:
            logger.info("📊 Generating query embedding...")
            query_embedding = generate_embedding(query)
            
            if query_embedding is None:
                logger.warning("❌ Failed to generate query embedding - returning empty results")
                return []
            
            logger.info(f"✅ Query embedding generated - Shape: {len(query_embedding) if query_embedding else 0}")
            
            # Build query with filters - only get articles with embeddings
            db_query = select(NewsArticle).filter(NewsArticle.embedding.isnot(None))
            
            # Apply optional filters
            if topic:
                logger.info(f"🔖 Filtering by topic: {topic}")
                db_query = db_query.filter(NewsArticle.topic == topic)
            if sentiment:
                logger.info(f"😊 Filtering by sentiment: {sentiment}")
                db_query = db_query.filter(NewsArticle.sentiment == sentiment)
            
            # Get all articles matching filters
            logger.info("📚 Querying database for articles with embeddings...")
            articles = session.execute(db_query).scalars().all()
            
            logger.info(f"📊 Found {len(articles)} articles with embeddings in database")
            
            if not articles:
                logger.warning("⚠️  No articles with embeddings found - returning empty results")
                return []
            
            # Calculate cosine similarity for each article
            import numpy as np
            
            logger.info(f"🧮 Calculating similarity scores (threshold: {similarity_threshold})...")
            results = []
            similarity_scores = []
            
            for i, article in enumerate(articles):
                # Check if embedding exists and is not empty
                if article.embedding is not None:
                    try:
                        # Convert to numpy arrays
                        emb1 = np.array(query_embedding)
                        emb2 = np.array(article.embedding)
                        
                        # Check if arrays are not empty
                        if len(emb1) == 0 or len(emb2) == 0:
                            logger.warning(f"⚠️  Article {i+1} has empty embedding - skipping")
                            continue
                        
                        # Validate embedding dimensions match
                        if len(emb1) != len(emb2):
                            logger.warning(f"⚠️  Article {i+1} embedding dimension mismatch: query={len(emb1)}, article={len(emb2)}")
                            continue
                        
                        # Check for zero or near-zero embeddings
                        norm1 = np.linalg.norm(emb1)
                        norm2 = np.linalg.norm(emb2)
                        
                        if norm1 == 0:
                            logger.warning(f"⚠️  Query embedding has zero norm - skipping all articles")
                            break
                        
                        if norm2 == 0 or norm2 < 1e-6:  # Very small norm threshold
                            logger.debug(f"⚠️  Article {i+1} has zero/very small norm ({norm2:.6f}) - skipping")
                            continue
                        
                        # Normalize embeddings
                        emb1_normalized = emb1 / norm1
                        emb2_normalized = emb2 / norm2
                        
                        # Cosine similarity: dot product of normalized vectors (range: -1 to 1)
                        similarity = float(np.dot(emb1_normalized, emb2_normalized))
                        
                        # Check for NaN or invalid values
                        if np.isnan(similarity) or np.isinf(similarity):
                            logger.warning(f"⚠️  Article {i+1} has invalid similarity: {similarity} - skipping")
                            continue
                        
                        # Convert to 0-1 scale for easier interpretation (0 = orthogonal, 1 = identical)
                        # similarity_01 = (similarity + 1) / 2  # Optional: scale to 0-1
                        
                        similarity_scores.append(similarity)
                        logger.debug(f"📊 Article {i+1}: Similarity: {similarity:.4f} (raw cosine)")
                        
                        # Only include if similarity >= threshold
                        # Note: Cosine similarity ranges from -1 to 1, so threshold of 0.2 means "somewhat similar"
                        if similarity >= similarity_threshold:
                            logger.info(f"✅ Article {i+1}: '{article.title[:50]}...' - Similarity: {similarity:.4f} (>= {similarity_threshold})")
                            results.append({
                                "title": article.title,
                                "url": article.url,
                                "snippet": article.content[:200] + "..." if article.content else None,
                                "source": article.source or "Internal Database",
                                "published_at": article.published_at.isoformat() if article.published_at else None,
                                "topic": article.topic,
                                "sentiment": article.sentiment,
                                "sentiment_score": float(article.sentiment_score) if article.sentiment_score else None,
                                "relevance_score": round(similarity, 4),
                            })
                        else:
                            logger.info(f"⏭️  Article {i+1}: '{article.title[:50]}...' - Similarity: {similarity:.4f} (< {similarity_threshold}) - filtered out")
                    except Exception as e:
                        logger.error(f"❌ Error processing article {i+1}: {str(e)}", exc_info=True)
                        continue
            
            # Log statistics
            if similarity_scores:
                logger.info(f"📈 Similarity stats - Min: {min(similarity_scores):.4f}, Max: {max(similarity_scores):.4f}, Mean: {sum(similarity_scores)/len(similarity_scores):.4f}")
                logger.info(f"✅ Found {len(results)} articles above threshold ({similarity_threshold}) out of {len(articles)} total")
            else:
                logger.warning("⚠️  No similarity scores calculated")
            
            # Sort by similarity (descending) and limit to max_results
            results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
            final_results = results[:limit]
            
            logger.info(f"🎯 Returning {len(final_results)} top results (limit: {limit})")
            return final_results
            
    except Exception as e:
        logger.error(f"❌ Database search error: {str(e)}", exc_info=True)
        # Return empty list on error, don't fail the whole search
        return []


@news_agent.tool
async def search_news_database_text(
    ctx: RunContext[NewsAgentDependencies],
    query: str,
    topic: Optional[str] = None,
    sentiment: Optional[str] = None,
    max_results: Optional[int] = None
) -> List[dict]:
    """
    Search the internal news database using text-based filtering.
    
    Use this tool when semantic search is not needed or as a fallback.
    Searches by matching keywords in title or content.
    
    Args:
        query: Search keywords
        topic: Filter by topic
        sentiment: Filter by sentiment
        max_results: Maximum number of results
    
    Returns:
        List of matching news articles
    """
    limit = max_results or ctx.deps.max_results
    
    try:
        with get_db_session() as session:
            # Build query with text search and filters
            db_query = select(NewsArticle)
            
            # Text search in title or content
            search_filter = (
                NewsArticle.title.ilike(f"%{query}%") | 
                NewsArticle.content.ilike(f"%{query}%")
            )
            db_query = db_query.filter(search_filter)
            
            if topic:
                db_query = db_query.filter(NewsArticle.topic == topic)
            if sentiment:
                db_query = db_query.filter(NewsArticle.sentiment == sentiment)
            
            # Order by most recent
            db_query = db_query.order_by(NewsArticle.published_at.desc())
            db_query = db_query.limit(limit)
            
            articles = session.execute(db_query).scalars().all()
            
            results = []
            for article in articles:
                results.append({
                    "title": article.title,
                    "url": article.url,
                    "snippet": article.content[:200] + "..." if article.content else None,
                    "source": article.source,
                    "published_at": article.published_at.isoformat() if article.published_at else None,
                    "topic": article.topic,
                    "sentiment": article.sentiment,
                    "sentiment_score": float(article.sentiment_score) if article.sentiment_score else None,
                })
            
            return results if results else [{"error": "No articles found matching query"}]
            
    except Exception as e:
        return [{"error": str(e), "query": query}]


@news_agent.tool
async def get_database_stats(ctx: RunContext[NewsAgentDependencies]) -> dict:
    """
    Get statistics about the news database.
    
    Use this tool to understand what's available in the database:
    - Total articles count
    - Available topics
    - Sentiment distribution
    - Date range of articles
    
    Returns:
        Database statistics
    """
    try:
        with get_db_session() as session:
            total = session.query(func.count(NewsArticle.id)).scalar()
            
            # Get topic distribution
            topics = session.query(
                NewsArticle.topic,
                func.count(NewsArticle.id)
            ).filter(
                NewsArticle.topic.isnot(None)
            ).group_by(NewsArticle.topic).all()
            
            # Get sentiment distribution
            sentiments = session.query(
                NewsArticle.sentiment,
                func.count(NewsArticle.id)
            ).filter(
                NewsArticle.sentiment.isnot(None)
            ).group_by(NewsArticle.sentiment).all()
            
            # Get date range
            date_range = session.query(
                func.min(NewsArticle.published_at),
                func.max(NewsArticle.published_at)
            ).filter(
                NewsArticle.published_at.isnot(None)
            ).first()
            
            return {
                "total_articles": total,
                "topics": {topic: count for topic, count in topics},
                "sentiments": {sentiment: count for sentiment, count in sentiments},
                "date_range": {
                    "earliest": date_range[0].isoformat() if date_range[0] else None,
                    "latest": date_range[1].isoformat() if date_range[1] else None,
                }
            }
    except Exception as e:
        return {"error": str(e)}


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
        Structured news search results
    """
    deps = NewsAgentDependencies(
        user_query=query,
        max_results=max_results,
        search_provider=search_provider
    )
    
    result = await news_agent.run(query, deps=deps)
    return result.output


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
        for i, article in enumerate(result.articles, 1):
            print(f"\n{i}. {article.title}")
            print(f"   Source: {article.source}")
            print(f"   URL: {article.url}")
            if article.relevance_score:
                print(f"   Relevance: {article.relevance_score:.2%}")
        
        # Example 2: Search database for technology news
        print("\n" + "=" * 70)
        print("Example 2: Searching database for positive technology news")
        print("=" * 70)
        result = await search_news(
            "machine learning innovations",
            max_results=3,
            search_provider="database"
        )
        print(f"\nSummary: {result.summary}")
        print(f"Found {result.total_results} articles")
    
    asyncio.run(main())

