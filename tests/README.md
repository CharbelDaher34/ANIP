# Tests

Test files for the ANIP project.

## Test Files

- `test_api.py` - Test the main API endpoints (articles, search, stats)
- `test_embedding_service.py` - Test the embedding microservice
- `test_model_serving.py` - Test MLflow model serving endpoints (classification & sentiment)

## Running Tests

### Prerequisites

Make sure the required services are running:

```bash
# Start all services
docker-compose up -d

# Or start specific services:
docker-compose up -d api                          # For test_api.py
docker-compose up -d embedding-service            # For test_embedding_service.py
docker-compose up -d model-serving-classification model-serving-sentiment  # For test_model_serving.py
```

### Running Individual Tests

```bash
# Test API endpoints
python tests/test_api.py

# Test embedding service
python tests/test_embedding_service.py

# Test model serving
python tests/test_model_serving.py

# Or with uv
uv run python tests/test_api.py
```

### Running All Tests

```bash
# Run all tests sequentially
for test in tests/test_*.py; do python "$test"; done
```

### Using pytest (Optional)

```bash
# Install test dependencies
uv pip install pytest pytest-cov

# Run all tests
pytest tests/

# Run specific test
pytest tests/test_api.py -v
```

## Test Descriptions

### test_api.py

Tests the main ANIP API endpoints:
- ✅ Root and health check endpoints
- ✅ Article retrieval (list, single, pagination)
- ✅ Article filtering (by topic, sentiment, source, API source)
- ✅ Topic statistics
- ✅ Sentiment statistics and distribution
- ✅ Source statistics
- ✅ API source statistics
- ✅ ML processing status
- ✅ Semantic search (similarity search using embeddings)
- ✅ Error handling (validation, 404s, invalid parameters)

**What it tests:**
- All REST API endpoints work correctly
- Filtering and pagination function properly
- Statistics are calculated accurately
- Semantic search returns relevant results sorted by similarity
- Error cases are handled gracefully
- Database integration works end-to-end

**Requirements:**
- API service running (`docker-compose up -d api`)
- Database with some articles (optional, tests will skip if empty)

### test_embedding_service.py

Tests the embedding microservice functionality:
- ✅ Health check endpoint
- ✅ Model info retrieval
- ✅ Single text embedding generation
- ✅ Batch embeddings generation
- ✅ Semantic similarity validation

**What it tests:**
- Service is running and healthy
- Embeddings are 384-dimensional
- Similar texts produce similar embeddings
- Batch processing works correctly

**Requirements:**
- Embedding service running (`docker-compose up -d embedding-service`)

### test_model_serving.py

Tests the MLflow model serving endpoints:
- ✅ Classification model (topic prediction)
- ✅ Sentiment analysis model
- ✅ Health checks
- ✅ Model info retrieval
- ✅ Prediction endpoints

**What it tests:**
- Model servers are healthy and loaded
- Classification returns valid topics
- Sentiment analysis returns scores and labels
- Model metadata is accessible

**Requirements:**
- Model serving containers running
- Models must be trained and promoted to "Production" in MLflow

