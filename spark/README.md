# Spark ML Processing

Apache Spark-based batch processing pipeline for applying ML models to news articles.

## Overview

The Spark ML processing pipeline processes news articles in batches, applying machine learning models for topic classification, sentiment analysis, and embedding generation. It's designed to handle large volumes of articles efficiently using distributed processing.

## ml_processing.py

The main Spark job that processes articles with ML models.

### What It Does

1. **Loads Articles from Database**
   - Reads articles from PostgreSQL that need ML processing (where `topic`, `sentiment`, or `embedding` is NULL)
   - Uses SQLAlchemy to connect to the database
   - Creates Spark DataFrame from query results

2. **Applies ML Transformations**
   - **Topic Classification**: Classifies articles into topics (e.g., Technology, Politics, Sports)
   - **Sentiment Analysis**: Analyzes sentiment (positive, neutral, negative) with confidence scores
   - **Embedding Generation**: Generates 384-dimensional embeddings for semantic search

3. **Saves Results Back to Database**
   - Updates existing articles with ML predictions
   - Uses SQLAlchemy for database updates
   - Collects Spark DataFrame results and updates records

### Processing Flow

```
Database (PostgreSQL)
    ↓ (SQLAlchemy query)
Spark DataFrame
    ↓ (Spark UDFs apply ML models)
    ├─ Topic Classification → topic column
    ├─ Sentiment Analysis → sentiment + sentiment_score columns
    └─ Embedding Generation → embedding column
    ↓ (Collect results)
Database Updates (SQLAlchemy)
```

## How Spark Job Submission Works (General)

### Understanding spark-submit

When you run `spark-submit`, it works like this:

1. **Client Side (where spark-submit runs)**:
   - You have the application file (e.g., `ml_processing.py`)
   - You run: `spark-submit --master spark://master:7077 ml_processing.py`

2. **What spark-submit does**:
   - **Reads the file** from the local filesystem
   - **Uploads it** to the Spark cluster (via HTTP/RPC)
   - **Tells Spark Master**: "Execute this application"
   - Spark Master distributes the uploaded code to Workers
   - Workers execute the code

### Code Distribution Methods

Spark supports several ways to get code to workers:

#### Method 1: File Upload (Default)
```
Client Machine                    Spark Cluster
┌─────────────┐                  ┌──────────────┐
│ ml_processing.py               │ Spark Master │
│ (local file)│  ──upload───►   │              │
└─────────────┘                  └──────┬───────┘
                                        │
                                        │ distribute
                                        ↓
                                  ┌──────────────┐
                                  │ Spark Worker │
                                  │ (executes)   │
                                  └──────────────┘
```

**How it works**:
- `spark-submit` uploads the file to Spark Master
- Master stores it temporarily and distributes to Workers
- Workers download and execute it
- **Code doesn't need to exist on Spark cluster beforehand**

#### Method 2: Shared Filesystem
```
Shared Filesystem (NFS, HDFS, S3, Docker Volume)
┌─────────────────────────────────────────┐
│ /shared/spark/ml_processing.py          │
└───────┬───────────────────┬─────────────┘
        │                   │
        │                   │
┌───────▼───────┐   ┌───────▼───────┐
│ Client        │   │ Spark Worker  │
│ (reads file)  │   │ (reads file)  │
└───────────────┘   └───────────────┘
```

**How it works**:
- Both client and Spark workers can access the same file path
- `spark-submit` references the path: `/shared/spark/ml_processing.py`
- Workers read directly from shared location
- **No upload needed** - both access same file

#### Method 3: Package Distribution
```
spark-submit \
  --py-files dependencies.zip \
  --jars lib.jar \
  ml_processing.py
```

**How it works**:
- Dependencies packaged into zip/jar files
- Uploaded separately and cached on workers
- Application code references them

### Key Points

1. **Spark Workers Don't Have Code by Default**
   - Workers are "dumb" executors - they execute what they're given
   - Code is distributed at job submission time
   - Workers don't store application code permanently (unless using shared filesystem)

2. **Where Code Lives**
   - **Client side**: Where `spark-submit` runs (e.g., Airflow container)
   - **During execution**: Uploaded to Spark cluster, distributed to workers
   - **After execution**: Usually cleaned up (unless using shared filesystem)

3. **File Paths in spark-submit**
   - If path is **local** (e.g., `./ml_processing.py`): File is uploaded
   - If path is **shared** (e.g., `hdfs://path` or shared volume): Workers read directly
   - If path is **remote** (e.g., `s3://bucket/file.py`): Workers download it

## How Airflow Calls the Spark Job

The `spark_ml_processing_dag.py` DAG orchestrates the Spark job execution:

### DAG Structure

1. **Check Task** (`check_articles_to_process`)
   - PythonOperator that checks if there are articles needing processing
   - Queries database to count articles with NULL ML fields
   - Returns early if no articles to process

2. **Spark Task** (`spark_ml_processing`)
   - Uses `SparkSubmitOperator` to submit the Spark job
   - Submits `/opt/anip/spark/ml_processing.py` to Spark cluster
   - Configures Spark executor/driver memory and settings

### SparkSubmitOperator Configuration

```python
SparkSubmitOperator(
    task_id='spark_ml_processing',
    application='/opt/anip/spark/ml_processing.py',
    conn_id='spark_default',  # Connection to spark://spark-master:7077
    conf={
        'spark.executor.memory': '2g',
        'spark.driver.memory': '2g',
    },
    env_vars={
        'POSTGRES_HOST': ...,
        'MLFLOW_TRACKING_URI': ...,
        # ... other environment variables
    }
)
```

### How Job Submission Works in This Setup

**In your specific case**:

1. **Airflow Container Has Spark Client Tools**:
   - Java runtime (`openjdk-17-jre-headless`) - required for `spark-submit`
   - PySpark client library (`pyspark==4.0.0`) - provides `spark-submit` command
   - Apache Airflow Spark provider - provides `SparkSubmitOperator`

2. **Shared Volume Setup**:
   - The `./spark` directory is mounted as a Docker volume in both containers:
     - Airflow: `./spark:/opt/anip/spark:ro`
     - Spark Master/Workers: `./spark:/opt/anip/spark:ro`
   - This means the same file path exists in both containers

3. **Job Submission Process**:
   - `SparkSubmitOperator` runs `spark-submit` command **inside the Airflow container**
   - `spark-submit` reads `/opt/anip/spark/ml_processing.py` from the mounted volume
   - **Two possible behaviors** (depends on Spark configuration):
     - **Option A**: File is uploaded to Spark cluster (default behavior)
     - **Option B**: Spark workers read directly from shared volume (if Spark is configured to use shared filesystem)
   
   In practice, Spark typically **uploads the file** even if it's on a shared volume, because:
   - Spark doesn't know the volume is shared
   - It treats the path as "local to client"
   - Workers receive the uploaded file and execute it

### Execution Flow

```
Airflow Scheduler Container
    ↓ (scheduled every hour)
Check Task (PythonOperator)
    ↓ (if articles found)
SparkSubmitOperator
    ↓ (runs spark-submit command INSIDE Airflow container)
    ↓ (reads /opt/anip/spark/ml_processing.py from mounted volume)
    ↓ (uploads file to Spark cluster via HTTP/RPC)
Spark Master Container (spark://spark-master:7077)
    ↓ (receives uploaded file, distributes to workers)
Spark Worker Container(s)
    ↓ (receives file, executes ml_processing.py)
Results saved to database
```

**Key Points**:
- Airflow has Spark **client tools** (Java + PySpark) but NOT a full Spark installation
- The actual Spark runtime and execution happens on Spark Master/Worker containers
- **Code is uploaded** from Airflow to Spark cluster (standard spark-submit behavior)
- Spark workers execute the uploaded code - they don't have the code beforehand
- The shared volume makes the file accessible to Airflow, but Spark still uploads it

## Service Connections

### Airflow → Spark

**Connection Type**: Spark Cluster Connection (Remote Submission)

- **Protocol**: Spark Standalone Cluster
- **Master URL**: `spark://spark-master:7077`
- **Method**: `SparkSubmitOperator` runs `spark-submit` command inside Airflow container, which submits jobs to remote Spark cluster
- **Network**: Both services on `anip-net` Docker network
- **Volumes**: Shared `/opt/anip/spark` directory mounted in both containers (allows Airflow to read the file)

**How It Works**:
1. Airflow scheduler triggers DAG
2. `SparkSubmitOperator` executes `spark-submit` command **inside Airflow container**
3. `spark-submit` reads the application file from `/opt/anip/spark/ml_processing.py` (mounted volume)
4. File is **uploaded** to Spark Master at `spark://spark-master:7077` via HTTP/RPC
5. Spark Master distributes the uploaded file to Workers
6. Workers execute the Python script

**Important**: 
- Airflow has Spark **client tools** (Java + PySpark) but NOT a full Spark installation
- The actual Spark runtime and execution happens on Spark Master/Worker containers
- **Code is uploaded** from Airflow to Spark - Spark workers don't have the code beforehand
- The shared volume allows Airflow to access the file, but Spark still uploads it (standard behavior)

### Spark → Other Services

#### 1. PostgreSQL Database

**Connection**: SQLAlchemy

- **Purpose**: Read articles needing processing, update with ML predictions
- **Connection String**: From environment variables (`POSTGRES_HOST`, `POSTGRES_DB`, etc.)
- **Network**: Both on `anip-net` Docker network
- **Access**: Direct database connection via SQLAlchemy engine

**Usage**:
- Read: Query articles with NULL ML fields
- Write: Update articles with topic, sentiment, embedding columns

#### 2. Model Serving Services

**Connection**: HTTP REST API

- **Classification Service**: `http://model-serving-classification:5001`
- **Sentiment Service**: `http://model-serving-sentiment:5002`
- **Network**: Both on `anip-net` Docker network
- **Protocol**: REST API (`/invocations` endpoint)

**How It Works**:
- Spark UDFs call ML inference functions (`predict_topic`, `predict_sentiment`)
- Inference functions check `USE_MODEL_SERVING` environment variable
- If enabled, makes HTTP POST requests to model serving endpoints
- Falls back to local MLflow model loading if serving unavailable

#### 3. Embedding Service

**Connection**: HTTP REST API

- **URL**: `http://embedding-service:5003`
- **Network**: Both on `anip-net` Docker network
- **Protocol**: REST API (`/embed` or `/embed/batch` endpoint)

**Usage**:
- Spark UDF calls `generate_embedding()` function
- Function makes HTTP request to embedding service
- Returns 384-dimensional embedding vector

#### 4. MLflow Tracking Server

**Connection**: HTTP REST API (optional)

- **URL**: `http://mlflow:5000`
- **Purpose**: Model metadata and registry (if not using model serving)
- **Network**: Both on `anip-net` Docker network

**Usage**:
- Only used if model serving is disabled
- Loads models from MLflow Model Registry
- Accesses model artifacts from shared `/mlruns` volume

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Airflow Scheduler                       │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  spark_ml_processing_dag.py                         │  │
│  │                                                      │  │
│  │  1. Check Task (PythonOperator)                     │  │
│  │     └─ Query PostgreSQL for articles                │  │
│  │                                                      │  │
│  │  2. Spark Task (SparkSubmitOperator)                │  │
│  │     └─ Runs spark-submit (uploads file)             │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬───────────────────────────────────┘
                         │ spark-submit uploads file
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                    Spark Cluster                            │
│                                                             │
│  ┌──────────────┐         ┌──────────────┐                 │
│  │ Spark Master │ ◄────── │ Spark Worker│                 │
│  │  Port 7077   │         │  Port 8081  │                 │
│  │              │         │             │                 │
│  │ Receives     │         │ Executes    │                 │
│  │ uploaded file│         │ ml_processing.py             │
│  └──────┬───────┘         └──────────────┘                 │
│         │                                                   │
│         └──► Distributes uploaded code to workers          │
└────────────────────────┬───────────────────────────────────┘
                         │
                         │ Spark UDFs call ML functions
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              ML Services (via HTTP REST)                    │
│                                                             │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │ Classification   │  │ Sentiment       │               │
│  │ Model Server     │  │ Model Server    │               │
│  │ :5001            │  │ :5002           │               │
│  └──────────────────┘  └──────────────────┘               │
│                                                             │
│  ┌──────────────────┐                                      │
│  │ Embedding        │                                      │
│  │ Service          │                                      │
│  │ :5003            │                                      │
│  └──────────────────┘                                      │
└────────────────────────┬───────────────────────────────────┘
                         │
                         │ SQLAlchemy
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              PostgreSQL Database                             │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  newsarticle table                                   │  │
│  │  - Read: articles with NULL ML fields                │  │
│  │  - Write: Update with topic, sentiment, embedding   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Environment Variables

### Why Spark Workers Need Environment Variables

**Important**: Spark workers **MUST have** the environment variables because:

1. **Code runs on Spark workers** - The Python code (`ml_processing.py`) executes on Spark worker containers, not Airflow
2. **Code reads environment variables** - The code uses:
   - `settings.database.url` → reads `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, etc.
   - `predict_topic()` → reads `USE_MODEL_SERVING`, `CLASSIFICATION_SERVING_URL`
   - `predict_sentiment()` → reads `USE_MODEL_SERVING`, `SENTIMENT_SERVING_URL`
   - `generate_embedding()` → reads `EMBEDDING_SERVICE_URL`

### Two Ways to Set Environment Variables

#### Method 1: Container-Level (docker-compose.yml)

Environment variables set in `docker-compose.yml` are available to **all processes** in the Spark container:

```yaml
spark-worker:
  environment:
    <<: *common-env  # Includes POSTGRES_*, MLFLOW_TRACKING_URI, etc.
    USE_MODEL_SERVING: ${USE_MODEL_SERVING:-true}
    CLASSIFICATION_SERVING_URL: ${CLASSIFICATION_SERVING_URL:-...}
    SENTIMENT_SERVING_URL: ${SENTIMENT_SERVING_URL:-...}
```

**Pros**:
- Available to all Spark jobs automatically
- Set once, works for all jobs
- No need to pass in each SparkSubmitOperator

**Cons**:
- Same values for all jobs (less flexible)
- Requires container restart to change

#### Method 2: Job-Level (SparkSubmitOperator env_vars)

Environment variables passed via `SparkSubmitOperator` are passed **specifically to that Spark job**:

```python
SparkSubmitOperator(
    task_id='spark_ml_processing',
    application='/opt/anip/spark/ml_processing.py',
    env_vars={
        'POSTGRES_HOST': settings.database.host,
        'POSTGRES_PORT': str(settings.database.port),
        'POSTGRES_DB': settings.database.db,
        'POSTGRES_USER': settings.database.user,
        'POSTGRES_PASSWORD': settings.database.password,
        'MLFLOW_TRACKING_URI': settings.mlflow.tracking_uri,
    },
)
```

**Pros**:
- Different values per job (more flexible)
- Can use Airflow variables/settings
- No container restart needed

**Cons**:
- Must be set for each job
- More verbose configuration

### How They Work Together

1. **Container-level env vars** are set when Spark containers start
2. **Job-level env vars** (from `SparkSubmitOperator`) are passed when the job is submitted
3. **Job-level overrides container-level** - If both are set, job-level takes precedence
4. **Spark workers use the final values** when executing the code

### Required Environment Variables

- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`: Database connection
- `MLFLOW_TRACKING_URI`: MLflow server URL (if not using model serving)
- `USE_MODEL_SERVING`: Enable/disable model serving (default: `true`)
- `CLASSIFICATION_SERVING_URL`: Classification model server URL
- `SENTIMENT_SERVING_URL`: Sentiment model server URL
- `EMBEDDING_SERVICE_URL`: Embedding service URL

### In This Setup

**Current configuration uses BOTH methods**:

1. **Container-level** (docker-compose.yml): Sets `USE_MODEL_SERVING`, `CLASSIFICATION_SERVING_URL`, `SENTIMENT_SERVING_URL` on Spark workers
2. **Job-level** (SparkSubmitOperator): Passes `POSTGRES_*` and `MLFLOW_TRACKING_URI` from Airflow settings

This hybrid approach:
- Uses container-level for model serving URLs (consistent across all jobs)
- Uses job-level for database credentials (can vary per job/environment)

## Running Locally

```bash
# Submit job directly to Spark cluster
spark-submit \
  --master spark://spark-master:7077 \
  --executor-memory 2g \
  --driver-memory 2g \
  /opt/anip/spark/ml_processing.py
```

## File Structure

```
spark/
├── ml_processing.py      # Main Spark ML processing job
├── __init__.py          # Package init
└── README.md            # This file
```
