"""
Custom MLflow Model Serving with Hot Reload Support.

This wrapper around MLflow models adds a /reload endpoint that allows
reloading the latest Production model without restarting the container.
"""
import os
import sys
import logging
import threading
from typing import Optional, Dict, Any

import mlflow
import mlflow.pyfunc
from fastapi import FastAPI, HTTPException, Request
import uvicorn
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PredictionRequest(BaseModel):
    """Request model for predictions."""
    dataframe_split: Optional[Dict[str, Any]] = None
    instances: Optional[list] = None


class PredictionResponse(BaseModel):
    """Response model for predictions."""
    predictions: list


class ReloadResponse(BaseModel):
    """Response model for reload endpoint."""
    status: str
    message: str
    model_uri: str
    old_version: str = None
    new_version: str = None
    version_changed: bool = False


class MLflowModelServer:
    """MLflow model server with hot reload capability."""
    
    def __init__(self, model_uri: str, model_name: str):
        """
        Initialize the model server.
        
        Args:
            model_uri: MLflow model URI (e.g., models:/model-name/Production)
            model_name: Human-readable model name for logging
        """
        self.model_uri = model_uri
        self.model_name = model_name
        self.model = None
        self.model_lock = threading.Lock()
        self.model_metadata = {}
        self.load_model()
    
    def load_model(self):
        """Load or reload the model from MLflow."""
        logger.info(f"🔄 Loading model from: {self.model_uri}")
        
        try:
            with self.model_lock:
                # Load model using MLflow
                self.model = mlflow.pyfunc.load_model(self.model_uri)
                
                # Get model metadata
                self._update_metadata()
                
                logger.info(f"✅ Model '{self.model_name}' loaded successfully")
                logger.info(f"   Version: {self.model_metadata.get('version', 'unknown')}")
                logger.info(f"   Run ID: {self.model_metadata.get('run_id', 'unknown')[:8]}...")
                
        except Exception as e:
            logger.error(f"❌ Failed to load model '{self.model_name}': {e}")
            raise
    
    def _update_metadata(self):
        """Update model metadata from MLflow."""
        import datetime
        from mlflow.tracking import MlflowClient
        
        try:
            client = MlflowClient()
            
            # Extract model name from URI (e.g., "models:/model-name/Production")
            if self.model_uri.startswith("models:/"):
                parts = self.model_uri.replace("models:/", "").split("/")
                model_name = parts[0]
                stage = parts[1] if len(parts) > 1 else "None"
                
                # Get the latest version in the specified stage
                versions = client.get_latest_versions(model_name, stages=[stage])
                if versions:
                    version = versions[0]
                    self.model_metadata = {
                        "model_name": model_name,
                        "version": version.version,
                        "stage": version.current_stage,
                        "run_id": version.run_id,
                        "status": version.status,
                        "loaded_at": datetime.datetime.now().isoformat()
                    }
                else:
                    self.model_metadata = {
                        "model_name": model_name,
                        "stage": stage,
                        "loaded_at": datetime.datetime.now().isoformat()
                    }
        except Exception as e:
            logger.warning(f"Could not fetch model metadata: {e}")
            self.model_metadata = {
                "loaded_at": datetime.datetime.now().isoformat(),
                "error": str(e)
            }
    
    def reload_model(self):
        """Reload the model from MLflow (hot reload)."""
        logger.info(f"🔄 Reloading model '{self.model_name}' from: {self.model_uri}")
        
        old_version = self.model_metadata.get('version', 'unknown')
        old_run_id = self.model_metadata.get('run_id', 'unknown')
        
        try:
            # Load new model instance
            new_model = mlflow.pyfunc.load_model(self.model_uri)
            
            # Atomically swap the model and update metadata
            with self.model_lock:
                self.model = new_model
                self._update_metadata()
            
            new_version = self.model_metadata.get('version', 'unknown')
            new_run_id = self.model_metadata.get('run_id', 'unknown')
            
            if old_version != new_version or old_run_id != new_run_id:
                logger.info(f"✅ Model '{self.model_name}' reloaded - Version changed!")
                logger.info(f"   Old: v{old_version} (run: {old_run_id[:8]}...)")
                logger.info(f"   New: v{new_version} (run: {new_run_id[:8]}...)")
            else:
                logger.info(f"✅ Model '{self.model_name}' reloaded (same version)")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to reload model '{self.model_name}': {e}")
            raise
    
    def predict(self, data):
        """Make predictions using the loaded model."""
        with self.model_lock:
            if self.model is None:
                raise RuntimeError(f"Model '{self.model_name}' not loaded")
            return self.model.predict(data)


def create_app(model_uri: str, model_name: str) -> FastAPI:
    """
    Create FastAPI app with MLflow model serving.
    
    Args:
        model_uri: MLflow model URI
        model_name: Model name for logging
    
    Returns:
        FastAPI application
    """
    app = FastAPI(
        title=f"MLflow Model Server - {model_name}",
        description=f"Serving {model_name} with hot reload support",
        version="1.0.0"
    )
    
    # Initialize model server
    model_server = MLflowModelServer(model_uri=model_uri, model_name=model_name)
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "model_name": model_name,
            "model_uri": model_uri
        }
    
    @app.get("/info")
    async def model_info():
        """
        Get detailed model information.
        
        Returns model metadata including version, run_id, and load time.
        Use this to verify which model version is currently loaded.
        """
        return {
            "model_name": model_name,
            "model_uri": model_uri,
            "metadata": model_server.model_metadata,
            "status": "loaded" if model_server.model is not None else "not_loaded"
        }
    
    @app.post("/reload", response_model=ReloadResponse)
    async def reload_model():
        """
        Reload the model from MLflow Model Registry.
        
        This endpoint allows hot-reloading the model without restarting
        the container. When a new model version is promoted to Production,
        calling this endpoint will load the new model.
        """
        try:
            old_version = model_server.model_metadata.get('version', 'unknown')
            old_run_id = model_server.model_metadata.get('run_id', 'unknown')
            
            model_server.reload_model()
            
            new_version = model_server.model_metadata.get('version', 'unknown')
            new_run_id = model_server.model_metadata.get('run_id', 'unknown')
            
            version_changed = (old_version != new_version) or (old_run_id != new_run_id)
            
            return ReloadResponse(
                status="success",
                message=f"Model '{model_name}' reloaded successfully" + 
                        (" - version changed!" if version_changed else " (same version)"),
                model_uri=model_uri,
                old_version=f"v{old_version}",
                new_version=f"v{new_version}",
                version_changed=version_changed
            )
        except Exception as e:
            logger.error(f"Failed to reload model: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to reload model: {str(e)}"
            )
    
    @app.post("/invocations")
    async def predict(request: Request):
        """
        Prediction endpoint (MLflow-compatible).
        
        Accepts input in MLflow's standard format:
        - dataframe_split: {"columns": [...], "data": [[...]]}
        - instances: [...]
        """
        try:
            # Parse request body
            body = await request.json()
            
            # Handle different input formats
            if "dataframe_split" in body:
                import pandas as pd
                df_data = body["dataframe_split"]
                data = pd.DataFrame(
                    data=df_data["data"],
                    columns=df_data.get("columns")
                )
            elif "instances" in body:
                data = body["instances"]
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid input format. Expected 'dataframe_split' or 'instances'"
                )
            
            # Make prediction
            predictions = model_server.predict(data)
            
            # Convert predictions to list if needed
            if hasattr(predictions, 'tolist'):
                predictions = predictions.tolist()
            
            return {"predictions": predictions}
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Prediction failed: {str(e)}"
            )
    
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "message": f"MLflow Model Server - {model_name}",
            "model_uri": model_uri,
            "endpoints": {
                "health": "/health",
                "predict": "/invocations (POST)",
                "reload": "/reload (POST)"
            }
        }
    
    return app


def main():
    """Main entry point for the model server."""
    # Get configuration from environment variables
    model_uri = os.getenv("MODEL_URI")
    model_name = os.getenv("MODEL_NAME", "model")
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5000"))
    
    # Validate configuration
    if not model_uri:
        logger.error("❌ MODEL_URI environment variable not set")
        sys.exit(1)
    
    # Set MLflow tracking URI if provided
    mlflow_tracking_uri = os.getenv("MLFLOW_TRACKING_URI")
    if mlflow_tracking_uri:
        mlflow.set_tracking_uri(mlflow_tracking_uri)
        logger.info(f"🔗 MLflow tracking URI: {mlflow_tracking_uri}")
    
    logger.info("🚀 Starting MLflow Model Server")
    logger.info(f"   Model: {model_name}")
    logger.info(f"   URI: {model_uri}")
    logger.info(f"   Host: {host}:{port}")
    
    # Create and run FastAPI app
    app = create_app(model_uri=model_uri, model_name=model_name)
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    main()

