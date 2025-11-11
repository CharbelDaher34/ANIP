"""
Sentiment analysis model - Returns random predictions for now.
"""

import random
from typing import Dict


def predict_sentiment(text: str) -> Dict[str, float]:
    """
    Predict sentiment of text (random values for prototyping).
    
    Args:
        text: Input text to analyze
        
    Returns:
        Dictionary with sentiment scores (positive, neutral, negative)
    """
    # Generate random scores
    scores = [random.random() for _ in range(3)]
    total = sum(scores)
    
    # Normalize to sum to 1.0
    return {
        "positive": round(scores[0] / total, 3),
        "neutral": round(scores[1] / total, 3),
        "negative": round(scores[2] / total, 3),
        "text_length": len(text)
    }


if __name__ == "__main__":
    # Test
    sample_text = "This is a great news article about technology!"
    result = predict_sentiment(sample_text)
    print(f"Sentiment analysis: {result}")
