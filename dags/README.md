# Apache Airflow DAGs

This directory contains Apache Airflow DAGs (Directed Acyclic Graphs) that orchestrate the ANIP news intelligence pipeline. DAGs automate data ingestion, ML model training, and batch processing workflows.

## Overview

The ANIP system uses Airflow to schedule and monitor three types of workflows:

1. **Data Ingestion DAGs** - Fetch news articles from various APIs
2. **ML Training DAG** - Train and retrain classification and sentiment models
3. **Spark ML Processing DAG** - Apply ML models to articles in batch

## DAGs

### Data Ingestion DAGs

These DAGs fetch news articles from different sources and save them to the PostgreSQL database.

#### 1. `newsapi_pipeline`
- **Source**: NewsAPI.org
- **Topic**: Artificial Intelligence (AI)
- **Schedule**: Every 6 hours (4 times/day)
- **Rate Limit**: 100 requests/day (free tier)
- **Description**: Fetches AI-related articles using query search

#### 2. `thenewsapi_pipeline`
- **Source**: TheNewsAPI.com
- **Topic**: Computer Vision
- **Schedule**: Every 6 hours (4 times/day)
- **Rate Limit**: 100 requests/day (free tier, 3 articles per request)
- **Description**: Fetches computer vision articles

#### 3. `worldnewsapi_pipeline`
- **Source**: WorldNewsAPI.com
- **Schedule**: Every 6 hours
- **Rate Limit**: Varies by tier
- **Description**: Fetches world news articles

#### 4. `newsdata_pipeline`
- **Source**: NewsData.io
- **Schedule**: Every 6 hours
- **Rate Limit**: Varies by tier
- **Description**: Fetches news articles

#### 5. `gdelt_pipeline`
- **Source**: GDELT Project
- **Topic**: Deep Learning & Neural Networks
- **Schedule**: Every 12 hours (2 times/day)
- **Rate Limit**: Unlimited (completely free, no API key required)
- **Description**: Fetches deep learning and neural networks articles

#### 6. `mediastack_pipeline`
- **Source**: MediaStack API
- **Schedule**: Every 6 hours
- **Rate Limit**: Varies by tier
- **Description**: Fetches news articles

### ML Training DAG

#### `ml_training_dag`
- **Purpose**: Train and retrain ML models
- **Schedule**: Daily (configurable)
- **Tasks**:
  1. Train classification model (topic classification)
  2. Train sentiment model (sentiment analysis)
  3. Evaluate models
  4. Promote best models to production (MLflow Model Registry)
- **Description**: Orchestrates the complete ML training pipeline, including dataset preparation, training, evaluation, and model promotion

### Spark ML Processing DAG

#### `spark_ml_processing`
- **Purpose**: Apply ML models to articles in batch
- **Schedule**: Every hour
- **Tasks**:
  1. Check if there are articles needing ML processing
  2. Submit Spark job to process articles with:
     - Topic classification
     - Sentiment analysis
     - Embedding generation
- **Description**: Processes articles that don't have ML predictions yet (where `topic`, `sentiment`, or `embedding` is NULL)

## DAG Structure

All DAGs follow a consistent structure:

```python
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

# Default arguments
default_args = {
    'owner': 'anip',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Create DAG
dag = DAG(
    'dag_name',
    default_args=default_args,
    description='DAG description',
    schedule_interval=timedelta(hours=X),
    catchup=False,
    tags=['tag1', 'tag2'],
)

# Define tasks
task = PythonOperator(
    task_id='task_name',
    python_callable=function_name,
    dag=dag,
)
```

## Running DAGs

### Prerequisites

1. **Airflow Setup**: Airflow must be running (via Docker Compose)
2. **Database Connection**: PostgreSQL database must be accessible
3. **Dependencies**: All Python packages must be installed (handled by `Dockerfile.airflow`)
4. **Spark Connection**: For `spark_ml_processing`, Spark cluster must be running

### Accessing Airflow UI

1. Start the services:
   ```bash
   docker-compose up -d airflow-webserver airflow-scheduler
   ```

2. Access the UI:
   - URL: `http://localhost:8080`
   - Default credentials: `airflow` / `airflow`

### Manual Trigger

You can trigger DAGs manually from the Airflow UI:

1. Navigate to the DAGs list
2. Toggle the DAG to enable it
3. Click the "Play" button to trigger a run

### Via CLI

```bash
# Trigger a DAG run
docker-compose exec airflow-webserver airflow dags trigger <dag_id>

# Example: Trigger ML training
docker-compose exec airflow-webserver airflow dags trigger ml_training

# Example: Trigger Spark processing
docker-compose exec airflow-webserver airflow dags trigger spark_ml_processing
```

## DAG Configuration

### Schedule Intervals

- **Ingestion DAGs**: Every 6 hours (to respect API rate limits)
- **ML Training**: Daily (configurable in DAG)
- **Spark Processing**: Every hour (to process new articles quickly)

### Retry Configuration

All DAGs use:
- **Retries**: 1-2 attempts
- **Retry Delay**: 5 minutes
- **Email Notifications**: Disabled (can be enabled in `default_args`)

### Environment Variables

DAGs use settings from `anip.config.settings`:
- Database connection (`POSTGRES_*`)
- MLflow tracking URI (`MLFLOW_TRACKING_URI`)
- Spark connection (`spark_default` connection)

## Dependencies

### Airflow Container

The `Dockerfile.airflow` installs:
- Apache Airflow 2.10.4
- Python dependencies (`[airflow,ml]` extras)
- Java runtime (for Spark submission)
- PostgreSQL client
- PySpark and Spark providers

### Required Connections

DAGs require these Airflow connections:

1. **PostgreSQL** (`postgres_default`)
   - Type: Postgres
   - Host: Database host
   - Schema: Database name
   - Login/Password: Credentials

2. **Spark** (`spark_default`)
   - Type: Spark
   - Host: `spark://spark-master:7077`
   - Port: 7077

### Python Packages

DAGs import from:
- `anip.shared.ingestion.*` - Data ingestion modules
- `anip.shared.utils.db_utils` - Database utilities
- `anip.ml.classification.train` - ML training
- `anip.ml.sentiment.train` - Sentiment training
- `anip.config` - Configuration settings

## Monitoring

### Airflow UI

Monitor DAG runs in the Airflow UI:
- **Graph View**: Visualize task dependencies
- **Tree View**: See historical runs
- **Logs**: View task execution logs
- **Gantt Chart**: Analyze task durations

### Task Logs

View logs for debugging:
1. Click on a task in the Graph/Tree view
2. Click "Log" button
3. View stdout/stderr output

### Common Issues

1. **DAG Not Appearing**:
   - Check `PYTHONPATH` includes `/opt/anip/src`
   - Verify DAG file syntax is correct
   - Check Airflow scheduler logs

2. **Import Errors**:
   - Ensure `anip` package is installed in Airflow container
   - Check `PYTHONPATH` environment variable

3. **Database Connection Errors**:
   - Verify PostgreSQL is running
   - Check connection credentials in Airflow connections
   - Test connection from Airflow container

4. **Spark Job Failures**:
   - Verify Spark cluster is running
   - Check Spark connection configuration
   - Review Spark worker logs

## File Structure

```
dags/
├── README.md                      # This file
├── Dockerfile.airflow            # Airflow container image
├── __init__.py                   # Package init
├── ml_training_dag.py            # ML training workflow
├── spark_ml_processing_dag.py   # Spark ML processing workflow
├── newsapi_pipeline_dag.py       # NewsAPI ingestion
├── thenewsapi_pipeline_dag.py    # TheNewsAPI ingestion
├── worldnewsapi_pipeline_dag.py  # WorldNewsAPI ingestion
├── newsdata_pipeline_dag.py      # NewsData ingestion
├── gdelt_pipeline_dag.py         # GDELT ingestion
└── mediastack_pipeline_dag.py    # MediaStack ingestion
```

## Adding New DAGs

To add a new DAG:

1. Create a new Python file (e.g., `new_source_pipeline_dag.py`)
2. Follow the standard DAG structure
3. Import required modules from `anip.shared.*`
4. Define tasks using `PythonOperator` or other operators
5. Set appropriate schedule interval and tags
6. The DAG will automatically appear in Airflow UI

Example template:

```python
"""
Airflow DAG for [Source Name] data pipeline.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

def ingest_source():
    """Ingest articles from [Source]."""
    from anip.shared.ingestion.source_ingestor import SourceIngestor
    from anip.shared.utils.db_utils import save_articles_batch
    
    ingestor = SourceIngestor()
    articles = ingestor.fetch(...)
    saved = save_articles_batch(articles)
    return saved

default_args = {
    'owner': 'anip',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'source_pipeline',
    default_args=default_args,
    description='Ingest news from [Source]',
    schedule_interval=timedelta(hours=6),
    catchup=False,
    tags=['ingestion', 'source'],
)

ingest_task = PythonOperator(
    task_id='ingest_source',
    python_callable=ingest_source,
    dag=dag,
)
```

## References

- [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- [Airflow DAGs Guide](https://airflow.apache.org/docs/apache-airflow/stable/concepts/dags.html)
- [Airflow Operators](https://airflow.apache.org/docs/apache-airflow/stable/concepts/operators.html)
- [Spark Submit Operator](https://airflow.apache.org/docs/apache-airflow-providers-apache-spark/stable/operators/spark-submit.html)

