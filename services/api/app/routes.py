"""
API routes for ANIP.
"""
import sys
sys.path.insert(0, '/workspace')

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime

# Import shared modules
sys.path.insert(0, '/workspace/../..')
from shared.database import get_db_session
from shared.models.news import NewsArticle

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
    topic: Optional[str]
    sentiment: Optional[str]
    sentiment_score: Optional[float]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.get("/articles", response_model=List[ArticleResponse])
async def get_articles(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    topic: Optional[str] = None,
    sentiment: Optional[str] = None,
    source: Optional[str] = None
):
    """
    Get articles with optional filtering.
    
    Args:
        limit: Number of articles to return (1-100)
        offset: Number of articles to skip
        topic: Filter by topic
        sentiment: Filter by sentiment (positive, negative, neutral)
        source: Filter by source
    
    Returns:
        List of articles
    """
    with get_db_session() as session:
        query = session.query(NewsArticle)
        
        # Apply filters
        if topic:
            query = query.filter(NewsArticle.topic == topic)
        if sentiment:
            query = query.filter(NewsArticle.sentiment == sentiment)
        if source:
            query = query.filter(NewsArticle.source == source)
        
        # Order by most recent first
        query = query.order_by(NewsArticle.published_at.desc())
        
        # Apply pagination
        articles = query.offset(offset).limit(limit).all()
        
        return articles


@router.get("/articles/{article_id}", response_model=ArticleResponse)
async def get_article(article_id: int):
    """
    Get a single article by ID.
    
    Args:
        article_id: Article ID
    
    Returns:
        Article details
    """
    with get_db_session() as session:
        article = session.query(NewsArticle).filter(NewsArticle.id == article_id).first()
        
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        return article


@router.get("/stats/topics")
async def get_topic_stats():
    """
    Get statistics by topic.
    
    Returns:
        Topic distribution
    """
    from sqlalchemy import func
    
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


@router.get("/stats/sentiments")
async def get_sentiment_stats():
    """
    Get statistics by sentiment.
    
    Returns:
        Sentiment distribution
    """
    from sqlalchemy import func
    
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

