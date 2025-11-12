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
    psycopg2-binary==2.9.9

EXPOSE 5000
