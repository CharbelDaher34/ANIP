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

## File Structure

```
spark/
├── ml_processing.py      # Main Spark ML processing job
├── __init__.py          # Package init
└── README.md            # This file
```
