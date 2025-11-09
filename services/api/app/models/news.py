from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import Float, String

# ==============================
# Base Models
# ==============================

class NewsArticleBase(SQLModel):
    """Common fields for input/output models."""
    title: str = Field(index=True)
    content: str
    source: Optional[str] = Field(default=None, description="Publisher or website name")
    author: Optional[str] = Field(default=None)
    url: Optional[str] = Field(default=None, unique=True)
    published_at: Optional[datetime] = Field(default=None, index=True)
    language: Optional[str] = Field(default="en", max_length=5)
    region: Optional[str] = Field(default=None)

# ==============================
# Database Models
# ==============================

class NewsArticle(NewsArticleBase, table=True):
    """Main news article table."""
    id: Optional[int] = Field(default=None, primary_key=True)

    # ML-generated fields
    topic: Optional[str] = Field(default=None, index=True)
    sentiment: Optional[str] = Field(default=None)
    sentiment_score: Optional[float] = Field(default=None)

    # Embedding info
    embedding: Optional[List[float]] = Field(
        default=None,
        sa_column=Column(ARRAY(Float)),
        description="Vector embedding of the article content"
    )

    # Summary and agent output
    summary: Optional[str] = Field(default=None)
    keywords: Optional[List[str]] = Field(
        default=None,
        sa_column=Column(ARRAY(String))
    )

    # Data lineage
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship
    analyses: List["ArticleAnalysis"] = Relationship(back_populates="article")


class ArticleAnalysis(SQLModel, table=True):
    """Detailed analysis logs per article (optional)."""
    
    model_config = {"protected_namespaces": ()}  # Allow model_name field
    
    id: Optional[int] = Field(default=None, primary_key=True)
    article_id: int = Field(foreign_key="newsarticle.id")
    analysis_type: str = Field(description="classification, sentiment, embedding, summary")
    model_name: Optional[str] = Field(default=None)
    version: Optional[str] = Field(default=None)
    score: Optional[float] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship
    article: Optional[NewsArticle] = Relationship(back_populates="analyses")
