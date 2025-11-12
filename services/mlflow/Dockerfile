FROM python:3.11-slim

WORKDIR /mlflow

# Install system dependencies (curl for health checks)
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install PostgreSQL client library for MLflow backend
RUN pip install --no-cache-dir \
    mlflow==2.16.0 \
    psycopg2-binary==2.9.9 \
    fastapi==0.104.1 \
    uvicorn==0.24.0 \
    pandas==2.1.4

# Copy model server script
COPY model_server.py /mlflow/model_server.py

EXPOSE 5000
