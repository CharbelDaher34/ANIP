"""
News article data model.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ARRAY
from sqlalchemy.sql import func
from shared.database import Base

class NewsArticle(Base):
    """News article model."""
    
    __tablename__ = 'newsarticle'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    content = Column(Text)
    source = Column(String(200))
    author = Column(String(200))
    url = Column(String(1000), unique=True, nullable=False)
    published_at = Column(DateTime)
    language = Column(String(10), default='en')
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
        return f"<NewsArticle(id={self.id}, title='{self.title[:50]}...', source='{self.source}')>"

