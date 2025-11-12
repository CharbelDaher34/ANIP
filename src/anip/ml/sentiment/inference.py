"""
Sentiment Analysis Inference with MLflow Model Loading.
Thread-safe model management with model serving support.
"""

import os
import threading
from typing import Dict, List, Optional, Any
import mlflow
import mlflow.pyfunc
from anip.config import settings

from .model import SENTIMENT_LABELS


class ModelServingClient:
    """Client for MLflow model serving endpoint."""
    
    def __init__(self, serving_url: str):
        self.serving_url = serving_url.rstrip('/')
        self._available = self._check_availability()
    
    def _check_availability(self) -> bool:
        """Check if serving endpoint is available."""
        try:
            import requests
            response = requests.get(f"{self.serving_url}/health", timeout=2)
            return response.status_code == 200
        except Exception:
            return False
    
    def predict(self, texts: List[str]) -> List[str]:
        """Make prediction via serving endpoint."""
        import requests
        
        try:
            response = requests.post(
                f"{self.serving_url}/invocations",
                json={"instances": texts},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()
            predictions = response.json()
            
            # Handle different response formats
            if isinstance(predictions, dict) and "predictions" in predictions:
                return predictions["predictions"]
            return predictions
        except Exception as e:
            raise RuntimeError(f"Model serving request failed: {e}")
    
    def is_available(self) -> bool:
        """Check if serving endpoint is available."""
        return self._available


class ModelManager:
    """Thread-safe model manager for sentiment analysis with serving support."""
    
    def __init__(self):
        self._model: Optional[Any] = None
        self._serving_client: Optional[ModelServingClient] = None
        self._lock = threading.Lock()
        self._model_version: Optional[str] = None
        self._use_serving = os.getenv("USE_MODEL_SERVING", "true").lower() == "true"
        self._serving_url = os.getenv("SENTIMENT_SERVING_URL", 
                                       "http://model-serving-sentiment:5002")
    
    def get_model(self, model_name: str = "sentiment-analysis", stage: str = "Production"):
        """Get model with thread-safe lazy loading or serving client."""
        # Try serving first if enabled
        if self._use_serving and self._serving_client is None:
            with self._lock:
                if self._serving_client is None:
                    try:
                        self._serving_client = ModelServingClient(self._serving_url)
                        if self._serving_client.is_available():
                            print(f"✅ Using model serving endpoint: {self._serving_url}")
                            return self._serving_client
                    except Exception as e:
                        print(f"⚠️ Model serving unavailable: {e}, falling back to local loading")
        
        # Return serving client if available
        if self._serving_client and self._serving_client.is_available():
            return self._serving_client
        
        # Fall back to local model loading
        if self._model is None:
            with self._lock:
                # Double-check locking pattern
                if self._model is None:
                    self._model = self._load_model(model_name, stage)
        return self._model
    
    def _load_model(self, model_name: str, stage: str):
        """Load model from MLflow Model Registry."""
        try:
            mlflow.set_tracking_uri(settings.mlflow.tracking_uri)
            
            # Try to load from Model Registry by stage
            if stage:
                model_uri = f"models:/{model_name}/{stage}"
            else:
                model_uri = f"models:/{model_name}/latest"
            
            print(f"📥 Loading model from: {model_uri}")
            print(f"   🔗 MLflow URI: {settings.mlflow.tracking_uri}")
            
            # Set timeout for model loading (important for production!)
            import os
            os.environ['MLFLOW_HTTP_REQUEST_TIMEOUT'] = '60'  # 60 seconds
            
            # Use concurrent.futures to enforce hard timeout
            from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
            import threading
            
            def load_model_task():
                return mlflow.pyfunc.load_model(model_uri)
            
            # Execute with 60-second timeout
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(load_model_task)
                try:
                    model = future.result(timeout=60)
                except FutureTimeoutError:
                    print(f"⏱️ Model loading timed out after 60 seconds")
                    raise TimeoutError(f"Model loading from {model_uri} timed out after 60 seconds")
            
            # Get model metadata for verification
            try:
                client = mlflow.tracking.MlflowClient()
                model_versions = client.search_model_versions(f"name='{model_name}'")
                
                # Find the version that matches the stage
                for mv in model_versions:
                    if mv.current_stage == stage:
                        self._model_version = mv.version
                        print("✅ Model loaded successfully")
                        print(f"   📌 Version: {mv.version}")
                        print(f"   🔖 Run ID: {mv.run_id}")
                        print(f"   📅 Created: {mv.creation_timestamp}")
                        print(f"   🎯 Stage: {mv.current_stage}")
                        break
            except Exception as meta_error:
                print(f"✅ Model loaded successfully (metadata unavailable: {meta_error})")
            
            return model
            
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            print(f"   Model URI: {model_uri}")
            print(f"   This may be expected if no model is in {stage} stage yet.")
            raise
    
    def reload_model(self, model_name: str = "sentiment-analysis", stage: str = "Production"):
        """Force reload model from MLflow."""
        with self._lock:
            self._model = None
            self._model_version = None
            return self.get_model(model_name, stage)


# Global model manager instance
_manager = ModelManager()


def load_model(model_name: str = "sentiment-analysis", stage: str = "Production"):
    """
    Load model from MLflow Model Registry.
    
    Args:
        model_name: Name of registered model
        stage: Model stage (Production, Staging, None)
        
    Returns:
        Loaded model
    """
    return _manager.get_model(model_name, stage)


def get_model():
    """Get cached model or load if not cached."""
    return _manager.get_model()


def predict_sentiment(text: str) -> Dict[str, float]:
    """
    Predict sentiment of text.
    
    Args:
        text: Input text to analyze
        
    Returns:
        Dictionary with sentiment scores (positive, neutral, negative)
    """
    model = get_model()
    
    # Check if using serving client or local model
    if isinstance(model, ModelServingClient):
        # Use serving endpoint
        predictions = model.predict([text])
        prediction = predictions[0]
    else:
        # Use local model
        # MLflow pyfunc predict expects a list or DataFrame
        # For sklearn text pipelines, just pass the text
        prediction = model.predict([text])[0]
    
    # Return prediction with high confidence for predicted class
    result = {label: 0.01 for label in SENTIMENT_LABELS}
    result[prediction] = 0.98
    result["text_length"] = len(text)
    return result


def reload_model():
    """Force reload model from MLflow."""
    return _manager.reload_model()


