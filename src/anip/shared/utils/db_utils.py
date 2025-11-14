"""
Database utility functions for saving articles.
"""
import logging
from typing import List, Dict, Any
from anip.shared.database import get_db_session
from anip.shared.models.news import NewsArticle

logger = logging.getLogger(__name__)

def save_articles_batch(articles: List[Dict[str, Any]]) -> int:
    """
    Save a batch of articles to the database using SQLAlchemy.
    Adds all articles without checking for duplicates.
    
    Args:
        articles: List of article dictionaries from ingestors
                 Expected fields: title, content, source, author, url, 
                                 published_at, language, region
                 Optional ML fields: topic, sentiment, sentiment_score, 
                                   embedding, summary, keywords
        
    Returns:
        Number of articles successfully saved
    """
    if not articles:
        return 0
    
    saved_count = 0
    skipped_count = 0
    
    with get_db_session() as session:
        for article_data in articles:
            # Create a savepoint for this article
            savepoint = session.begin_nested()
            
            try:
                # Create new article (no duplicate checking)
                # Note: created_at and updated_at are handled by database server_default
                article = NewsArticle(
                    title=article_data.get('title'),
                    content=article_data.get('content'),
                    source=article_data.get('source'),
                    author=article_data.get('author'),
                    url=article_data.get('url'),
                    published_at=article_data.get('published_at'),
                    language=article_data.get('language', 'en'),
                    region=article_data.get('region'),
                    api_source=article_data.get('api_source'),
                    topic=article_data.get('topic'),
                    sentiment=article_data.get('sentiment'),
                    sentiment_score=article_data.get('sentiment_score'),
                    embedding=article_data.get('embedding'),
                    summary=article_data.get('summary'),
                    keywords=article_data.get('keywords')
                )
                session.add(article)
                savepoint.commit()  # Commit this savepoint
                print(f"✅ Created article: {article_data.get('title', 'Unknown')[:50]}")
                saved_count += 1
                
            except Exception as e:
                savepoint.rollback()  # Rollback only this article, not the entire batch
                skipped_count += 1
                logger.warning(f"Skipped article due to error: {article_data.get('title', 'Unknown')[:50]} - {str(e)}")
                print(f"⚠️  Skipped due to error: {article_data.get('title', 'Unknown')[:50]}")
                continue
    
    if skipped_count > 0:
        print(f"📊 Batch summary: {saved_count} new, {skipped_count} skipped, {saved_count} total processed")
    else:
        print(f"📊 Batch summary: {saved_count} new articles saved")
    return saved_count


def update_articles_ml_predictions(articles: List[Dict[str, Any]]) -> int:
    """
    Update existing articles with ML predictions (topic, sentiment, embedding).
    
    Args:
        articles: List of article dictionaries with 'id' and ML predictions
        
    Returns:
        Number of articles successfully updated
    """
    if not articles:
        return 0
    
    updated_count = 0
    skipped_count = 0
    
    with get_db_session() as session:
        for article_data in articles:
            article_id = article_data.get('id')
            
            if not article_id:
                skipped_count += 1
                logger.warning(f"Skipped article without ID: {article_data.get('title', 'Unknown')[:50]}")
                continue
            
            savepoint = session.begin_nested()
            
            try:
                article = session.query(NewsArticle).filter(NewsArticle.id == article_id).first()
                
                if not article:
                    skipped_count += 1
                    logger.warning(f"Article ID {article_id} not found in database")
                    savepoint.rollback()
                    continue
                
                # Only update fields that have non-null values
                updated_fields = []
                
                if article_data.get('topic') is not None:
                    article.topic = article_data.get('topic')
                    updated_fields.append('topic')
                
                if article_data.get('sentiment') is not None:
                    article.sentiment = article_data.get('sentiment')
                    updated_fields.append('sentiment')
                
                if article_data.get('sentiment_score') is not None:
                    article.sentiment_score = article_data.get('sentiment_score')
                    updated_fields.append('sentiment_score')
                
                embedding = article_data.get('embedding')
                if embedding is not None:
                    # Validate embedding before saving - don't store zero vectors
                    if isinstance(embedding, list) and len(embedding) > 0:
                        # Check if it's not all zeros
                        if sum(abs(x) for x in embedding) > 0.001:
                            article.embedding = embedding
                            updated_fields.append('embedding')
                        else:
                            logger.warning(f"Skipping zero-norm embedding for article ID {article_id}")
                
                # Only update if at least one field was updated
                if updated_fields:
                    # Update timestamp to trigger updated_at automatic update
                    session.flush()  # Let database handle updated_at via onupdate
                    savepoint.commit()
                    print(f"✅ Updated article: {article.title[:50]} (fields: {', '.join(updated_fields)})")
                    updated_count += 1
                else:
                    savepoint.rollback()
                    skipped_count += 1
                    print(f"⚠️  No ML predictions to update for: {article.title[:50]}")
                
            except Exception as e:
                savepoint.rollback()
                skipped_count += 1
                logger.warning(f"Failed to update article ID {article_id}: {str(e)}")
                print(f"⚠️  Failed to update article ID {article_id}: {str(e)}")
                continue
    
    if skipped_count > 0:
        print(f"📊 Update summary: {updated_count} updated, {skipped_count} skipped")
    else:
        print(f"📊 Update summary: {updated_count} articles updated with ML predictions")
    
    return updated_count

