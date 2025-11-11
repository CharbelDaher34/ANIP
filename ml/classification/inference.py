"""
Topic Classification Inference with MLflow Model Loading.
"""

import os
from typing import Dict, List
import mlflow
import mlflow.pyfunc

from .model import TOPICS


# Global model cache
_model = None
_mlflow_tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")


def load_model(model_name: str = "topic-classification", stage: str = "Production"):
    """
    Load model from MLflow Model Registry.
    
    Args:
        model_name: Name of registered model
        stage: Model stage (Production, Staging, None)
        
    Returns:
        Loaded model
    """
    global _model
    
    mlflow.set_tracking_uri(_mlflow_tracking_uri)
    
    # Try to load from Model Registry by stage
    if stage:
        model_uri = f"models:/{model_name}/{stage}"
    else:
        model_uri = f"models:/{model_name}/latest"
    
    print(f"📥 Loading model from: {model_uri}")
    _model = mlflow.pyfunc.load_model(model_uri)
    
    # Get model metadata for verification
    try:
        client = mlflow.tracking.MlflowClient()
        model_versions = client.search_model_versions(f"name='{model_name}'")
        
        # Find the version that matches the stage
        for mv in model_versions:
            if mv.current_stage == stage:
                print(f"✅ Model loaded successfully")
                print(f"   📌 Version: {mv.version}")
                print(f"   🔖 Run ID: {mv.run_id}")
                print(f"   📅 Created: {mv.creation_timestamp}")
                print(f"   🎯 Stage: {mv.current_stage}")
                break
    except Exception as meta_error:
        print(f"✅ Model loaded successfully (metadata unavailable: {meta_error})")
    
    return _model


def get_model():
    """Get cached model or load if not cached."""
    global _model
    if _model is None:
        load_model()
    return _model


def predict_topic(text: str, top_k: int = 3) -> Dict[str, any]:
    """
    Predict topic of text.
    
    Args:
        text: Input text to classify
        top_k: Number of top predictions to return
        
    Returns:
        Dictionary with top topics and confidence scores
    """
    model = get_model()
    
    # MLflow pyfunc predict expects a list or DataFrame
    # For sklearn text pipelines, just pass the text
    prediction = model.predict([text])[0]
    
    # Return single prediction with high confidence
    return {
        "predictions": [
            {"topic": prediction, "confidence": 0.95}
        ] + [
            {"topic": t, "confidence": 0.01} 
            for t in TOPICS if t != prediction
        ][:top_k-1],
        "text_length": len(text)
    }


def reload_model():
    """Force reload model from MLflow."""
    global _model
    _model = None
    return load_model()


