"""
Text embedding client - Connects to the embedding microservice.
"""

import os
from typing import List
import requests


def get_embedding_service_url() -> str:
    """Get the embedding service URL from environment or use default."""
    return os.getenv("EMBEDDING_SERVICE_URL", "http://embedding-service:5003")


def generate_embedding(text: str, dimension: int = 384) -> List[float]:
    """
    Generate text embedding by calling the embedding microservice.
    
    Args:
        text: Input text to embed
        dimension: Embedding dimension (default: 384, ignored - returned by service)
        
    Returns:
        List of floats representing the embedding vector
        
    Raises:
        Exception: If the embedding service is unavailable or returns an error
    """
    service_url = get_embedding_service_url()
    
    try:
        response = requests.post(
            f"{service_url}/embed",
            json={"text": text, "normalize": True},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["embedding"]
        else:
            raise Exception(f"Embedding service returned status {response.status_code}: {response.text}")
            
    except requests.exceptions.ConnectionError:
        raise Exception(f"Cannot connect to embedding service at {service_url}")
    except requests.exceptions.Timeout:
        raise Exception(f"Embedding service timeout at {service_url}")
    except Exception as e:
        raise Exception(f"Error generating embedding: {str(e)}")


def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for multiple texts in batch (more efficient).
    
    Args:
        texts: List of texts to embed
        
    Returns:
        List of embedding vectors
        
    Raises:
        Exception: If the embedding service is unavailable or returns an error
    """
    service_url = get_embedding_service_url()
    
    try:
        response = requests.post(
            f"{service_url}/embed/batch",
            json={"texts": texts, "normalize": True},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["embeddings"]
        else:
            raise Exception(f"Embedding service returned status {response.status_code}: {response.text}")
            
    except requests.exceptions.ConnectionError:
        raise Exception(f"Cannot connect to embedding service at {service_url}")
    except requests.exceptions.Timeout:
        raise Exception(f"Embedding service timeout at {service_url}")
    except Exception as e:
        raise Exception(f"Error generating batch embeddings: {str(e)}")


if __name__ == "__main__":
    # Test
    sample_text = "Machine learning is transforming the world."
    embedding = generate_embedding(sample_text, dimension=128)
    print(f"Embedding dimension: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")
