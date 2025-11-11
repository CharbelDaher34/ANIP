"""
Topic Classification Training Script with MLflow Integration.
"""

import os
import random
from typing import List, Tuple
import mlflow
import mlflow.sklearn
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, f1_score

from .model import create_classification_model, TOPICS


def generate_mock_dataset(n_samples: int = 1000) -> Tuple[List[str], List[str]]:
    """
    Generate mock dataset for topic classification.
    
    Args:
        n_samples: Number of samples to generate
        
    Returns:
        Tuple of (texts, labels)
    """
    texts = []
    labels = []
    
    # Topic-specific keywords for generating mock data
    topic_keywords = {
        "politics": ["election", "government", "president", "policy", "vote", "congress", "senate"],
        "technology": ["software", "AI", "computer", "tech", "startup", "innovation", "digital"],
        "sports": ["game", "player", "team", "championship", "score", "match", "league"],
        "business": ["company", "market", "stock", "CEO", "revenue", "profit", "investment"],
        "entertainment": ["movie", "music", "celebrity", "show", "film", "actor", "performance"],
        "health": ["medical", "disease", "doctor", "treatment", "health", "patient", "hospital"],
        "science": ["research", "study", "scientist", "discovery", "experiment", "theory", "data"],
        "world": ["international", "country", "global", "nation", "foreign", "crisis", "region"]
    }
    
    for _ in range(n_samples):
        topic = random.choice(TOPICS)
        keywords = topic_keywords[topic]
        
        # Generate text with topic-specific keywords
        n_words = random.randint(20, 50)
        text_words = []
        
        for _ in range(n_words):
            if random.random() < 0.3:  # 30% chance to use topic keyword
                text_words.append(random.choice(keywords))
            else:
                text_words.append(random.choice([
                    "the", "a", "an", "is", "are", "was", "were", "has", "have",
                    "new", "latest", "breaking", "major", "report", "news", "says"
                ]))
        
        texts.append(" ".join(text_words))
        labels.append(topic)
    
    return texts, labels


def train_and_evaluate(
    dataset: Tuple[List[str], List[str]] = None,
    test_size: float = 0.2,
    random_state: int = 42,
    mlflow_tracking_uri: str = "http://mlflow:5000",
    experiment_name: str = "topic-classification"
) -> dict:
    """
    Train and evaluate topic classification model.
    
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
        model = create_classification_model()
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
        mlflow.log_param("model_type", "MultinomialNB")
        
        # Log metrics
        mlflow.log_metric("accuracy", accuracy)
        mlflow.log_metric("f1_score", f1)
        
        # Log classification report
        report = classification_report(y_test, y_pred)
        print("\n📊 Classification Report:")
        print(report)
        
        # Save report as artifact
        report_path = "/tmp/classification_report.txt"
        with open(report_path, 'w') as f:
            f.write(report)
        mlflow.log_artifact(report_path)
        
        # Log model
        print("💾 Logging model to MLflow...")
        mlflow.sklearn.log_model(
            model,
            "model",
            registered_model_name="topic-classification"
        )
        
        # Register best model based on accuracy
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
    print("🚀 Training Topic Classification Model")
    print("=" * 60)
    
    results = train_and_evaluate()
    
    print("\n" + "=" * 60)
    print("✅ Training Complete")
    print(f"📊 Accuracy: {results['accuracy']:.4f}")
    print(f"📊 F1 Score: {results['f1_score']:.4f}")
    print(f"🔗 Model URI: {results['model_uri']}")
    print("=" * 60)


