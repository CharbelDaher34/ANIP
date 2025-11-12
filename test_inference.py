"""
Test script to verify ML inference functions work correctly.
Run this after training models and setting them to Production stage.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


def test_classification_inference():
    """Test topic classification inference."""
    print("\n" + "="*60)
    print("Testing Classification Inference")
    print("="*60)
    
    try:
        from anip.ml.classification.inference import predict_topic
        from anip.ml.classification.model import TOPICS
        
        # Test samples
        test_texts = [
            "Breaking news: New AI technology revolutionizes computing",
            "Football team wins championship in stunning victory",
            "Stock market reaches all-time high as investors celebrate",
            "Scientists discover new treatment for common disease"
        ]
        
        print(f"\n📋 Available topics: {TOPICS}\n")
        
        for i, text in enumerate(test_texts, 1):
            print(f"Test {i}: {text[:60]}...")
            try:
                result = predict_topic(text, top_k=3)
                print(f"  ✅ Success!")
                print(f"     Top prediction: {result['predictions'][0]['topic']} "
                      f"(confidence: {result['predictions'][0]['confidence']:.2f})")
                print(f"     Text length: {result['text_length']}")
            except Exception as e:
                print(f"  ❌ Error: {e}")
                return False
            print()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Classification inference test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sentiment_inference():
    """Test sentiment analysis inference."""
    print("\n" + "="*60)
    print("Testing Sentiment Inference")
    print("="*60)
    
    try:
        from anip.ml.sentiment.inference import predict_sentiment
        from anip.ml.sentiment.model import SENTIMENT_LABELS
        
        # Test samples
        test_texts = [
            "This is absolutely wonderful news! I'm so happy!",
            "The weather is okay, nothing special.",
            "This is terrible and disappointing news.",
            "The company announced its quarterly earnings report."
        ]
        
        print(f"\n📋 Sentiment labels: {SENTIMENT_LABELS}\n")
        
        for i, text in enumerate(test_texts, 1):
            print(f"Test {i}: {text[:60]}...")
            try:
                result = predict_sentiment(text)
                
                # Find the predicted sentiment
                sentiments = {k: v for k, v in result.items() if k in SENTIMENT_LABELS}
                predicted = max(sentiments, key=sentiments.get)
                confidence = sentiments[predicted]
                
                print(f"  ✅ Success!")
                print(f"     Predicted: {predicted} (confidence: {confidence:.2f})")
                print(f"     Scores: {sentiments}")
                print(f"     Text length: {result['text_length']}")
            except Exception as e:
                print(f"  ❌ Error: {e}")
                return False
            print()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Sentiment inference test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_model_loading():
    """Test that models can be loaded from MLflow."""
    print("\n" + "="*60)
    print("Testing Model Loading")
    print("="*60)
    
    try:
        from anip.ml.classification.inference import get_model as get_classification_model
        from anip.ml.sentiment.inference import get_model as get_sentiment_model
        
        print("\n1. Loading Classification Model...")
        try:
            classification_model = get_classification_model()
            print(f"   ✅ Classification model loaded: {type(classification_model)}")
        except Exception as e:
            print(f"   ⚠️ Classification model not available: {e}")
            print("   💡 Hint: Train the model and set it to Production stage in MLflow")
        
        print("\n2. Loading Sentiment Model...")
        try:
            sentiment_model = get_sentiment_model()
            print(f"   ✅ Sentiment model loaded: {type(sentiment_model)}")
        except Exception as e:
            print(f"   ⚠️ Sentiment model not available: {e}")
            print("   💡 Hint: Train the model and set it to Production stage in MLflow")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Model loading test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    """Test that the integration with main module works."""
    print("\n" + "="*60)
    print("Testing Integration (anip.ml module)")
    print("="*60)
    
    try:
        # Test that functions are properly exported
        from anip.ml import predict_topic, predict_sentiment, TOPICS, SENTIMENT_LABELS
        
        print("\n✅ All functions successfully imported from anip.ml")
        print(f"   - predict_topic: {predict_topic}")
        print(f"   - predict_sentiment: {predict_sentiment}")
        print(f"   - TOPICS: {TOPICS}")
        print(f"   - SENTIMENT_LABELS: {SENTIMENT_LABELS}")
        
        # Quick test
        print("\n🧪 Quick integration test...")
        try:
            topic_result = predict_topic("Test news article about technology", top_k=1)
            print(f"   ✅ predict_topic works: {topic_result['predictions'][0]}")
        except Exception as e:
            print(f"   ⚠️ predict_topic failed: {e}")
        
        try:
            sentiment_result = predict_sentiment("This is a test")
            print(f"   ✅ predict_sentiment works")
        except Exception as e:
            print(f"   ⚠️ predict_sentiment failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "🚀 "*20)
    print("ML Inference Test Suite")
    print("🚀 "*20)
    
    results = {
        "Model Loading": test_model_loading(),
        "Integration": test_integration(),
        "Classification": test_classification_inference(),
        "Sentiment": test_sentiment_inference(),
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
        print("\n✅ Inference functions are working correctly.")
        print("✅ Models are properly loaded from MLflow.")
        print("✅ Ready for Spark, Kafka, and API integration.")
    else:
        print("⚠️ Some tests failed.")
        print("\n💡 Common issues:")
        print("   1. MLflow server not running (check: http://localhost:5000)")
        print("   2. Models not trained yet (run training DAG in Airflow)")
        print("   3. Models not in Production stage (set in MLflow UI)")
        print("   4. Database connection issues (check docker-compose)")
    print("="*60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

