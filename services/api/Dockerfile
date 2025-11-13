FROM python:3.11-slim

WORKDIR /opt/anip

# Install uv from official image
COPY --from=docker.io/astral/uv:latest /uv /uvx /bin/

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy package files first (for better caching)
COPY pyproject.toml setup.py ./
COPY src/ ./src/

# Install anip package with API extras using uv
RUN uv pip install --system -e ".[api]"

# Copy application code
COPY services/api/app /opt/anip/services/api/app

# Set PYTHONPATH
ENV PYTHONPATH="/opt/anip:${PYTHONPATH}"

# Expose port
EXPOSE 8000

WORKDIR /opt/anip/services/api

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

