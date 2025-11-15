#!/usr/bin/env python3
"""
Database cleanup script for ANIP.

Removes low-quality articles:
- Empty or null content
- Paid plan placeholder messages

Usage:
    python scripts/cleanup_database.py [--dry-run]
"""
import argparse
import logging
from typing import List
from contextlib import contextmanager
from sqlalchemy import func, or_, create_engine
from sqlalchemy.orm import Session, sessionmaker
import os
import sys

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

# ============================================================================
# CONFIGURATION - Edit this variable to change the database URL
# ============================================================================
DATABASE_URL = "postgresql+psycopg2://anip:anip_pw@localhost:5436/anip"
# Example formats:
# DATABASE_URL = "postgresql+psycopg2://user:password@localhost:5432/dbname"
# DATABASE_URL = "postgresql+psycopg2://user:password@host:5432/dbname"
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@contextmanager
def get_db_session():
    """
    Create a database session using the configured DATABASE_URL.
    
    Yields:
        Database session
    """
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


def find_empty_content_articles(session: Session) -> List[NewsArticle]:
    """Find articles with empty or null content."""
    return session.query(NewsArticle).filter(
        or_(
            NewsArticle.content.is_(None),
            NewsArticle.content == '',
            func.trim(NewsArticle.content) == ''
        )
    ).all()


def find_paid_plan_articles(session: Session) -> List[NewsArticle]:
    """Find articles containing paid plan placeholder messages."""
    return session.query(NewsArticle).filter(
        func.upper(NewsArticle.content).contains('ONLY AVAILABLE IN PAID PLANS')
    ).all()


def cleanup_database(dry_run: bool = False) -> dict:
    """
    Clean up the database by removing low-quality articles.
    
    Removes:
    - Articles with empty or null content
    - Articles containing "ONLY AVAILABLE IN PAID PLANS" messages
    
    Args:
        dry_run: If True, only report what would be removed without actually deleting
    
    Returns:
        Dictionary with cleanup statistics
    """
    stats = {
        'empty_content': 0,
        'paid_plan': 0,
        'total_removed': 0,
        'total_articles_before': 0,
        'total_articles_after': 0
    }
    
    with get_db_session() as session:
        # Get total count before cleanup
        stats['total_articles_before'] = session.query(NewsArticle).count()
        
        # Find empty content articles
        empty_articles = find_empty_content_articles(session)
        stats['empty_content'] = len(empty_articles)
        
        if empty_articles:
            logger.info(f"Found {len(empty_articles)} articles with empty content")
            if not dry_run:
                for article in empty_articles:
                    logger.debug(f"Removing empty content: {article.title[:50]} (ID: {article.id})")
                    session.delete(article)
            else:
                for article in empty_articles[:5]:  # Show first 5 examples
                    logger.info(f"  Would remove: {article.title[:50]} (ID: {article.id})")
                if len(empty_articles) > 5:
                    logger.info(f"  ... and {len(empty_articles) - 5} more")
        
        # Find paid plan articles
        paid_plan_articles = find_paid_plan_articles(session)
        stats['paid_plan'] = len(paid_plan_articles)
        
        if paid_plan_articles:
            logger.info(f"Found {len(paid_plan_articles)} articles with paid plan messages")
            if not dry_run:
                for article in paid_plan_articles:
                    logger.debug(f"Removing paid plan: {article.title[:50]} (ID: {article.id})")
                    session.delete(article)
            else:
                for article in paid_plan_articles[:5]:  # Show first 5 examples
                    logger.info(f"  Would remove: {article.title[:50]} (ID: {article.id})")
                if len(paid_plan_articles) > 5:
                    logger.info(f"  ... and {len(paid_plan_articles) - 5} more")
        
        # Calculate total removed
        stats['total_removed'] = stats['empty_content'] + stats['paid_plan']
        
        # Commit if not dry run
        if not dry_run:
            session.commit()
            stats['total_articles_after'] = session.query(NewsArticle).count()
        else:
            stats['total_articles_after'] = stats['total_articles_before'] - stats['total_removed']
    
    return stats


def main():
    """Main entry point for the cleanup script."""
    parser = argparse.ArgumentParser(
        description='Clean up ANIP database by removing low-quality articles (empty content and paid plan messages)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run to see what would be removed
  python scripts/cleanup_database.py --dry-run
  
  # Actually remove empty and paid plan articles
  python scripts/cleanup_database.py
  
Note: Edit the DATABASE_URL variable at the top of this script to change the database connection.
        """
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be removed without actually deleting anything'
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("ANIP Database Cleanup Script")
    logger.info("=" * 60)
    
    # Show database URL being used (mask password for security)
    def mask_password_in_url(url: str) -> str:
        """Mask password in database URL for logging."""
        try:
            if '@' in url and '://' in url:
                # Format: postgresql://user:pass@host:port/db
                parts = url.split('@')
                if len(parts) == 2:
                    auth_part = parts[0]
                    rest = parts[1]
                    if '://' in auth_part:
                        protocol_user = auth_part.split('://')
                        if len(protocol_user) == 2:
                            protocol = protocol_user[0]
                            user_pass = protocol_user[1]
                            if ':' in user_pass:
                                user = user_pass.split(':')[0]
                                return f"{protocol}://{user}:****@{rest}"
        except Exception:
            pass
        return url
    
    logger.info(f"Database: {mask_password_in_url(DATABASE_URL)}")
    logger.info("")
    
    if args.dry_run:
        logger.info("🔍 DRY RUN MODE - No changes will be made")
        logger.info("")
    
    # Run cleanup
    stats = cleanup_database(dry_run=args.dry_run)
    
    # Print summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("Cleanup Summary")
    logger.info("=" * 60)
    logger.info(f"Total articles before: {stats['total_articles_before']}")
    logger.info(f"  - Empty content: {stats['empty_content']}")
    logger.info(f"  - Paid plan messages: {stats['paid_plan']}")
    logger.info(f"Total to remove: {stats['total_removed']}")
    logger.info(f"Total articles after: {stats['total_articles_after']}")
    
    if args.dry_run:
        logger.info("")
        logger.info("💡 Run without --dry-run to actually remove these articles")
    else:
        logger.info("")
        logger.info("✅ Cleanup completed successfully!")
    
    logger.info("=" * 60)


if __name__ == '__main__':
    main()

