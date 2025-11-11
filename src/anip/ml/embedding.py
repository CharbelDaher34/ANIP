"""
Text embedding model - Returns random vectors for now.
"""

import random
from typing import List


def generate_embedding(text: str, dimension: int = 384) -> List[float]:
    """
    Generate text embedding (random vectors for prototyping).
    
    Args:
        text: Input text to embed
        dimension: Embedding dimension (default: 384)
        
    Returns:
        List of floats representing the embedding vector
    """
    # Generate random embedding vector
    embedding = [random.gauss(0, 1) for _ in range(dimension)]
    
    # Normalize
    magnitude = sum(x**2 for x in embedding) ** 0.5
    normalized = [x / magnitude for x in embedding]
    
    return normalized


if __name__ == "__main__":
    # Test
    sample_text = "Machine learning is transforming the world."
    embedding = generate_embedding(sample_text, dimension=128)
    print(f"Embedding dimension: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")
