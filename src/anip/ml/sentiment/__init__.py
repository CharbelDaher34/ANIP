"""
Sentiment Analysis Module.

Provides training and inference for news article sentiment analysis.
"""

from .inference import predict_sentiment, load_model, reload_model
from .model import SENTIMENT_LABELS, create_sentiment_model
from .train import train_and_evaluate, generate_mock_dataset

__all__ = [
    'predict_sentiment',
    'load_model',
    'reload_model',
    'SENTIMENT_LABELS',
    'create_sentiment_model',
    'train_and_evaluate',
    'generate_mock_dataset'
]


