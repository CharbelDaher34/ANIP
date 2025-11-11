"""
Topic Classification Module.

Provides training and inference for news article topic classification.
"""

from .inference import predict_topic, load_model, reload_model
from .model import TOPICS, create_classification_model
from .train import train_and_evaluate, generate_mock_dataset

__all__ = [
    'predict_topic',
    'load_model',
    'reload_model',
    'TOPICS',
    'create_classification_model',
    'train_and_evaluate',
    'generate_mock_dataset'
]


