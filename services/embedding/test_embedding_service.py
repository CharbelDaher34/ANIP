#!/usr/bin/env python3
"""
Test script for the embedding service.
Run this after starting the embedding service to verify it works.
"""
import requests
import sys

SERVICE_URL = "http://localhost:5003"


def test_health():
    """Test health endpoint."""
    print("Testing /health endpoint...")
    try:
        response = requests.get(f"{SERVICE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False


def test_single_embedding():
    """Test single embedding generation."""
    print("\nTesting /embed endpoint...")
    try:
        response = requests.post(
            f"{SERVICE_URL}/embed",
            json={"text": "Machine learning is transforming the world.", "normalize": True},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Single embedding generated:")
            print(f"   - Dimension: {data['dimension']}")
            print(f"   - Model: {data['model']}")
            print(f"   - First 5 values: {data['embedding'][:5]}")
            return True
        else:
            print(f"❌ Embedding generation failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Embedding generation error: {e}")
        return False


def test_batch_embedding():
    """Test batch embedding generation."""
    print("\nTesting /embed/batch endpoint...")
    try:
        texts = [
            "Artificial intelligence is the future.",
            "Deep learning uses neural networks.",
            "Natural language processing enables AI to understand text."
        ]
        response = requests.post(
            f"{SERVICE_URL}/embed/batch",
            json={"texts": texts, "normalize": True},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Batch embeddings generated:")
            print(f"   - Count: {data['count']}")
            print(f"   - Dimension: {data['dimension']}")
            print(f"   - Model: {data['model']}")
            return True
        else:
            print(f"❌ Batch embedding generation failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Batch embedding generation error: {e}")
        return False


def test_info():
    """Test model info endpoint."""
    print("\nTesting /info endpoint...")
    try:
        response = requests.get(f"{SERVICE_URL}/info", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Model info:")
            print(f"   - Model: {data['model_name']}")
            print(f"   - Dimension: {data['dimension']}")
            print(f"   - Max sequence length: {data['max_seq_length']}")
            return True
        else:
            print(f"❌ Model info failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Model info error: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Testing Embedding Service")
    print("=" * 60)
    
    results = []
    results.append(("Health Check", test_health()))
    results.append(("Single Embedding", test_single_embedding()))
    results.append(("Batch Embedding", test_batch_embedding()))
    results.append(("Model Info", test_info()))
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    print("=" * 60)
    if all_passed:
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)

