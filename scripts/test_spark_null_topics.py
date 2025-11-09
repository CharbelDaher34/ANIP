"""
Test script to nullify ML fields for selected articles.
Used for testing the Spark ML processing pipeline.
"""
import os
import sys
from datetime import datetime
from typing import List

# Add project root to path
sys.path.insert(0, '/opt/anip')

from shared.database import get_db_session, init_database
from shared.models.news import NewsArticle
from sqlalchemy import func, select

def create_tables_if_not_exist():
    """Create database tables if they don't exist using SQLAlchemy."""
    return init_database()

def get_article_stats():
    """Get total, with_topic, and null_topic counts."""
    with get_db_session() as session:
        total_count = session.query(func.count(NewsArticle.id)).scalar()
        with_topic_count = session.query(func.count(NewsArticle.id)).filter(NewsArticle.topic.isnot(None)).scalar()
        null_topic_count = session.query(func.count(NewsArticle.id)).filter(NewsArticle.topic.is_(None)).scalar()
        return total_count, with_topic_count, null_topic_count

def nullify_ml_fields_for_articles(article_ids: List[int]):
    """Set topic, sentiment, sentiment_score, and embedding to NULL for specified article IDs."""
    print(f"\n🔧 Nullifying ML fields for {len(article_ids)} articles...")
    with get_db_session() as session:
        for article_id in article_ids:
            article = session.query(NewsArticle).filter(NewsArticle.id == article_id).first()
            if article:
                print(f"   - ID {article.id}: {article.title[:50]}...")
                print(f"     Current topic: {article.topic}, sentiment: {article.sentiment}")
                article.topic = None
                article.sentiment = None
                article.sentiment_score = None
                article.embedding = None
                article.updated_at = datetime.utcnow()
                session.add(article)
        session.commit()
    print(f"\n✅ Successfully nullified {len(article_ids)} articles")

def get_null_count():
    """Get count of articles with NULL topic, sentiment, or embedding."""
    with get_db_session() as session:
        count = session.query(func.count(NewsArticle.id)).filter(
            (NewsArticle.topic.is_(None)) |
            (NewsArticle.sentiment.is_(None)) |
            (NewsArticle.embedding.is_(None))
        ).scalar()
        return count if count else 0

def main():
    print("============================================================")
    print("🧪 Testing Spark ML Processing with NULL Topics")
    print("============================================================")
    
    print("\n1️⃣  Initializing database...")
    create_tables_if_not_exist()
    
    total, with_topic, null_topic = get_article_stats()
    print(f"\n📊 Initial stats:")
    print(f"   Total articles: {total}")
    print(f"   With topics: {with_topic}")
    print(f"   NULL topics: {null_topic}")
    
    # Select some articles to nullify
    with get_db_session() as session:
        articles_to_nullify = session.query(NewsArticle.id).limit(5).all()
        article_ids = [a.id for a in articles_to_nullify]
    
    if not article_ids:
        print("⚠️  No articles found to nullify. Please ingest some data first.")
        return
    
    nullify_ml_fields_for_articles(article_ids)
    
    current_null_count = get_null_count()
    print(f"\n📊 Articles with NULL topics now: {current_null_count}")
    
    print("\n✅ Nullification complete!")
    print(f"   Article IDs: {article_ids}")
    
    print("\n🚀 Ready to run Spark job!")

if __name__ == "__main__":
    main()

