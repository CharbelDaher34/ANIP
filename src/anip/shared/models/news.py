"""
News article data model.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ARRAY
from sqlalchemy.sql import func
from anip.shared.database import Base

class NewsArticle(Base):
    """News article model."""
    
    __tablename__ = 'newsarticle'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    content = Column(Text)
    source = Column(String(200))
    author = Column(String(200))
    url = Column(String(1000), unique=False, nullable=False)
    published_at = Column(DateTime)
    language = Column(String(50), default='en')
    region = Column(String(100))
    
    # ML predictions
    topic = Column(String(100))
    sentiment = Column(String(50))
    sentiment_score = Column(Float)
    embedding = Column(ARRAY(Float))
    
    # Additional fields
    summary = Column(Text)
    keywords = Column(ARRAY(String))
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        """Safe repr that works even when detached from session."""
        try:
            # Access __dict__ directly to avoid lazy loading
            id_val = self.__dict__.get('id', 'unknown')
            title_val = self.__dict__.get('title', 'unknown')
            source_val = self.__dict__.get('source', 'unknown')
            
            if title_val and title_val != 'unknown':
                title_val = title_val[:50] + '...' if len(title_val) > 50 else title_val
            
            return f"<NewsArticle(id={id_val}, title='{title_val}', source='{source_val}')>"
        except Exception:
            # Fallback if even __dict__ access fails
            return f"<NewsArticle at {hex(id(self))}>"

