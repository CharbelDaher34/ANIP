"""
FastAPI application for ANIP API service.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy import text
from pathlib import Path

from app.news import router as news_router
from app.conversations import router as conversations_router
from anip.shared.database import Base, engine
from anip.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for FastAPI app.
    Drops and recreates all database tables on startup.
    """
    logger.info("🚀 Starting ANIP API - Initializing database...")
    
    try:
        # Drop all tables with CASCADE to handle foreign key dependencies
        # logger.info("🗑️  Dropping all existing tables...")
        # with engine.begin() as conn:
        #     # Drop all tables with CASCADE to handle foreign key constraints // only the tables related to the news model
        #     conn.execute(text("DROP TABLE IF EXISTS newsarticle CASCADE"))
        # logger.info("✅ News article table dropped successfully")
        
        # Create all tables
        logger.info("📦 Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")
        
    except Exception as e:
        logger.error(f"❌ Error during database initialization: {e}", exc_info=True)
        raise
    
    logger.info("✅ ANIP API startup complete")
    
    yield
    
    logger.info("🛑 Shutting down ANIP API...")


app = FastAPI(
    title="ANIP API",
    description="Automated News Intelligence Pipeline API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS - use pydantic settings for allowed origins
allowed_origins = settings.api.cors_origins.split(",")
if "*" in allowed_origins:
    logger.warning("CORS is configured to allow all origins. This should be restricted in production.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(news_router)
app.include_router(conversations_router)

# Mount static files for UI
ui_static_path = Path(__file__).parent / "ui" / "static"
if ui_static_path.exists():
    app.mount("/static", StaticFiles(directory=str(ui_static_path)), name="static")
    logger.info(f"✅ Mounted static files from {ui_static_path}")
else:
    logger.warning(f"⚠️  UI static directory not found at {ui_static_path}")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    logger.warning(f"Validation error on {request.url}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to ANIP API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "api": "/api",
        "chat": "/chat"
    }


@app.get("/chat", response_class=HTMLResponse)
async def chat_ui():
    """Serve the chat UI."""
    ui_html_path = Path(__file__).parent / "ui" / "static" / "index.html"
    
    if not ui_html_path.exists():
        return HTMLResponse(
            content="<h1>Chat UI not found</h1><p>The UI files are not available.</p>",
            status_code=404
        )
    
    with open(ui_html_path, 'r', encoding='utf-8') as f:
        return HTMLResponse(content=f.read())


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    from anip.shared.database import engine
    
    db_healthy = False
    db_error = None
    
    try:
        # Test database connection using SQLAlchemy text() for safety
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_healthy = True
    except Exception as e:
        db_error = str(e)
        logger.error(f"Database health check failed: {e}")
    
    overall_status = "healthy" if db_healthy else "unhealthy"
    status_code = status.HTTP_200_OK if db_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return JSONResponse(
        status_code=status_code,
        content={
            "status": overall_status,
            "database": "healthy" if db_healthy else f"unhealthy: {db_error}"
        }
    )

