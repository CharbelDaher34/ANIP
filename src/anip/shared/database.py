"""
Database connection and session management for ANIP.
"""
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
from anip.config import settings

# Create declarative base
Base = declarative_base()

def get_database_url():
    """
    Get database URL from settings.
    
    Returns:
        Database connection URL
    """
    return settings.database.url

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
# expire_on_commit=False keeps objects usable after session closes
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    expire_on_commit=False  # Critical for FastAPI: objects stay accessible after session closes
)

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
    from anip.shared.models.news import NewsArticle
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")
    return True

