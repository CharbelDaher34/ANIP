# MLflow Model Serving

A production-ready model serving infrastructure for deploying MLflow models with hot reload capabilities.

## Overview

This service provides a custom MLflow model server (`model_server.py`) that wraps MLflow models with additional features like hot reloading, health checks, and standardized APIs. It's designed to serve machine learning models in production without container restarts when models are updated.

## Architecture

The service runs **two independent model servers** for different ML tasks:

```
┌─────────────────────────────────────────────────────┐
│                   MLflow Service                     │
│                                                       │
│  ┌──────────────────────┐  ┌──────────────────────┐ │
│  │  Classification      │  │  Sentiment Analysis  │ │
│  │  Model Server        │  │  Model Server        │ │
│  │  Port: 5001          │  │  Port: 5002          │ │
│  │                      │  │                      │ │
│  │  Model: topic-       │  │  Model: sentiment-   │ │
│  │  classification      │  │  analysis            │ │
│  │  Stage: Production   │  │  Stage: Production   │ │
│  └──────────────────────┘  └──────────────────────┘ │
│              │                       │               │
│              └───────────┬───────────┘               │
│                          ↓                           │
│              ┌─────────────────────┐                 │
│              │  MLflow Tracking    │                 │
│              │  Server (Port 5000) │                 │
│              └─────────────────────┘                 │
│                          │                           │
└──────────────────────────┼───────────────────────────┘
                           ↓
                   PostgreSQL Backend
                   + /mlruns artifacts
```

## Model Server Features

### 1. **Hot Reload** 🔄
- Reload models without container restart
- Atomic model swapping with thread-safe locking
- Version tracking and change detection

### 2. **Production Ready** 💪
- Health check endpoints
- Detailed model metadata and info
- Error handling and logging
- MLflow-compatible API

### 3. **Thread Safe** 🔒
- Thread locks for concurrent requests
- Safe model swapping during reload
- No downtime during updates

## Deployment

### Docker Compose Configuration

Both model servers are defined in `docker-compose.yml`:

#### Classification Model Server

```yaml
model-serving-classification:
  build:
    context: ./services/mlflow
  container_name: anip-model-serving-classification
  ports:
    - "5001:5001"
  environment:
    MODEL_URI: "models:/topic-classification/Production"
    MODEL_NAME: "topic-classification"
    HOST: "0.0.0.0"
    PORT: "5001"
    MLFLOW_TRACKING_URI: "http://mlflow:5000"
  command: python /mlflow/model_server.py
  volumes:
    - ./volumes/mlruns:/mlruns
```

**Purpose**: Classifies news articles into topics (e.g., politics, technology, sports, etc.)

#### Sentiment Analysis Model Server

```yaml
model-serving-sentiment:
  build:
    context: ./services/mlflow
  container_name: anip-model-serving-sentiment
  ports:
    - "5002:5002"
  environment:
    MODEL_URI: "models:/sentiment-analysis/Production"
    MODEL_NAME: "sentiment-analysis"
    HOST: "0.0.0.0"
    PORT: "5002"
    MLFLOW_TRACKING_URI: "http://mlflow:5000"
  command: python /mlflow/model_server.py
  volumes:
    - ./volumes/mlruns:/mlruns
```

**Purpose**: Analyzes sentiment of news articles (positive, negative, neutral)

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `MODEL_URI` | MLflow model URI (registry path) | `models:/model-name/Production` |
| `MODEL_NAME` | Human-readable model name | `topic-classification` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `5001` |
| `MLFLOW_TRACKING_URI` | MLflow tracking server URL | `http://mlflow:5000` |

## API Endpoints

All model servers expose the same REST API:

### Health Check
```bash
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "model_name": "topic-classification",
  "model_uri": "models:/topic-classification/Production"
}
```

### Model Info
```bash
GET /info
```

**Response:**
```json
{
  "model_name": "topic-classification",
  "model_uri": "models:/topic-classification/Production",
  "metadata": {
    "model_name": "topic-classification",
    "version": "3",
    "stage": "Production",
    "run_id": "abc123...",
    "status": "READY",
    "loaded_at": "2025-11-14T10:30:00"
  },
  "status": "loaded"
}
```

### Prediction (MLflow-compatible)
```bash
POST /invocations
Content-Type: application/json
```

**Request Format 1: DataFrame Split**
```json
{
  "dataframe_split": {
    "columns": ["text"],
    "data": [["This is a news article about technology"]]
  }
}
```

**Request Format 2: Instances**
```json
{
  "instances": ["This is a news article about technology"]
}
```

**Response:**
```json
{
  "predictions": ["technology"]
}
```

### Hot Reload
```bash
POST /reload
```

**Response:**
```json
{
  "status": "success",
  "message": "Model 'topic-classification' reloaded successfully - version changed!",
  "model_uri": "models:/topic-classification/Production",
  "old_version": "v2",
  "new_version": "v3",
  "version_changed": true
}
```

## Usage Examples

### Starting the Services

```bash
# Start all services (including both model servers)
docker-compose up -d

# Start only classification model server
docker-compose up -d model-serving-classification

# Start only sentiment analysis model server
docker-compose up -d model-serving-sentiment

# Check logs
docker-compose logs -f model-serving-classification
docker-compose logs -f model-serving-sentiment
```

### Making Predictions

#### Classification Model

```bash
# Classify a news article
curl -X POST http://localhost:5001/invocations \
  -H "Content-Type: application/json" \
  -d '{
    "instances": ["Breaking: New AI breakthrough announced at tech conference"]
  }'

# Response: {"predictions": ["technology"]}
```

#### Sentiment Analysis Model

```bash
# Analyze sentiment
curl -X POST http://localhost:5002/invocations \
  -H "Content-Type: application/json" \
  -d '{
    "instances": ["This is wonderful news for the economy!"]
  }'

# Response: {"predictions": ["positive"]}
```

### Python Client Usage

```python
import requests

# Classification
response = requests.post(
    "http://localhost:5001/invocations",
    json={"instances": ["News article text here"]}
)
topic = response.json()["predictions"][0]

# Sentiment Analysis
response = requests.post(
    "http://localhost:5002/invocations",
    json={"instances": ["News article text here"]}
)
sentiment = response.json()["predictions"][0]
```

### Hot Reloading Models

When you train and register a new model version in MLflow:

```bash
# 1. Train and register new model (in your training pipeline)
# 2. Promote to Production stage in MLflow UI
# 3. Reload the model server

# Reload classification model
curl -X POST http://localhost:5001/reload

# Reload sentiment model
curl -X POST http://localhost:5002/reload
```

**No container restart needed!** The new model version is loaded atomically.

## Model Registry Workflow

```
┌─────────────────────────────────────────────────────────┐
│ 1. Train Model                                          │
│    ├─ Run training pipeline                             │
│    └─ Log model to MLflow                               │
│                                                          │
│ 2. Register Model                                       │
│    ├─ Register in Model Registry                        │
│    └─ Create version (e.g., v1, v2, v3)                 │
│                                                          │
│ 3. Promote to Production                                │
│    ├─ Transition version to "Production" stage          │
│    └─ (via MLflow UI or API)                            │
│                                                          │
│ 4. Hot Reload                                           │
│    ├─ POST /reload on model server                      │
│    └─ New model version loaded without downtime         │
└─────────────────────────────────────────────────────────┘
```

## Integration with Application

The model servers are integrated into the ANIP pipeline via environment variables:

```yaml
# In docker-compose.yml services (api, spark-worker, etc.)
environment:
  USE_MODEL_SERVING: "true"
  CLASSIFICATION_SERVING_URL: "http://model-serving-classification:5001"
  SENTIMENT_SERVING_URL: "http://model-serving-sentiment:5002"
```

Application code checks `USE_MODEL_SERVING` and routes predictions to these endpoints instead of loading models locally.

## Benefits

### Before (Embedded Models)
```
❌ Each service loads models (~500MB per model)
❌ High memory usage across containers
❌ Container restart needed for model updates
❌ Inconsistent model versions across services
```

### After (Model Serving)
```
✅ Centralized model serving
✅ Lower total memory footprint
✅ Hot reload without downtime
✅ Single source of truth for model versions
✅ Easy to scale horizontally
```

## Monitoring

### Check Service Health

```bash
# Classification
curl http://localhost:5001/health

# Sentiment
curl http://localhost:5002/health
```

### Check Model Version

```bash
# Classification
curl http://localhost:5001/info | jq '.metadata.version'

# Sentiment
curl http://localhost:5002/info | jq '.metadata.version'
```

### View Logs

```bash
docker-compose logs -f model-serving-classification
docker-compose logs -f model-serving-sentiment
```

## File Structure

```
services/mlflow/
├── Dockerfile           # Container image definition
├── model_server.py      # Custom MLflow model server with hot reload
└── README.md           # This file
```

