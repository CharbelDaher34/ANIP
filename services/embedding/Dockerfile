FROM python:3.11-slim

WORKDIR /app

# Install uv from official image
COPY --from=docker.io/astral/uv:latest /uv /uvx /bin/

# Install dependencies
RUN uv pip install --system \
    fastapi==0.104.1 \
    uvicorn==0.24.0 \
    sentence-transformers>=5.1.2 \
    torch>=2.0.0

# Copy the service code
COPY embedding_service.py /app/

# Expose port
EXPOSE 5003

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5003/health')"

# Run the service
CMD ["uvicorn", "embedding_service:app", "--host", "0.0.0.0", "--port", "5003"]

