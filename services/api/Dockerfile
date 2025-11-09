FROM python:3.11-slim

WORKDIR /app

# System deps (psycopg2-binary often fine, but add libpq for safety)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir \
    fastapi==0.115.0 uvicorn[standard]==0.30.6 \
    sqlmodel==0.0.21 psycopg2-binary==2.9.9 \
    pydantic==2.9.2 pydantic-core==2.23.4 \
    kafka-python==2.0.2 \
    mlflow==2.16.0
COPY ./app /app



EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
