#!/usr/bin/env python3
"""
Remove duplicate articles from the database.

Identifies duplicates by URL and keeps only the article with the smallest ID.
"""
import logging
from contextlib import contextmanager
import sys
import os
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session, sessionmaker
# Get the absolute path of the current file
current_file = os.path.abspath(__file__)

# Go back to the project root (2 levels up for example)
project_root = os.path.dirname(os.path.dirname(current_file))

# Enter the "src" folder inside the root
src_path = os.path.join(project_root, "src")

# Add to sys.path if not already present
if src_path not in sys.path:
    sys.path.append(src_path)

print("Root:", project_root)
print("Src:", src_path)

# load dotenv from root
from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, ".env"))

from anip.shared.models.news import NewsArticle
from anip.shared.models.news import NewsArticle

# ============================================================================
# CONFIGURATION - Edit this variable to change the database URL
# ============================================================================
DATABASE_URL = "postgresql+psycopg2://anip:anip_pw@localhost:5436/anip"
# ============================================================================



logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@contextmanager
def get_db_session():
    """Create a database session."""
    engine = create_engine(DATABASE_URL, echo=False)
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        expire_on_commit=False
    )
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def find_and_remove_duplicates(dry_run: bool = False) -> dict:
    """
    Find and remove duplicate articles based on URL.
    
    For each URL, keeps the article with the smallest ID and removes the rest.
    
    Args:
        dry_run: If True, only report what would be removed
    
    Returns:
        Dictionary with statistics
    """
    stats = {
        'total_articles': 0,
        'duplicate_groups': 0,
        'duplicates_removed': 0,
        'articles_remaining': 0
    }
    
    with get_db_session() as session:
        # Get total count
        stats['total_articles'] = session.query(NewsArticle).count()
        logger.info(f"Total articles in database: {stats['total_articles']}")
        
        # Find URLs with multiple articles
        duplicate_urls = session.query(
            NewsArticle.url,
            func.count(NewsArticle.id).label('count'),
            func.min(NewsArticle.id).label('min_id')
        ).group_by(
            NewsArticle.url
        ).having(
            func.count(NewsArticle.id) > 1
        ).all()
        
        if not duplicate_urls:
            logger.info("✅ No duplicate articles found!")
            return stats
        
        stats['duplicate_groups'] = len(duplicate_urls)
        logger.info(f"Found {len(duplicate_urls)} URLs with duplicate articles")
        
        # Process each duplicate group
        for url, count, min_id in duplicate_urls:
            # Find all articles with this URL except the one with min_id
            duplicates = session.query(NewsArticle).filter(
                NewsArticle.url == url,
                NewsArticle.id != min_id
            ).all()
            
            logger.info(f"\n📋 URL: {url[:80]}...")
            logger.info(f"   Found {count} articles, keeping ID {min_id}")
            
            for article in duplicates:
                logger.info(f"   {'Would remove' if dry_run else 'Removing'} ID {article.id}: {article.title[:50]}...")
                stats['duplicates_removed'] += 1
                
                if not dry_run:
                    session.delete(article)
        
        # Commit if not dry run
        if not dry_run:
            session.commit()
            logger.info("\n✅ Duplicates removed!")
        
        # Get final count
        if dry_run:
            stats['articles_remaining'] = stats['total_articles'] - stats['duplicates_removed']
        else:
            stats['articles_remaining'] = session.query(NewsArticle).count()
    
    return stats


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Remove duplicate articles from the database'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be removed without actually deleting'
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 70)
    logger.info("ANIP Duplicate Removal Script")
    logger.info("=" * 70)
    
    if args.dry_run:
        logger.info("🔍 DRY RUN MODE - No changes will be made\n")
    
    # Run duplicate removal
    stats = find_and_remove_duplicates(dry_run=args.dry_run)
    
    # Print summary
    logger.info("\n" + "=" * 70)
    logger.info("Summary")
    logger.info("=" * 70)
    logger.info(f"Total articles before: {stats['total_articles']}")
    logger.info(f"Duplicate URL groups: {stats['duplicate_groups']}")
    logger.info(f"Duplicate articles {'to remove' if args.dry_run else 'removed'}: {stats['duplicates_removed']}")
    logger.info(f"Articles remaining: {stats['articles_remaining']}")
    
    if args.dry_run and stats['duplicates_removed'] > 0:
        logger.info("\n💡 Run without --dry-run to actually remove duplicates")
    elif stats['duplicates_removed'] > 0:
        logger.info("\n✅ Cleanup completed successfully!")
    
    logger.info("=" * 70)


if __name__ == '__main__':
    main()

