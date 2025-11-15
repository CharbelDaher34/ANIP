"""
Shared similarity search utilities using pgvector.

This module provides a unified similarity search function that both the API
and agent tools use to ensure consistent results and performance.
"""
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from anip.shared.models.news import NewsArticle
from anip.ml.embedding import generate_embedding

logger = logging.getLogger(__name__)


def search_similar_articles(
    query: str,
    session: Session,
    limit: int = 5,
    similarity_threshold: float = 0.4,
    topic: Optional[str] = None,
    sentiment: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Search for similar articles using pgvector cosine similarity.
    
    This function uses the database's built-in vector operations for efficient
    similarity search with indexing support.
    
    Args:
        query: Search query text (natural language question or keywords)
        session: SQLAlchemy database session
        limit: Maximum number of results to return
        similarity_threshold: Minimum similarity score (0.0-1.0), default 0.0 returns all
        topic: Optional topic filter (Technology, Politics, Business, etc.)
        sentiment: Optional sentiment filter (positive, negative, neutral)
    
    Returns:
        List of article dictionaries with similarity scores, sorted by relevance
        Each dict contains: id, title, content, source, url, published_at, 
                           topic, sentiment, sentiment_score, similarity_score
    
    Example:
        >>> from anip.shared.database import get_db_session
        >>> with get_db_session() as session:
        >>>     results = search_similar_articles(
        >>>         query="artificial intelligence",
        >>>         session=session,
        >>>         limit=5,
        >>>         similarity_threshold=0.3
        >>>     )
        >>> print(f"Found {len(results)} similar articles")
    """
    logger.info(f"Searching similar articles - Query: '{query[:50]}...', Limit: {limit}, Threshold: {similarity_threshold}")
    
    # Generate embedding for the query
    try:
        query_embedding = generate_embedding(query)
    except Exception as e:
        logger.error(f"Failed to generate query embedding: {e}")
        raise
    
    if not query_embedding:
        logger.warning("Query embedding is empty or None")
        return []
    
    logger.debug(f"Generated query embedding with {len(query_embedding)} dimensions")
    
    # Build base query - pgvector's cosine_distance returns distance in range [0, 2]
    # where 0 = identical, 2 = opposite
    distance = NewsArticle.embedding.cosine_distance(query_embedding)
    
    # Start building the query
    db_query = session.query(
        NewsArticle,
        distance.label('distance')
    ).filter(
        NewsArticle.embedding.isnot(None)
    )
    
    # Apply optional filters
    if topic:
        logger.debug(f"Filtering by topic: {topic}")
        db_query = db_query.filter(NewsArticle.topic == topic)
    
    if sentiment:
        logger.debug(f"Filtering by sentiment: {sentiment}")
        db_query = db_query.filter(NewsArticle.sentiment == sentiment)
    
    # Order by distance (smallest = most similar), then by ID for deterministic results
    # Secondary sort by ID ensures consistent ordering when similarity scores are equal
    db_query = db_query.order_by(distance, NewsArticle.id).limit(limit)
    
    # Execute query
    results = db_query.all()
    
    if not results:
        logger.info("No articles with embeddings found matching filters")
        return []
    
    logger.info(f"Found {len(results)} articles from database")
    
    # Convert to response format with similarity scores
    # Cosine distance [0, 2] -> Similarity [0, 1] where 1 = identical
    similar_articles = []
    
    for article, dist in results:
        # Ensure distance is in valid range [0, 2]
        dist = float(dist) if dist is not None else 1.0
        dist = max(0.0, min(2.0, dist))
        
        # Convert distance to similarity: similarity = 1 - (distance / 2)
        # This gives us a score between 0 (opposite) and 1 (identical)
        similarity = 1.0 - (dist / 2.0)
        
        # Apply similarity threshold filter
        if similarity < similarity_threshold:
            logger.debug(f"Filtered out article '{article.title[:30]}...' - Similarity {similarity:.4f} < {similarity_threshold}")
            continue
        
        similar_articles.append({
            "id": article.id,
            "title": article.title,
            "content": article.content,
            "source": article.source,
            "url": article.url,
            "published_at": article.published_at,
            "topic": article.topic,
            "sentiment": article.sentiment,
            "sentiment_score": float(article.sentiment_score) if article.sentiment_score else None,
            "similarity_score": round(similarity, 4),
            "relevance_score": round(similarity, 4),  # Alias for agent compatibility
        })
        
        logger.debug(f"Article: '{article.title[:50]}...' - Similarity: {similarity:.4f}")
    
    logger.info(f"Returning {len(similar_articles)} articles after threshold filter")
    return similar_articles

