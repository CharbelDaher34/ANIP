# ANIP - Automated News Intelligence Pipeline

An end-to-end automated pipeline for collecting, processing, and analyzing news articles with machine learning.

**What it does:**
- 📰 Collects news from multiple sources (NewsAPI, NewsData.io, GDELT)
- 🤖 Processes with ML models (topic classification, sentiment analysis, embeddings)
- 💾 Stores in PostgreSQL with vector search (pgvector)
- 🔄 Orchestrates with Apache Airflow
- 🚀 Serves via REST API
- 🧠 **AI Agent** for intelligent news search and analysis

---

## Table of Contents

- [Infrastructure](#infrastructure)
- [How It Works](#how-it-works)
- [Quick Start](#quick-start)
- [API Endpoints](#api-endpoints)
- [Development](#development)

---

## Infrastructure

### Docker Services

| Service | Container | Purpose | Port |
|---------|-----------|---------|------|
| **PostgreSQL** | `anip-postgres` | Stores articles and ML predictions | 5432 |
| **Airflow Scheduler** | `anip-airflow-scheduler` | Runs and schedules DAGs | - |
| **Airflow Webserver** | `anip-airflow-webserver` | Web UI for monitoring | 8080 |
| **Spark Master** | `spark-master` | Coordinates ML processing | 9090 |
| **Spark Worker** | `spark-worker` | Executes transformations | 9091 |
| **MLflow** | `anip-mlflow` | Model registry and tracking | 5000 |
| **Model Serving (Classification)** | `anip-model-serving-classification` | Topic classification API | 5001 |
| **Model Serving (Sentiment)** | `anip-model-serving-sentiment` | Sentiment analysis API | 5002 |
| **Embedding Service** | `anip-embedding-service` | Text embedding generation | 5003 |
| **FastAPI** | `anip-api` | REST API + AI Agent | 8000 |

All services communicate via the `anip-net` Docker network.

---

## How It Works

### 1. Data Ingestion (Airflow DAGs)

Three DAGs fetch news articles and save them to PostgreSQL:

**NewsAPI Pipeline** (`newsapi_pipeline.py`)
- Fetches from NewsAPI.org
- Topics: Technology, Business, Science
- Schedule: Every 6 hours

**NewsData Pipeline** (`newsdata_pipeline.py`)
- Fetches from NewsData.io
- Coverage: Global news, multiple languages
- Schedule: Every 6 hours

**GDELT Pipeline** (`gdelt_pipeline.py`)
- Queries GDELT Project
- Real-time global events
- Schedule: Every 12 hours

Articles are saved without ML predictions initially (`topic`, `sentiment`, `embedding` are `NULL`).

### 2. ML Processing (Spark Job)

**Trigger**: `spark_ml_processing` DAG (manual or scheduled)

**Process**:
1. Check for articles missing ML predictions
2. Load articles from PostgreSQL
3. Apply ML models in parallel:
   - **Topic Classification**: Categorizes into Business, Technology, Sports, Politics, Health, Science, Entertainment, World
   - **Sentiment Analysis**: Positive/Neutral/Negative + confidence score
   - **Embeddings**: 384-dimensional vectors for similarity search
4. Update articles in database (no duplicates created)

**Models Location**: `ml/classification.py`, `ml/sentiment.py`, `ml/embedding.py`

**Features**:
- Distributed processing with Spark
- Update-only (never creates duplicates)
- Null-safe (only updates fields with valid predictions)
- Processes 1000+ articles in 5-10 minutes

### 3. API Layer (FastAPI)

REST API for querying processed articles + AI-powered news search.

**Location**: `services/api/app/`

**Features**:
- Query articles by topic, sentiment, source
- Semantic search using embeddings
- Statistics and analytics endpoints
- **AI Agent** (`/api/chat`) - Intelligent news assistant
  - DuckDuckGo search integration
  - Semantic database search
  - Multi-source result aggregation

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- 8GB+ RAM recommended
- API keys (see below)

### Setup

```bash
# Clone repository
git clone https://github.com/CharbelDaher34/ANIP.git
cd ANIP

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start all services
docker-compose up -d
```

Wait 2-3 minutes for initialization.

### Access Services

- **Airflow UI**: http://localhost:8080 (admin/admin)
- **Spark UI**: http://localhost:9090
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Run Pipeline

**Via Airflow UI:**
1. Go to http://localhost:8080
2. Login with admin/admin
3. Enable and trigger DAGs: `newsapi_pipeline`, `newsdata_pipeline`, `gdelt_pipeline`
4. After ingestion completes, trigger `spark_ml_processing`

**Via Command Line:**
```bash
# Ingest articles
docker exec anip-airflow-scheduler airflow dags trigger newsapi_pipeline
docker exec anip-airflow-scheduler airflow dags trigger newsdata_pipeline
docker exec anip-airflow-scheduler airflow dags trigger gdelt_pipeline

# Process with ML (wait 2-3 min after ingestion)
docker exec anip-airflow-scheduler airflow dags trigger spark_ml_processing
```

### Query Results

```bash
# Use AI Agent (New!)
curl "http://localhost:8000/api/chat?query=latest%20AI%20news&max_results=5"

# Get articles
curl http://localhost:8000/api/articles?limit=5

# Semantic search
curl "http://localhost:8000/api/search/similar?question=artificial%20intelligence&limit=3"

# Get statistics
curl http://localhost:8000/api/stats/general

# Filter by topic and sentiment
curl "http://localhost:8000/api/articles?topic=Technology&sentiment=positive"
```

---

## API Endpoints

### AI Chat Agent (New!)
```http
GET /api/chat?query=artificial%20intelligence%20news&max_results=5&search_provider=both
```

**Parameters:**
- `query` (required): Your question or search query
- `max_results` (optional): Maximum results per source (default: 5)
- `search_provider` (optional): `both`, `duckduckgo`, or `database` (default: both)

**Response:**
```json
{
  "summary": "AI-generated summary of all findings...",
  "answer": "Detailed answer to your question...",
  "duckduckgo_results": [...],
  "database_results": [...],
  "sources_used": ["DuckDuckGo", "Internal Database"],
  "query_intent": "Breaking news search",
  "total_results": 8,
  "duckduckgo_count": 5,
  "database_count": 3
}
```

**Example:**
```bash
curl "http://localhost:8000/api/chat?query=latest%20AI%20breakthroughs&max_results=3"
```

### List Articles
```http
GET /api/articles?limit=10&offset=0&topic=Technology&sentiment=positive&source=newsapi
```

**Response:**
```json
[
  {
    "id": 123,
    "title": "AI Breakthrough in Healthcare",
    "content": "...",
    "source": "newsapi",
    "url": "https://...",
    "published_at": "2025-11-10T12:00:00",
    "topic": "Technology",
    "sentiment": "positive",
    "sentiment_score": 0.89,
    "created_at": "2025-11-10T12:15:00"
  }
]
```

### Get Single Article
```http
GET /api/articles/{id}
```

### General Statistics
```http
GET /api/stats/general
```

**Response:**
```json
{
  "total_articles": 1250,
  "articles_by_topic": {
    "Technology": 320,
    "Business": 280,
    "Politics": 220
  },
  "articles_by_sentiment": {
    "positive": 450,
    "neutral": 520,
    "negative": 280
  }
}
```

### ML Coverage Statistics
```http
GET /api/stats/missing-ml
```

Shows articles with incomplete ML predictions.

### Semantic Search
```http
GET /api/search/similar?question=climate%20change&limit=5
```

**Parameters:**
- `question` (required): Natural language query
- `limit` (optional): Number of results (default: 5)
- `threshold` (optional): Similarity threshold 0.0-1.0 (default: 0.5)

Returns articles ranked by semantic similarity using embeddings.

### Health Check
```http
GET /health
```

---

## Project Structure

```
anip/
├── dags/                           # Airflow DAG definitions
│   ├── newsapi_pipeline.py
│   ├── newsdata_pipeline.py
│   ├── gdelt_pipeline.py
│   ├── spark_ml_processing_dag.py
│   └── Dockerfile.airflow
├── spark/                          # Spark ML jobs
│   ├── ml_processing.py
│   └── Dockerfile
├── src/anip/                       # Main Python package
│   ├── agent/                      # AI Agent (NEW!)
│   │   ├── news_agent.py           # Pydantic AI news agent
│   │   └── __init__.py
│   ├── ml/                         # ML models
│   │   ├── classification.py
│   │   ├── sentiment.py
│   │   └── embedding.py
│   ├── shared/                     # Shared modules
│   │   ├── database.py
│   │   ├── models/news.py
│   │   ├── ingestion/              # News ingestors
│   │   └── utils/db_utils.py
├── services/
│   ├── api/                        # FastAPI service
│   │   └── app/
│   │       ├── main.py
│   │       └── routes.py
│   ├── mlflow/                     # MLflow model serving
│   │   ├── model_server.py
│   │   └── Dockerfile
│   └── embedding/                  # Embedding microservice
│       ├── embedding_service.py
│       └── Dockerfile
├── tests/                          # Test files
│   ├── test_api.py
│   ├── test_embedding_service.py
│   └── test_model_serving.py
├── docker-compose.yml
├── pyproject.toml
└── .env
```

---

## Environment Variables

Create `.env` file:

```bash
# News API Keys (Required)
NEWSAPI_KEY=your_newsapi_key_here
NEWSDATA_API_KEY=your_newsdata_key_here
GDELT_PROJECT_ID=                         # Optional

# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=anip
POSTGRES_PORT=5432

# Airflow
AIRFLOW_DB_USER=airflow
AIRFLOW_DB_PASSWORD=airflow
AIRFLOW_DB=airflow
AIRFLOW_ADMIN_USER=admin
AIRFLOW_ADMIN_PASSWORD=admin
AIRFLOW_UID=50000

# API
CORS_ORIGINS=*

# OpenAI (for AI Agent)
OPENAI_API_KEY=your_openai_api_key

# Embedding Service
EMBEDDING_SERVICE_URL=http://embedding-service:5003

# GitHub (for code push)
GITHUB_TOKEN=your_github_token
```

**Get API Keys:**
- **NewsAPI**: https://newsapi.org
- **NewsData**: https://newsdata.io
- **GDELT**: No key needed (public)
- **OpenAI**: https://platform.openai.com (for AI Agent)

---

## Development

### Add Dependencies
```bash
uv add <package-name>
```

### Database Access
```bash
# Connect to PostgreSQL
docker exec -it anip-postgres psql -U postgres -d anip

# Run queries
SELECT COUNT(*) FROM newsarticle;
SELECT topic, COUNT(*) FROM newsarticle GROUP BY topic;
```

### View Logs
```bash
docker logs anip-airflow-scheduler -f
docker logs spark-master -f
docker logs anip-api -f
docker-compose logs -f
```

### Rebuild Services
```bash
# Specific service
docker-compose build api
docker-compose up -d api

# All services
docker-compose build
docker-compose up -d
```

### Reset Database
```bash
# API recreates tables on startup
docker-compose restart api
```

---

## Troubleshooting

**Port in use**: Change port in `docker-compose.yml`

**Out of memory**: Increase Docker memory limit in settings

**Invalid API keys**: Check `.env` file

**Database connection failed**:
```bash
docker-compose restart postgres
docker-compose restart api airflow-scheduler
```

**DAG not appearing**: Restart scheduler and wait 1 minute

---

## Performance

- **Ingestion**: ~100 articles per run
- **ML Processing**: ~1000 articles in 5-10 minutes
- **Database**: Tested with 10,000+ articles
- **API**: ~100 requests/second

---

## License

MIT License - see LICENSE file.

---

**Built with Apache Spark, Airflow, PostgreSQL, and FastAPI**
