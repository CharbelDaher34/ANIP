"""
Conversation and Message data models for the chat UI.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from anip.shared.database import Base


class Conversation(Base):
    """Conversation model for chat sessions."""
    
    __tablename__ = 'conversation'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationship to messages
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, title='{self.title[:50]}')>"


class Message(Base):
    """Message model for storing user queries and agent responses."""
    
    __tablename__ = 'message'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey('conversation.id', ondelete='CASCADE'), nullable=False)
    
    # Message content
    user_query = Column(Text, nullable=False)
    
    # Agent response (LLM-generated)
    summary = Column(Text)
    answer = Column(Text)
    query_intent = Column(String(200))
    
    # Search results (stored as JSON)
    duckduckgo_results = Column(JSON)
    database_results = Column(JSON)
    
    # Metadata
    sources_used = Column(JSON)
    total_results = Column(Integer, default=0)
    duckduckgo_count = Column(Integer, default=0)
    database_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationship to conversation
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self):
        return f"<Message(id={self.id}, conversation_id={self.conversation_id}, query='{self.user_query[:50]}')>"


