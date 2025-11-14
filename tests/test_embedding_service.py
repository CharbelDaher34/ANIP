#!/usr/bin/env python
"""
Test script for the Embedding Service.

Run with: python tests/test_embedding_service.py
Or with: uv run python tests/test_embedding_service.py

Make sure the embedding service is running:
    docker-compose up -d embedding-service
"""
import requests
import sys
from typing import List, Dict, Any


# Embedding service URL
EMBEDDING_SERVICE_URL = "http://localhost:5003"


def test_health_check() -> bool:
    """Test the health check endpoint."""
    try:
        response = requests.get(f"{EMBEDDING_SERVICE_URL}/health", timeout=5)
        response.raise_for_status()
        data = response.json()
        
        print("✅ Health Check:")
        print(f"   Status: {data.get('status')}")
        print(f"   Model: {data.get('model')}")
        print(f"   Dimension: {data.get('dimension')}")
        return True
    except Exception as e:
        print(f"❌ Health Check Failed: {e}")
        return False


def test_model_info() -> bool:
    """Test the model info endpoint."""
    try:
        response = requests.get(f"{EMBEDDING_SERVICE_URL}/info", timeout=5)
        response.raise_for_status()
        data = response.json()
        
        print("\n✅ Model Info:")
        print(f"   Model Name: {data.get('model_name')}")
        print(f"   Dimension: {data.get('dimension')}")
        print(f"   Max Sequence Length: {data.get('max_seq_length')}")
        print(f"   Status: {data.get('status')}")
        return True
    except Exception as e:
        print(f"❌ Model Info Failed: {e}")
        return False


def test_single_embedding() -> bool:
    """Test single text embedding generation."""
    try:
        test_text = "Artificial intelligence is transforming the world."
        
        payload = {
            "text": test_text,
            "normalize": True
        }
        
        response = requests.post(
            f"{EMBEDDING_SERVICE_URL}/embed",
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        embedding = data.get('embedding', [])
        dimension = data.get('dimension')
        model = data.get('model')
        
        print("\n✅ Single Embedding:")
        print(f"   Text: '{test_text}'")
        print(f"   Model: {model}")
        print(f"   Dimension: {dimension}")
        print(f"   Embedding (first 5 values): {embedding[:5]}")
        print(f"   Embedding length: {len(embedding)}")
        
        # Validate
        assert len(embedding) == dimension, f"Embedding length mismatch: {len(embedding)} != {dimension}"
        assert dimension == 384, f"Expected 384 dimensions, got {dimension}"
        
        return True
    except Exception as e:
        print(f"❌ Single Embedding Failed: {e}")
        return False


def test_batch_embeddings() -> bool:
    """Test batch embeddings generation."""
    try:
        test_texts = [
            "Machine learning is a subset of artificial intelligence.",
            "Natural language processing enables computers to understand human language.",
            "Deep learning uses neural networks with multiple layers.",
        ]
        
        payload = {
            "texts": test_texts,
            "normalize": True
        }
        
        response = requests.post(
            f"{EMBEDDING_SERVICE_URL}/embed/batch",
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        embeddings = data.get('embeddings', [])
        dimension = data.get('dimension')
        count = data.get('count')
        model = data.get('model')
        
        print("\n✅ Batch Embeddings:")
        print(f"   Model: {model}")
        print(f"   Number of texts: {len(test_texts)}")
        print(f"   Number of embeddings: {count}")
        print(f"   Dimension: {dimension}")
        
        for i, text in enumerate(test_texts):
            print(f"\n   Text {i+1}: '{text[:50]}...'")
            print(f"   Embedding (first 3): {embeddings[i][:3]}")
        
        # Validate
        assert count == len(test_texts), f"Count mismatch: {count} != {len(test_texts)}"
        assert len(embeddings) == count, f"Embeddings count mismatch"
        assert dimension == 384, f"Expected 384 dimensions, got {dimension}"
        
        for emb in embeddings:
            assert len(emb) == dimension, f"Embedding length mismatch"
        
        return True
    except Exception as e:
        print(f"❌ Batch Embeddings Failed: {e}")
        return False


def test_semantic_similarity() -> bool:
    """Test that similar texts have similar embeddings."""
    try:
        # Similar texts
        text1 = "The cat sat on the mat."
        text2 = "A cat is sitting on a mat."
        # Different text
        text3 = "Quantum physics explains subatomic particles."
        
        texts = [text1, text2, text3]
        payload = {"texts": texts, "normalize": True}
        
        response = requests.post(
            f"{EMBEDDING_SERVICE_URL}/embed/batch",
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        embeddings = data.get('embeddings', [])
        
        # Calculate cosine similarity (for normalized vectors, it's just dot product)
        def cosine_similarity(a: List[float], b: List[float]) -> float:
            return sum(x * y for x, y in zip(a, b))
        
        sim_1_2 = cosine_similarity(embeddings[0], embeddings[1])
        sim_1_3 = cosine_similarity(embeddings[0], embeddings[2])
        sim_2_3 = cosine_similarity(embeddings[1], embeddings[2])
        
        print("\n✅ Semantic Similarity:")
        print(f"   Text 1: '{text1}'")
        print(f"   Text 2: '{text2}'")
        print(f"   Text 3: '{text3}'")
        print(f"\n   Similarity (1 <-> 2): {sim_1_2:.4f} (similar texts)")
        print(f"   Similarity (1 <-> 3): {sim_1_3:.4f} (different texts)")
        print(f"   Similarity (2 <-> 3): {sim_2_3:.4f} (different texts)")
        
        # Similar texts should have higher similarity than different ones
        assert sim_1_2 > sim_1_3, "Similar texts should have higher similarity"
        assert sim_1_2 > sim_2_3, "Similar texts should have higher similarity"
        
        print(f"\n   ✓ Verification: Similar texts have higher similarity!")
        
        return True
    except Exception as e:
        print(f"❌ Semantic Similarity Failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("🧪 Testing Embedding Service")
    print("=" * 60)
    print(f"Service URL: {EMBEDDING_SERVICE_URL}")
    print("=" * 60)
    
    tests = [
        ("Health Check", test_health_check),
        ("Model Info", test_model_info),
        ("Single Embedding", test_single_embedding),
        ("Batch Embeddings", test_batch_embeddings),
        ("Semantic Similarity", test_semantic_similarity),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    # Exit with appropriate code
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()

