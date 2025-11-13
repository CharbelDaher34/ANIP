# Embedding Microservice

A dedicated microservice for generating text embeddings using sentence-transformers.

## Features

- 🚀 **Fast**: Model loaded once, reused for all requests
- 📦 **Isolated**: sentence-transformers only installed here (saves ~2GB across other containers)
- 🔄 **Batch Support**: Process multiple texts efficiently
- 💪 **Production Ready**: Health checks, error handling, logging
- 🎯 **Simple API**: REST endpoints for easy integration

## Model

- **Model**: `all-MiniLM-L6-v2`
- **Dimension**: 384
- **Use Case**: General-purpose semantic similarity
- **Performance**: Fast inference, good quality

## API Endpoints

### Health Check
```bash
GET /health
```

Response:
```json
{
  "status": "healthy",
  "model": "all-MiniLM-L6-v2",
  "dimension": 384
}
```

### Single Embedding
```bash
POST /embed
Content-Type: application/json

{
  "text": "Your text here",
  "normalize": true
}
```

Response:
```json
{
  "embedding": [0.123, -0.456, ...],
  "dimension": 384,
  "model": "all-MiniLM-L6-v2"
}
```

### Batch Embeddings (Recommended for multiple texts)
```bash
POST /embed/batch
Content-Type: application/json

{
  "texts": ["Text 1", "Text 2", "Text 3"],
  "normalize": true
}
```

Response:
```json
{
  "embeddings": [[0.123, ...], [0.456, ...], [0.789, ...]],
  "dimension": 384,
  "count": 3,
  "model": "all-MiniLM-L6-v2"
}
```

### Model Info
```bash
GET /info
```

Response:
```json
{
  "model_name": "all-MiniLM-L6-v2",
  "dimension": 384,
  "max_seq_length": 256,
  "status": "ready"
}
```

## Usage

### Docker Compose
```bash
# Start the service
docker-compose up -d embedding-service

# Check logs
docker-compose logs -f embedding-service

# Test the service
python services/embedding/test_embedding_service.py
```

### Standalone Docker
```bash
# Build
docker build -t anip-embedding-service services/embedding/

# Run
docker run -p 5003:5003 anip-embedding-service
```

## Configuration

Environment variables:
- `EMBEDDING_SERVICE_URL`: URL of the service (default: `http://embedding-service:5003`)

## Client Usage

In your Python code:
```python
from anip.ml.embedding import generate_embedding, generate_embeddings_batch

# Single text
embedding = generate_embedding("Machine learning is amazing")

# Multiple texts (more efficient)
embeddings = generate_embeddings_batch([
    "Text 1",
    "Text 2",
    "Text 3"
])
```

## Architecture Benefits

### Before (Embedded Models)
```
API Container (2GB) + Spark Worker 1 (2GB) + Spark Worker 2 (2GB) = 6GB total
- Each container downloads sentence-transformers
- Slower build times
- More memory usage
```

### After (Microservice)
```
Embedding Service (2GB) + API (100MB) + Spark Worker 1 (100MB) + Spark Worker 2 (100MB) = 2.3GB total
- Model loaded once
- Faster builds
- Less memory usage
- Easy to scale independently
```

## Performance

- **Single request**: ~10-50ms per text
- **Batch request**: ~5-10ms per text (much faster!)
- **Concurrent requests**: Handles multiple requests in parallel

## Troubleshooting

### Service not responding
```bash
# Check if container is running
docker ps | grep embedding

# Check logs
docker-compose logs embedding-service

# Restart
docker-compose restart embedding-service
```

### Connection refused
- Make sure the service is running: `docker-compose ps embedding-service`
- Check the port is exposed: `netstat -tulpn | grep 5003`
- Verify network: containers must be on the same Docker network

### Slow first request
- The model is loaded on first request (takes ~5-10 seconds)
- Subsequent requests are fast
- Consider adding a startup warmup request

