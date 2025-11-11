"""
Topic classification model - Returns random predictions for now.
"""

import random
from typing import Dict, List


TOPICS = [
    "politics",
    "technology",
    "sports",
    "business",
    "entertainment",
    "health",
    "science",
    "world"
]


def predict_topic(text: str, top_k: int = 3) -> Dict[str, any]:
    """
    Predict topic of text (random values for prototyping).
    
    Args:
        text: Input text to classify
        top_k: Number of top predictions to return
        
    Returns:
        Dictionary with top topics and confidence scores
    """
    # Generate random scores for all topics
    scores = {topic: random.random() for topic in TOPICS}
    
    # Sort by score and get top_k
    sorted_topics = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    
    return {
        "predictions": [
            {"topic": topic, "confidence": round(score, 3)}
            for topic, score in sorted_topics
        ],
        "text_length": len(text)
    }


if __name__ == "__main__":
    # Test
    sample_text = "The latest iPhone release features advanced AI capabilities."
    result = predict_topic(sample_text)
    print(f"Topic classification: {result}")
