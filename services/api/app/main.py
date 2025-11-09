"""
FastAPI application for ANIP API service.
"""
import sys
sys.path.insert(0, '/')

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.routes import router as api_router

app = FastAPI(
    title="ANIP API",
    description="Automated News Intelligence Pipeline API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to ANIP API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "api": "/api"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    from shared.database import engine
    
    try:
        # Test database connection
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "database": db_status
        }
    )

