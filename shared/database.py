"""
Database connection and session management for ANIP.
"""
import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool

# Create declarative base
Base = declarative_base()

def get_database_url():
    """
    Get database URL from environment variables.
    
    Raises:
        ValueError: If required environment variables are not set.
    """
    # Inside Docker, always use internal port 5432
    # POSTGRES_PORT env var is for external host access
    host = os.getenv("POSTGRES_HOST", "postgres")
    port = "5432" if host == "postgres" else os.getenv("POSTGRES_PORT", "5432")
    
    # Require password to be set (no default for security)
    postgres_user = os.getenv("POSTGRES_USER")
    postgres_password = os.getenv("POSTGRES_PASSWORD")
    postgres_db = os.getenv("POSTGRES_DB", "anip")
    
    if not postgres_user:
        raise ValueError("POSTGRES_USER environment variable is required")
    if not postgres_password:
        raise ValueError("POSTGRES_PASSWORD environment variable is required")
    
    return f"postgresql+psycopg2://{postgres_user}:{postgres_password}@{host}:{port}/{postgres_db}"

# Create engine with connection pooling
engine = create_engine(
    get_database_url(),
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Enable connection health checks
    pool_recycle=3600,   # Recycle connections after 1 hour
    echo=False
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def get_db_session():
    """
    Context manager for database sessions.
    Automatically commits on success and rolls back on error.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def init_database():
    """Initialize database tables."""
    from shared.models.news import NewsArticle
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")
    return True

