"""
Test MLflow Model Serving Endpoints
Tests both classification and sentiment model serving containers.
"""

import requests
import json
import sys

import sys
import os
import time
# Add src to path, go to root through src/anip
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
#print cwd and sle

# Model serving endpoints
CLASSIFICATION_URL = "http://localhost:5001/invocations"
SENTIMENT_URL = "http://localhost:5002/invocations"

def test_classification():
    """Test classification model serving."""
    print("\n" + "="*60)
    print("Testing Classification Model Serving")
    print("="*60)
    
    test_cases = [
        "Apple releases new iPhone with advanced AI features and improved camera system",
        "Manchester United defeats rival team 3-0 in Premier League match",
        "Tesla stock drops 15% amid concerns about production delays",
        "New COVID-19 variant detected in multiple countries, health officials warn",
        "President announces new economic policy to combat inflation",
        "Hollywood celebrates blockbuster weekend at the box office",
        "NASA discovers potentially habitable exoplanet 100 light years away"
    ]
    
    try:
        response = requests.post(
            CLASSIFICATION_URL,
            json={"instances": test_cases},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        response.raise_for_status()
        
        predictions = response.json()
        print(f"\n✅ Classification successful!")
        print(f"   Response: {json.dumps(predictions, indent=2)}")
        
        if "predictions" in predictions:
            print(f"\n   Results:")
            for i, (text, pred) in enumerate(zip(test_cases, predictions["predictions"]), 1):
                print(f"   {i}. {text[:50]}... → {pred}")
        
        return True
        
    except requests.exceptions.Timeout:
        print(f"\n❌ Request timed out (>30s)")
        return False
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sentiment():
    """Test sentiment model serving."""
    print("\n" + "="*60)
    print("Testing Sentiment Model Serving")
    print("="*60)
    
    test_cases = [
        "This is the best product I have ever purchased! Highly recommended!",
        "The service was average, nothing particularly good or bad.",
        "Worst experience ever. Complete waste of time and money. Very disappointed!",
        "I hate this! Everything went wrong and nobody helped. Absolutely awful!",
        "Amazing performance! Exceeded all my expectations. Five stars!",
        "It's okay, does what it's supposed to do.",
        "Terrible quality. Broke after one day. Do not buy this garbage!"
    ]
    
    try:
        response = requests.post(
            SENTIMENT_URL,
            json={"instances": test_cases},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        response.raise_for_status()
        
        predictions = response.json()
        print(f"\n✅ Sentiment analysis successful!")
        print(f"   Response: {json.dumps(predictions, indent=2)}")
        
        if "predictions" in predictions:
            print(f"\n   Results:")
            for i, (text, pred) in enumerate(zip(test_cases, predictions["predictions"]), 1):
                print(f"   {i}. {text[:50]}... → {pred}")
        
        return True
        
    except requests.exceptions.Timeout:
        print(f"\n❌ Request timed out (>30s)")
        return False
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_health():
    """Test health endpoints."""
    print("\n" + "="*60)
    print("Testing Health Endpoints")
    print("="*60)
    
    results = {}
    
    # Classification health
    try:
        response = requests.get("http://localhost:5001/health", timeout=5)
        results["Classification"] = "✅ Healthy" if response.status_code == 200 else f"⚠️ Status {response.status_code}"
        print(f"   Classification: {results['Classification']}")
    except Exception as e:
        results["Classification"] = f"❌ Unhealthy: {e}"
        print(f"   Classification: {results['Classification']}")
    # Sentiment health
    try:
        response = requests.get("http://localhost:5002/health", timeout=5)
        results["Sentiment"] = "✅ Healthy" if response.status_code == 200 else f"⚠️ Status {response.status_code}"
        print(f"   Sentiment: {results['Sentiment']}")
    except Exception as e:
        results["Sentiment"] = f"❌ Unhealthy: {e}"
        print(f"   Sentiment: {results['Sentiment']}")
    
    for service, status in results.items():
        print(f"   {service:20} : {status}")
    
    return all("✅" in status for status in results.values())


def main():
    """Run all tests."""
    print("\n" + "🚀 "*20)
    print("MLflow Model Serving Test Suite")
    print("🚀 "*20)
    
    results = {
        "Health Check": test_health(),
        "Classification": test_classification(),
        "Sentiment": test_sentiment(),
    }
    
    print("\n" + "="*60)
    print("Test Results Summary")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:20} : {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 All tests passed!")
        print("\n✅ Model serving endpoints are working correctly.")
        print("✅ Models are loaded and responding to inference requests.")
        print("✅ Ready for production use!")
    else:
        print("⚠️ Some tests failed.")
        print("\n💡 Troubleshooting:")
        print("   1. Check containers are running: docker ps | grep model-serving")
        print("   2. Check logs: docker-compose logs model-serving-classification")
        print("   3. Verify models are in Production stage in MLflow UI")
    print("="*60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

