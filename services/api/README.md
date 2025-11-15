# ANIP API Service

FastAPI application providing REST API endpoints and chat UI for the ANIP News Intelligence system.

## Structure

```
services/api/
├── app/
│   ├── news/                      # News API routes
│   │   ├── __init__.py           # News router export
│   │   └── routes.py             # Article endpoints
│   ├── conversations/             # Chat/Conversations API routes
│   │   ├── __init__.py           # Conversations router export
│   │   └── routes.py             # Conversation & message endpoints
│   ├── ui/                        # Chat UI (HTML/CSS/JS)
│   │   ├── static/
│   │   │   ├── index.html        # Main UI template
│   │   │   ├── styles.css        # Styles
│   │   │   └── app.js            # JavaScript logic
│   │   ├── README.md             # UI documentation
│   │   └── IMPLEMENTATION.md     # Implementation details
│   ├── main.py                   # FastAPI application entry point
│   └── __init__.py               # App package init
├── Dockerfile                     # Container image definition
└── README.md                      # This file
```

## Overview

The API service provides:
- **News API**: Query articles with ML predictions
- **Conversations API**: Chat interface with AI agent
- **Chat UI**: Web interface at `/chat`
- **Health Check**: Service status monitoring

## Routes

### News Routes (`/api`)

**Module:** `app.news.routes`

#### Endpoints:

- `GET /api/articles` - List articles with filtering
- `GET /api/articles/{id}` - Get single article
- `GET /api/stats/general` - General statistics
- `GET /api/stats/missing-ml` - ML coverage stats
- `GET /api/search/similar` - Semantic search
- `GET /api/chat` - AI agent query (legacy, use conversations API instead)

**Features:**
- Topic filtering (Technology, Business, Politics, etc.)
- Sentiment filtering (positive, negative, neutral)
- Source filtering
- Pagination support
- Semantic similarity search using embeddings
- Integration with AI agent for natural language queries

### Conversations Routes (`/api/conversations`)

**Module:** `app.conversations.routes`

#### Endpoints:

- `GET /api/conversations/` - List all conversations
- `POST /api/conversations/` - Create new conversation
- `GET /api/conversations/{id}` - Get conversation
- `DELETE /api/conversations/{id}` - Delete conversation
- `GET /api/conversations/{id}/messages` - Get messages
- `POST /api/conversations/{id}/messages` - Create message (calls AI agent)

**Features:**
- Persistent conversation history
- AI agent integration for message processing
- Stores complete search results (DuckDuckGo + Database)
- Rich metadata (summary, answer, intent, sources)
- RESTful API design

### UI Routes

**Module:** `app.main`

#### Endpoints:

- `GET /` - API info
- `GET /chat` - Chat UI (serves HTML)
- `GET /health` - Health check
- `GET /static/*` - Static files (CSS, JS)

**UI Features:**
- Modern, responsive design
- Real-time chat interface
- Multi-source search (DuckDuckGo + Database)
- Source display with metadata
- Conversation management

## Configuration

### Environment Variables

Configured via `anip.config.settings`:

```python
# Database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=anip
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# API
CORS_ORIGINS=*  # Comma-separated origins

# AI Agent
OPENAI_API_KEY=your_openai_key

# Embedding Service
EMBEDDING_SERVICE_URL=http://embedding-service:5003
```

### CORS Configuration

CORS is configured in `main.py`:
- Allowed origins from `settings.api.cors_origins`
- Supports credentials
- All HTTP methods enabled
- All headers allowed

## Database Models

### News Models

**Module:** `anip.shared.models.news`

- `NewsArticle`: News articles with ML predictions

### Conversation Models

**Module:** `anip.shared.models.conversation`

- `Conversation`: Chat sessions
- `Message`: User queries and AI responses

Tables are auto-created on startup via SQLAlchemy.

## Running the Service

### Development

```bash
# Start with Docker Compose
docker-compose up -d api

# Access services
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
# Chat: http://localhost:8000/chat
```

### Standalone (for development)

```bash
# Install dependencies
cd services/api
uv pip install -e "../../[api,ml]"

# Run with uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## API Documentation

### Interactive Docs

FastAPI provides interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Example Requests

#### List Articles

```bash
curl "http://localhost:8000/api/articles?limit=5&topic=Technology"
```

#### Semantic Search

```bash
curl "http://localhost:8000/api/search/similar?question=artificial%20intelligence&limit=3"
```

#### Create Conversation

```bash
curl -X POST http://localhost:8000/api/conversations/ \
  -H "Content-Type: application/json" \
  -d '{"title": "My Chat"}'
```

#### Send Message (AI Agent)

```bash
curl -X POST http://localhost:8000/api/conversations/1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "user_query": "Latest AI news",
    "max_results": 5,
    "search_provider": "both"
  }'
```

## Dependencies

### Python Packages

- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `sqlalchemy` - ORM
- `pydantic` - Data validation
- `pydantic-ai` - AI agent framework
- `anip` package with extras: `[api,ml]`

### Services

- PostgreSQL - Database
- Embedding Service - Text embeddings
- MLflow Model Serving - ML predictions
- Spark - Batch processing (indirect)

## Architecture

### Request Flow

```
Client → FastAPI → Router → Business Logic → Database
                          ↓
                    AI Agent (for chat)
                          ↓
                    [DuckDuckGo + Database Search]
```

### Module Organization

- **`app/`**: Main application package
  - **`news/`**: News-related endpoints
  - **`conversations/`**: Chat-related endpoints
  - **`ui/`**: Frontend files
  - **`main.py`**: Application configuration

### Database Connection

Uses centralized database module:
- `anip.shared.database.get_db_session()` - Context manager for sessions
- `anip.shared.database.Base` - SQLAlchemy declarative base
- `anip.shared.database.engine` - Database engine

## Error Handling

### Exception Handlers

Configured in `main.py`:

1. **ValidationError** (422) - Invalid request data
2. **HTTPException** - Explicit API errors
3. **General Exception** (500) - Unexpected errors

### Logging

All routes use Python logging:
```python
import logging
logger = logging.getLogger(__name__)
```

Logs are output to stdout (captured by Docker).

## Health Checks

### Endpoint: `GET /health`

**Response (Healthy):**
```json
{
  "status": "healthy",
  "database": "healthy"
}
```

**Response (Unhealthy):**
```json
{
  "status": "unhealthy",
  "database": "unhealthy: connection error"
}
```

## Development Guidelines

### Adding New Routes

1. Create a new folder in `app/` (e.g., `app/analytics/`)
2. Add `__init__.py` and `routes.py`
3. Define router with `APIRouter()`
4. Import and include in `main.py`:
   ```python
   from app.analytics import router as analytics_router
   app.include_router(analytics_router)
   ```

### Route Best Practices

- Use Pydantic models for request/response
- Add proper HTTP status codes
- Include comprehensive docstrings
- Log important operations
- Handle exceptions gracefully
- Return consistent error formats

### Testing

```bash
# Test endpoints
curl http://localhost:8000/health

# Test with pytest (if tests exist)
pytest services/api/tests/
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker logs anip-api

# Verify database connection
docker exec anip-api python -c "from anip.shared.database import engine; engine.connect()"
```

### Import Errors

Ensure the API container has access to the `anip` package:
```bash
# Check if package is installed
docker exec anip-api python -c "import anip; print(anip.__file__)"
```

### UI Not Loading

```bash
# Check static files path
ls services/api/app/ui/static/

# Verify in logs
docker logs anip-api | grep "Mounted static files"
```

### Database Tables Missing

Tables are created automatically on startup. Check logs:
```bash
docker logs anip-api | grep "Creating database tables"
```

## Security

### Authentication

Currently **no authentication** is implemented. Consider adding:
- JWT tokens for API
- Session management for UI
- Role-based access control

### Input Validation

All inputs validated via Pydantic models.

### CORS

Configured to allow specified origins. In production, restrict to specific domains.

### SQL Injection

Protected by SQLAlchemy ORM and parameterized queries.

## Performance

### Async Operations

FastAPI uses async/await for concurrent request handling.

### Database Optimization

- Connection pooling via SQLAlchemy
- Context managers for session lifecycle
- Indexes on foreign keys

### Caching

Consider adding:
- Redis for API response caching
- Embedding caching for repeated queries

## Monitoring

### Metrics

Consider adding:
- Prometheus metrics
- Request/response times
- Error rates
- AI agent usage

### Logging

All routes log:
- Info: Successful operations
- Warning: Validation errors
- Error: Exceptions with stack traces

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/orm/)
- [Pydantic AI](https://ai.pydantic.dev/)
- [ANIP Main README](../../README.md)


