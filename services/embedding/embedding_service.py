"""
Embedding Microservice - Provides text embedding generation via HTTP API.
Loads sentence-transformers model once and serves embedding requests.
"""
import logging
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="ANIP Embedding Service",
    description="Text embedding generation using sentence-transformers",
    version="1.0.0"
)

# Global model instance (singleton)
_model: Optional[SentenceTransformer] = None
_model_lock = threading.Lock()
_model_name = "all-MiniLM-L6-v2"


def get_model() -> SentenceTransformer:
    """Get or load the embedding model (singleton pattern)."""
    global _model
    
    if _model is None:
        with _model_lock:
            if _model is None:
                logger.info(f"🔄 Loading embedding model: {_model_name}")
                _model = SentenceTransformer(_model_name)
                logger.info(f"✅ Embedding model loaded successfully")
    
    return _model


# Pydantic models
class EmbeddingRequest(BaseModel):
    """Request model for embedding generation."""
    text: str = Field(..., min_length=1, max_length=10000, description="Text to embed")
    normalize: bool = Field(default=True, description="Normalize embeddings to unit length")


class EmbeddingResponse(BaseModel):
    """Response model for embedding generation."""
    embedding: List[float] = Field(..., description="384-dimensional embedding vector")
    dimension: int = Field(..., description="Embedding dimension")
    model: str = Field(..., description="Model name used")


class BatchEmbeddingRequest(BaseModel):
    """Request model for batch embedding generation."""
    texts: List[str] = Field(..., min_items=1, max_items=100, description="List of texts to embed")
    normalize: bool = Field(default=True, description="Normalize embeddings to unit length")


class BatchEmbeddingResponse(BaseModel):
    """Response model for batch embedding generation."""
    embeddings: List[List[float]] = Field(..., description="List of embedding vectors")
    dimension: int = Field(..., description="Embedding dimension")
    count: int = Field(..., description="Number of embeddings")
    model: str = Field(..., description="Model name used")


# API endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        model = get_model()
        return {
            "status": "healthy",
            "model": _model_name,
            "dimension": model.get_sentence_embedding_dimension()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


@app.post("/embed", response_model=EmbeddingResponse)
async def generate_embedding(request: EmbeddingRequest):
    """
    Generate embedding for a single text.
    
    Args:
        request: EmbeddingRequest with text and normalize flag
        
    Returns:
        EmbeddingResponse with embedding vector
    """
    try:
        model = get_model()
        
        # Generate embedding
        embedding = model.encode(
            request.text,
            normalize_embeddings=request.normalize,
            show_progress_bar=False
        )
        
        return EmbeddingResponse(
            embedding=embedding.tolist(),
            dimension=len(embedding),
            model=_model_name
        )
        
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")


@app.post("/embed/batch", response_model=BatchEmbeddingResponse)
async def generate_embeddings_batch(request: BatchEmbeddingRequest):
    """
    Generate embeddings for multiple texts in a single request (more efficient).
    
    Args:
        request: BatchEmbeddingRequest with list of texts
        
    Returns:
        BatchEmbeddingResponse with list of embedding vectors
    """
    try:
        model = get_model()
        
        # Generate embeddings in batch (more efficient than individual requests)
        embeddings = model.encode(
            request.texts,
            normalize_embeddings=request.normalize,
            show_progress_bar=False,
            batch_size=32
        )
        
        return BatchEmbeddingResponse(
            embeddings=[emb.tolist() for emb in embeddings],
            dimension=len(embeddings[0]) if len(embeddings) > 0 else 0,
            count=len(embeddings),
            model=_model_name
        )
        
    except Exception as e:
        logger.error(f"Error generating batch embeddings: {e}")
        raise HTTPException(status_code=500, detail=f"Batch embedding generation failed: {str(e)}")


@app.get("/info")
async def model_info():
    """Get information about the embedding model."""
    try:
        model = get_model()
        return {
            "model_name": _model_name,
            "dimension": model.get_sentence_embedding_dimension(),
            "max_seq_length": model.max_seq_length,
            "status": "ready"
        }
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# Startup event
@app.on_event("startup")
async def startup_event():
    """Load model on startup."""
    logger.info("🚀 Starting Embedding Service")
    get_model()  # Pre-load model
    logger.info("✅ Embedding Service ready")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5003)

