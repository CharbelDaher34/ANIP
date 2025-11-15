"""
API routes for conversations and messages.
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from datetime import datetime

from anip.shared.database import get_db_session
from anip.shared.models.conversation import Conversation, Message
from anip.agent import search_news

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/conversations", tags=["conversations"])


# ==================== Pydantic Models ====================

class ConversationCreate(BaseModel):
    """Request model for creating a conversation."""
    title: str


class ConversationResponse(BaseModel):
    """Response model for a conversation."""
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    """Request model for creating a message."""
    user_query: str
    max_results: int = 5
    search_provider: str = "both"


class NewsResult(BaseModel):
    """Individual news result."""
    title: str
    url: str
    snippet: Optional[str] = None
    source: Optional[str] = None
    published_at: Optional[str] = None
    topic: Optional[str] = None
    sentiment: Optional[str] = None
    relevance_score: Optional[float] = None


class MessageResponse(BaseModel):
    """Response model for a message."""
    id: int
    conversation_id: int
    user_query: str
    summary: Optional[str]
    answer: Optional[str]
    query_intent: Optional[str]
    duckduckgo_results: Optional[List[dict]] = []
    database_results: Optional[List[dict]] = []
    sources_used: Optional[List[str]] = []
    total_results: int = 0
    duckduckgo_count: int = 0
    database_count: int = 0
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== Routes ====================

@router.get("/", response_model=List[ConversationResponse])
async def get_conversations():
    """Get all conversations ordered by most recent."""
    try:
        with get_db_session() as session:
            conversations = session.query(Conversation).order_by(
                Conversation.updated_at.desc()
            ).all()
            
            # Add message count to each conversation
            result = []
            for conv in conversations:
                conv_dict = {
                    "id": conv.id,
                    "title": conv.title,
                    "created_at": conv.created_at,
                    "updated_at": conv.updated_at,
                    "message_count": len(conv.messages)
                }
                result.append(conv_dict)
            
            return result
            
    except Exception as e:
        logger.error(f"Error fetching conversations: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch conversations"
        )


@router.post("/", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(conversation: ConversationCreate):
    """Create a new conversation."""
    try:
        with get_db_session() as session:
            new_conversation = Conversation(
                title=conversation.title
            )
            session.add(new_conversation)
            session.commit()
            session.refresh(new_conversation)
            
            return {
                "id": new_conversation.id,
                "title": new_conversation.title,
                "created_at": new_conversation.created_at,
                "updated_at": new_conversation.updated_at,
                "message_count": 0
            }
            
    except Exception as e:
        logger.error(f"Error creating conversation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create conversation"
        )


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: int):
    """Get a specific conversation."""
    try:
        with get_db_session() as session:
            conversation = session.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()
            
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found"
                )
            
            return {
                "id": conversation.id,
                "title": conversation.title,
                "created_at": conversation.created_at,
                "updated_at": conversation.updated_at,
                "message_count": len(conversation.messages)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching conversation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch conversation"
        )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(conversation_id: int):
    """Delete a conversation and all its messages."""
    try:
        with get_db_session() as session:
            conversation = session.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()
            
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found"
                )
            
            session.delete(conversation)
            session.commit()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete conversation"
        )


@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(conversation_id: int):
    """Get all messages in a conversation."""
    try:
        with get_db_session() as session:
            # Check if conversation exists
            conversation = session.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()
            
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found"
                )
            
            # Get messages ordered by creation time
            messages = session.query(Message).filter(
                Message.conversation_id == conversation_id
            ).order_by(Message.created_at.asc()).all()
            
            return messages
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching messages: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch messages"
        )


@router.post("/{conversation_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(conversation_id: int, message: MessageCreate):
    """
    Create a new message in a conversation.
    This calls the news agent and stores the results.
    """
    try:
        # Check if conversation exists
        with get_db_session() as session:
            conversation = session.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()
            
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found"
                )
        
        # Call the news agent
        logger.info(f"Calling news agent for query: {message.user_query}")
        agent_result = await search_news(
            query=message.user_query,
            max_results=message.max_results,
            search_provider=message.search_provider
        )
        
        # Convert Pydantic models to dicts for JSON storage
        duckduckgo_results = [
            {
                "title": r.title,
                "url": r.url,
                "content": r.content,
                "source": r.source,
                "published_at": r.published_at,
                "topic": r.topic,
                "sentiment": r.sentiment,
                "relevance_score": r.relevance_score
            }
            for r in agent_result.duckduckgo_results
        ]
        
        database_results = [
            {
                "title": r.title,
                "url": r.url,
                "content": r.content,
                "source": r.source,
                "published_at": r.published_at,
                "topic": r.topic,
                "sentiment": r.sentiment,
                "relevance_score": r.relevance_score
            }
            for r in agent_result.database_results
        ]
        
        # Save message to database
        with get_db_session() as session:
            new_message = Message(
                conversation_id=conversation_id,
                user_query=message.user_query,
                summary=agent_result.summary,
                answer=agent_result.answer,
                query_intent=agent_result.query_intent,
                duckduckgo_results=duckduckgo_results,
                database_results=database_results,
                sources_used=agent_result.sources_used,
                total_results=agent_result.total_results,
                duckduckgo_count=agent_result.duckduckgo_count,
                database_count=agent_result.database_count
            )
            session.add(new_message)
            session.commit()
            session.refresh(new_message)
            
            # Update conversation's updated_at timestamp
            conversation = session.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()
            if conversation:
                # Touch the conversation to update its timestamp
                session.query(Conversation).filter(
                    Conversation.id == conversation_id
                ).update({"updated_at": datetime.utcnow()})
                session.commit()
            
            return new_message
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating message: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create message: {str(e)}"
        )

