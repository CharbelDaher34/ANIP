"""
Sentiment Analysis Training Script with MLflow Integration.
"""

import os
import random
from typing import List, Tuple, Dict
import mlflow
import mlflow.sklearn
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, f1_score

from .model import create_sentiment_model, SENTIMENT_LABELS


def generate_mock_dataset(n_samples: int = 1000) -> Tuple[List[str], List[str]]:
    """
    Generate mock dataset for sentiment analysis.
    
    Args:
        n_samples: Number of samples to generate
        
    Returns:
        Tuple of (texts, labels)
    """
    texts = []
    labels = []
    
    # Sentiment-specific keywords
    sentiment_keywords = {
        "positive": [
            "excellent", "great", "amazing", "wonderful", "fantastic", "good", "best",
            "love", "happy", "success", "win", "perfect", "outstanding", "brilliant"
        ],
        "neutral": [
            "report", "announced", "stated", "according", "said", "during", "meeting",
            "conference", "data", "information", "update", "news", "release", "event"
        ],
        "negative": [
            "bad", "terrible", "worst", "awful", "poor", "fail", "problem", "issue",
            "crisis", "disaster", "concern", "warning", "threat", "decline", "loss"
        ]
    }
    
    for _ in range(n_samples):
        sentiment = random.choice(SENTIMENT_LABELS)
        keywords = sentiment_keywords[sentiment]
        
        # Generate text with sentiment-specific keywords
        n_words = random.randint(15, 40)
        text_words = []
        
        for _ in range(n_words):
            if random.random() < 0.4:  # 40% chance to use sentiment keyword
                text_words.append(random.choice(keywords))
            else:
                text_words.append(random.choice([
                    "the", "a", "an", "is", "are", "was", "were", "has", "have",
                    "company", "market", "people", "report", "new", "today", "year"
                ]))
        
        texts.append(" ".join(text_words))
        labels.append(sentiment)
    
    return texts, labels


def train_and_evaluate(
    dataset: Tuple[List[str], List[str]] = None,
    test_size: float = 0.2,
    random_state: int = 42,
    mlflow_tracking_uri: str = "http://mlflow:5000",
    experiment_name: str = "sentiment-analysis"
) -> Dict:
    """
    Train and evaluate sentiment analysis model.
    
    Args:
        dataset: Tuple of (texts, labels). If None, generates mock dataset
        test_size: Proportion of data for testing
        random_state: Random seed for reproducibility
        mlflow_tracking_uri: MLflow tracking server URI
        experiment_name: MLflow experiment name
        
    Returns:
        Dictionary with training metrics and model info
    """
    # Generate or use provided dataset
    if dataset is None:
        print("📊 Generating mock dataset...")
        texts, labels = generate_mock_dataset(n_samples=1000)
    else:
        texts, labels = dataset
    
    print(f"📊 Dataset size: {len(texts)} samples")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=test_size, random_state=random_state, stratify=labels
    )
    
    print(f"🔀 Train: {len(X_train)}, Test: {len(X_test)}")
    
    # Set MLflow tracking
    mlflow.set_tracking_uri(mlflow_tracking_uri)
    mlflow.set_experiment(experiment_name)
    
    # Start MLflow run
    with mlflow.start_run() as run:
        print(f"🚀 MLflow Run ID: {run.info.run_id}")
        
        # Create and train model
        print("🔬 Training model...")
        model = create_sentiment_model()
        model.fit(X_train, y_train)
        
        # Evaluate
        print("📈 Evaluating model...")
        y_pred = model.predict(X_test)
        
        accuracy = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average='weighted')
        
        print(f"✅ Accuracy: {accuracy:.4f}")
        print(f"✅ F1 Score: {f1:.4f}")
        
        # Log parameters
        mlflow.log_param("n_samples", len(texts))
        mlflow.log_param("test_size", test_size)
        mlflow.log_param("random_state", random_state)
        mlflow.log_param("model_type", "LogisticRegression")
        
        # Log metrics
        mlflow.log_metric("accuracy", accuracy)
        mlflow.log_metric("f1_score", f1)
        
        # Log classification report
        report = classification_report(y_test, y_pred)
        print("\n📊 Classification Report:")
        print(report)
        
        # Save report as artifact
        report_path = "/tmp/sentiment_report.txt"
        with open(report_path, 'w') as f:
            f.write(report)
        mlflow.log_artifact(report_path)
        
        # Log model
        print("💾 Logging model to MLflow...")
        mlflow.sklearn.log_model(
            model,
            "model",
            registered_model_name="sentiment-analysis"
        )
        
        model_uri = f"runs:/{run.info.run_id}/model"
        
        print(f"✅ Model logged: {model_uri}")
        
        return {
            "run_id": run.info.run_id,
            "model_uri": model_uri,
            "accuracy": accuracy,
            "f1_score": f1,
            "n_samples": len(texts)
        }


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Training Sentiment Analysis Model")
    print("=" * 60)
    
    results = train_and_evaluate()
    
    print("\n" + "=" * 60)
    print("✅ Training Complete")
    print(f"📊 Accuracy: {results['accuracy']:.4f}")
    print(f"📊 F1 Score: {results['f1_score']:.4f}")
    print(f"🔗 Model URI: {results['model_uri']}")
    print("=" * 60)


