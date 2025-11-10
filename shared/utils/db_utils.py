"""
Database utility functions for saving articles.
"""
import logging
from typing import List, Dict, Any
from datetime import datetime, timezone
from shared.database import get_db_session
from shared.models.news import NewsArticle

logger = logging.getLogger(__name__)

def save_articles_batch(articles: List[Dict[str, Any]]) -> int:
    """
    Save a batch of articles to the database using SQLAlchemy.
    Returns the number of articles saved (excluding duplicates).
    
    Args:
        articles: List of article dictionaries with ML predictions
        
    Returns:
        Number of articles successfully saved
    """
    if not articles:
        return 0
    
    # Deduplicate within the batch by URL (keep last occurrence)
    seen_urls = {}
    for article in articles:
        url = article.get('url')
        if url:
            seen_urls[url] = article
    
    deduplicated = list(seen_urls.values())
    
    if len(deduplicated) < len(articles):
        print(f"ℹ️  Deduplicated batch: {len(articles)} → {len(deduplicated)} articles")
    
    saved_count = 0
    updated_count = 0
    skipped_count = 0
    
    with get_db_session() as session:
        for article_data in deduplicated:
            # Create a savepoint for this article
            savepoint = session.begin_nested()
            
            try:
                # Check if article exists by URL
                existing = session.query(NewsArticle).filter(
                    NewsArticle.url == article_data.get('url')
                ).first()
                
                if existing:
                    # Update existing article with ML predictions
                    if 'topic' in article_data:
                        existing.topic = article_data.get('topic', existing.topic)
                    if 'sentiment' in article_data:
                        existing.sentiment = article_data.get('sentiment', existing.sentiment)
                    if 'sentiment_score' in article_data:
                        existing.sentiment_score = article_data.get('sentiment_score', existing.sentiment_score)
                    if 'embedding' in article_data:
                        existing.embedding = article_data.get('embedding', existing.embedding)
                    if 'summary' in article_data:
                        existing.summary = article_data.get('summary', existing.summary)
                    if 'keywords' in article_data:
                        existing.keywords = article_data.get('keywords', existing.keywords)
                    existing.updated_at = datetime.now(timezone.utc)
                    savepoint.commit()  # Commit this savepoint
                    print(f"✅ Updated article: {article_data.get('title', 'Unknown')[:50]}")
                    updated_count += 1
                else:
                    # Create new article
                    article = NewsArticle(
                        title=article_data.get('title'),
                        content=article_data.get('content'),
                        source=article_data.get('source'),
                        author=article_data.get('author'),
                        url=article_data.get('url'),
                        published_at=article_data.get('published_at'),
                        language=article_data.get('language', 'en'),
                        region=article_data.get('region'),
                        topic=article_data.get('topic'),
                        sentiment=article_data.get('sentiment'),
                        sentiment_score=article_data.get('sentiment_score'),
                        embedding=article_data.get('embedding'),
                        summary=article_data.get('summary'),
                        keywords=article_data.get('keywords'),
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc)
                    )
                    session.add(article)
                    savepoint.commit()  # Commit this savepoint
                    print(f"✅ Created article: {article_data.get('title', 'Unknown')[:50]}")
                    saved_count += 1
                
            except Exception as e:
                savepoint.rollback()  # Rollback only this article, not the entire batch
                skipped_count += 1
                logger.warning(f"Skipped article due to error: {article_data.get('title', 'Unknown')[:50]} - {str(e)}")
                print(f"⚠️  Skipped duplicate/error: {article_data.get('title', 'Unknown')[:50]}")
                continue
    
    total = saved_count + updated_count
    if skipped_count > 0:
        print(f"📊 Batch summary: {saved_count} new, {updated_count} updated, {skipped_count} skipped, {total} total processed")
    else:
        print(f"📊 Batch summary: {saved_count} new, {updated_count} updated, {total} total processed")
    return total

