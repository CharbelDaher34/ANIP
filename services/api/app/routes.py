"""
API routes for ANIP.
"""
import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

from anip.shared.database import get_db_session
from anip.shared.models.news import NewsArticle
from anip.ml.embedding import generate_embedding

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["news"])


class ArticleResponse(BaseModel):
    """Article response model."""
    id: int
    title: str
    content: Optional[str]
    source: Optional[str]
    author: Optional[str]
    url: str
    published_at: Optional[datetime]
    language: Optional[str]
    region: Optional[str]
    api_source: Optional[str]
    topic: Optional[str]
    sentiment: Optional[str]
    sentiment_score: Optional[float]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SimilarArticleResponse(BaseModel):
    """Similar article response with similarity score."""
    id: int
    title: str
    content: Optional[str]
    source: Optional[str]
    url: str
    published_at: Optional[datetime]
    topic: Optional[str]
    sentiment: Optional[str]
    similarity_score: float

    class Config:
        from_attributes = True


@router.get("/articles", response_model=List[ArticleResponse])
async def get_articles(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    topic: Optional[str] = Query(default=None, max_length=100),
    sentiment: Optional[str] = Query(default=None, max_length=50),
    source: Optional[str] = Query(default=None, max_length=200),
    api_source: Optional[str] = Query(default=None, max_length=50)
):
    """
    Get articles with optional filtering.
    
    Args:
        limit: Number of articles to return (1-100)
        offset: Number of articles to skip
        topic: Filter by topic
        sentiment: Filter by sentiment (positive, negative, neutral)
        source: Filter by source
        api_source: Filter by API source (newsapi, newsdata, gdelt, mediastack, thenewsapi, worldnewsapi)
    
    Returns:
        List of articles
    """
    # Validate sentiment value if provided
    valid_sentiments = {"positive", "negative", "neutral"}
    if sentiment and sentiment.lower() not in valid_sentiments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid sentiment. Must be one of: {', '.join(valid_sentiments)}"
        )
    
    try:
        with get_db_session() as session:
            query = session.query(NewsArticle)
            
            # Apply filters (SQLAlchemy handles parameterization automatically)
            if topic:
                # Sanitize: strip whitespace and limit length
                topic = topic.strip()[:100]
                query = query.filter(NewsArticle.topic == topic)
            if sentiment:
                sentiment = sentiment.lower().strip()
                query = query.filter(NewsArticle.sentiment == sentiment)
            if source:
                # Sanitize: strip whitespace and limit length
                source = source.strip()[:200]
                query = query.filter(NewsArticle.source == source)
            if api_source:
                # Sanitize: strip whitespace and limit length
                api_source = api_source.lower().strip()[:50]
                query = query.filter(NewsArticle.api_source == api_source)
            
            # Order by most recent first (handle NULL published_at)
            from sqlalchemy import nullslast
            query = query.order_by(nullslast(NewsArticle.published_at.desc()))
            
            # Apply pagination
            articles = query.offset(offset).limit(limit).all()
            
            return articles
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_articles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred"
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_articles: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/articles/{article_id}", response_model=ArticleResponse)
async def get_article(article_id: int):
    """
    Get a single article by ID.
    
    Args:
        article_id: Article ID
    
    Returns:
        Article details
    """
    try:
        with get_db_session() as session:
            article = session.query(NewsArticle).filter(NewsArticle.id == article_id).first()
            
            if not article:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Article with ID {article_id} not found"
                )
            
            return article
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_article: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred"
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_article: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/stats/topics")
async def get_topic_stats():
    """
    Get statistics by topic.
    
    Returns:
        Topic distribution
    """
    from sqlalchemy import func
    
    try:
        with get_db_session() as session:
            stats = session.query(
                NewsArticle.topic,
                func.count(NewsArticle.id).label('count')
            ).filter(
                NewsArticle.topic.isnot(None)
            ).group_by(
                NewsArticle.topic
            ).order_by(
                func.count(NewsArticle.id).desc()
            ).all()
            
            return {
                "topics": [
                    {"topic": topic, "count": count}
                    for topic, count in stats
                ]
            }
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_topic_stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred"
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_topic_stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/stats/sentiments")
async def get_sentiment_stats():
    """
    Get statistics by sentiment.
    
    Returns:
        Sentiment distribution
    """
    from sqlalchemy import func
    
    try:
        with get_db_session() as session:
            stats = session.query(
                NewsArticle.sentiment,
                func.count(NewsArticle.id).label('count')
            ).filter(
                NewsArticle.sentiment.isnot(None)
            ).group_by(
                NewsArticle.sentiment
            ).order_by(
                func.count(NewsArticle.id).desc()
            ).all()
            
            return {
                "sentiments": [
                    {"sentiment": sentiment, "count": count}
                    for sentiment, count in stats
                ]
            }
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_sentiment_stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred"
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_sentiment_stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/stats/sources")
async def get_source_stats(limit: int = Query(default=10, ge=1, le=50)):
    """
    Get statistics by source.
    
    Args:
        limit: Number of top sources to return
    
    Returns:
        Source distribution
    """
    from sqlalchemy import func
    
    try:
        with get_db_session() as session:
            stats = session.query(
                NewsArticle.source,
                func.count(NewsArticle.id).label('count')
            ).filter(
                NewsArticle.source.isnot(None)
            ).group_by(
                NewsArticle.source
            ).order_by(
                func.count(NewsArticle.id).desc()
            ).limit(limit).all()
            
            return {
                "sources": [
                    {"source": source, "count": count}
                    for source, count in stats
                ]
            }
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_source_stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred"
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_source_stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/stats/api-sources")
async def get_api_source_stats():
    """
    Get statistics by API source.
    
    Returns:
        API source distribution
    """
    from sqlalchemy import func
    
    try:
        with get_db_session() as session:
            stats = session.query(
                NewsArticle.api_source,
                func.count(NewsArticle.id).label('count')
            ).filter(
                NewsArticle.api_source.isnot(None)
            ).group_by(
                NewsArticle.api_source
            ).order_by(
                func.count(NewsArticle.id).desc()
            ).all()
            
            return {
                "api_sources": [
                    {"api_source": api_source, "count": count}
                    for api_source, count in stats
                ]
            }
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_api_source_stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred"
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_api_source_stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/search/similar", response_model=List[SimilarArticleResponse])
async def search_similar_articles(
    question: str = Query(..., min_length=1, max_length=500, description="Question or text to find similar articles for"),
    limit: int = Query(default=2, ge=1, le=10, description="Number of similar articles to return")
):
    """
    Find similar articles using vector similarity search.
    
    This endpoint uses cosine similarity on article embeddings to find
    the most relevant articles to a given question or text query.
    
    Args:
        question: Question or text to search for similar articles
        limit: Number of similar articles to return (1-10, default: 2)
    
    Returns:
        List of similar articles with similarity scores
    """
    try:
        # Generate embedding for the question
        logger.info(f"Generating embedding for question: {question[:100]}...")
        question_embedding = generate_embedding(question)
        
        with get_db_session() as session:
            # pgvector supports passing Python lists directly to distance operators
            # Calculate cosine distance using the <=> operator
            distance = NewsArticle.embedding.cosine_distance(question_embedding)
            
            # Query articles using SQLAlchemy ORM
            # Order by distance (smallest distance = most similar)
            results = session.query(
                NewsArticle,
                distance.label('distance')
            ).filter(
                NewsArticle.embedding.isnot(None)
            ).order_by(
                distance
            ).limit(limit).all()
            
            if not results:
                logger.warning("No articles with embeddings found in database")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No articles with embeddings found. Please wait for ML processing to complete."
                )
            
            # Convert to response with similarity scores
            # Cosine distance range is [0, 2], so similarity is [0, 1]
            similar_articles = []
            for article, dist in results:
                # Ensure distance is in valid range [0, 2]
                dist = float(dist) if dist is not None else 1.0
                dist = max(0.0, min(2.0, dist))
                similarity = 1.0 - (dist / 2.0)
                
                similar_articles.append({
                    "id": article.id,
                    "title": article.title,
                    "content": article.content,
                    "source": article.source,
                    "url": article.url,
                    "published_at": article.published_at,
                    "topic": article.topic,
                    "sentiment": article.sentiment,
                    "similarity_score": round(similarity, 4)
                })
            
            logger.info(f"Found {len(similar_articles)} similar articles")
            return similar_articles
            
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error in search_similar_articles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred"
        )
    except Exception as e:
        logger.error(f"Unexpected error in search_similar_articles: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/stats/missing-ml")
async def get_missing_ml_stats():
    """
    Get statistics about articles missing ML predictions.
    
    Returns:
        Counts of articles missing topic, sentiment, or embedding predictions.
        Also includes total articles and articles missing any ML field.
    """
    from sqlalchemy import func, or_
    
    try:
        with get_db_session() as session:
            # Total articles
            total_count = session.query(func.count(NewsArticle.id)).scalar()
            
            # Articles missing topic
            missing_topic_count = session.query(func.count(NewsArticle.id)).filter(
                NewsArticle.topic.is_(None)
            ).scalar()
            
            # Articles missing sentiment
            missing_sentiment_count = session.query(func.count(NewsArticle.id)).filter(
                NewsArticle.sentiment.is_(None)
            ).scalar()
            
            # Articles missing embedding
            missing_embedding_count = session.query(func.count(NewsArticle.id)).filter(
                NewsArticle.embedding.is_(None)
            ).scalar()
            
            # Articles missing any ML field (topic OR sentiment OR embedding)
            missing_any_count = session.query(func.count(NewsArticle.id)).filter(
                or_(
                    NewsArticle.topic.is_(None),
                    NewsArticle.sentiment.is_(None),
                    NewsArticle.embedding.is_(None)
                )
            ).scalar()
            
            return {
                "total_articles": total_count,
                "missing_topic": missing_topic_count,
                "missing_sentiment": missing_sentiment_count,
                "missing_embedding": missing_embedding_count,
                "missing_any_ml_field": missing_any_count,
                "complete_ml_predictions": total_count - missing_any_count if total_count else 0
            }
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_missing_ml_stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred"
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_missing_ml_stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

