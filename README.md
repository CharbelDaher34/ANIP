# ANIP - Automated News Intelligence Pipeline

An automated pipeline for collecting, processing, and analyzing news articles using Apache Spark, Airflow, and PostgreSQL.

## Architecture

- **Data Ingestion**: Airflow DAGs pull news from NewsAPI, NewsData.io, and GDELT
- **ML Processing**: Apache Spark performs topic classification, sentiment analysis, and embedding generation
- **Storage**: PostgreSQL database stores articles and ML predictions
- **Orchestration**: Airflow manages the entire pipeline workflow

## Quick Start

1. **Environment Setup**:
```bash
cp .env.example .env
# Edit .env with your API keys
```

2. **Start Services**:
```bash
docker-compose up -d
```

3. **Access Services**:
- Airflow UI: http://localhost:8080 (admin/admin)
- Spark Master UI: http://localhost:9090
- API: http://localhost:8000

## Project Structure

```
anip/
├── dags/                  # Airflow DAG definitions
├── spark/                 # Spark ML processing scripts
├── shared/                # Shared Python modules
│   ├── database.py        # Database connection
│   ├── models/            # SQLAlchemy models
│   ├── ingestion/         # News source ingestors
│   └── utils/             # Utility functions
├── scripts/               # Helper scripts
├── services/              # Microservices
│   ├── api/               # FastAPI service
│   └── mlflow/            # MLflow tracking
└── volumes/               # Persistent data
```

## Running the Pipeline

### 1. Ingest Data
```bash
# Via Airflow UI - trigger DAGs manually
# Or via Airflow CLI:
docker-compose exec airflow-webserver airflow dags trigger newsapi_pipeline
```

### 2. Run ML Processing
```bash
docker-compose exec spark-master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  /opt/anip/spark/ml_processing.py
```

### 3. Test Spark Job
```bash
# Nullify some topics first
docker-compose exec -T airflow-webserver python /opt/airflow/scripts/test_spark_null_topics.py

# Run Spark job to re-process
docker-compose exec spark-master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  /opt/anip/spark/ml_processing.py
```

## Environment Variables

Required variables in `.env`:
- `NEWSAPI_KEY`: NewsAPI.org API key
- `NEWSDATA_KEY`: NewsData.io API key
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`: Database credentials

## Development

### Install Dependencies
```bash
uv add <package-name>
```

### Run Tests
```bash
uv run pytest tests/
```

## License

See LICENSE file for details.

