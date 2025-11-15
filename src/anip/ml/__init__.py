"""
Machine Learning Module for News Article Processing.

This module provides ML capabilities for:
- Topic classification
- Sentiment analysis
- Text embedding generation
- Text summarization

All models are managed via MLflow for tracking, versioning, and deployment.
"""

# Import classification functions
from .classification import predict_topic as classification_predict_topic
from .classification import TOPICS

# Import sentiment functions
from .sentiment import predict_sentiment as sentiment_predict_sentiment
from .sentiment import SENTIMENT_LABELS

# Import legacy modules (embedding and summarization still use old implementation)
from .embedding import generate_embedding


# ==================== Backward Compatible API ====================

def predict_topic(text: str, top_k: int = 3):
    """
    Predict topic of text using MLflow-managed model.
    
    Backward compatible wrapper for classification.predict_topic.
    
    Args:
        text: Input text to classify
        top_k: Number of top predictions to return
        
    Returns:
        Dictionary with top topics and confidence scores
    """
    return classification_predict_topic(text, top_k)


def predict_sentiment(text: str):
    """
    Predict sentiment of text using MLflow-managed model.
    
    Backward compatible wrapper for sentiment.predict_sentiment.
    
    Args:
        text: Input text to analyze
        
    Returns:
        Dictionary with sentiment scores (positive, neutral, negative)
    """
    return sentiment_predict_sentiment(text)


# ==================== Exports ====================

__all__ = [
    # Classification
    'predict_topic',
    'TOPICS',
    
    # Sentiment
    'predict_sentiment',
    'SENTIMENT_LABELS',
    
    # Embedding (legacy)
    'generate_embedding',
]


