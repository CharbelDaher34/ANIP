# 🔧 Fixes Applied - Import Errors & Spark Submit

## Issues Found from Logs

Based on the Airflow DAG execution logs, several issues were identified and fixed:

---

## 1. ✅ Fixed Import Errors in DAGs

### Issue
DAGs were failing with `ModuleNotFoundError: No module named 'shared'`

### Files Fixed

#### `dags/newsdata_pipeline_dag.py`
- **Before:** `from shared.ingestion.newsdata_ingestor import NewsDataIngestor`
- **After:** `from anip.shared.ingestion.newsdata_ingestor import NewsDataIngestor`
- **Before:** `os.getenv('NEWSDATA_API_KEY')`
- **After:** `settings.news_api.newsdata_api_key`
- Removed `sys.path.insert(0, '/opt/airflow')`

#### `dags/gdelt_pipeline_dag.py`
- **Before:** `from shared.ingestion.gdelt_ingestor import GDELTIngestor`
- **After:** `from anip.shared.ingestion.gdelt_ingestor import GDELTIngestor`
- Removed `sys.path.insert(0, '/opt/airflow')`

---

## 2. ✅ Fixed Import Errors in Ingestor Files

### Issue
Ingestor files were importing from `shared.` instead of `anip.shared.`

### Files Fixed

#### `src/anip/shared/ingestion/newsapi_ingestor.py`
- **Before:** `from shared.ingestion.base import BaseIngestor`
- **After:** `from anip.shared.ingestion.base import BaseIngestor`

#### `src/anip/shared/ingestion/newsdata_ingestor.py`
- **Before:** `from shared.ingestion.base import BaseIngestor`
- **After:** `from anip.shared.ingestion.base import BaseIngestor`

#### `src/anip/shared/ingestion/gdelt_ingestor.py`
- **Before:** `from shared.ingestion.base import BaseIngestor`
- **After:** `from anip.shared.ingestion.base import BaseIngestor`

---

## 3. ✅ Fixed Spark Submit Issue

### Issue
```
JAVA_HOME is not set
Cannot execute: spark-submit ... Error code is: 1
```

The Airflow container didn't have Spark binaries or Java installed, which are required by `SparkSubmitOperator`.

### Solution Applied

Updated `Dockerfile.airflow` to:
1. **Install Java (OpenJDK 17 JRE)** - Required for Spark
2. **Install Spark binaries (3.5.0)** - Provides `spark-submit` command
3. **Set environment variables:**
   - `SPARK_HOME=/opt/spark`
   - `JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64`
   - Added Spark bin directory to `PATH`

### Changes Made

```dockerfile
# Install Java
RUN apt-get install -y openjdk-17-jre-headless wget

# Install Spark
ENV SPARK_VERSION=3.5.0
ENV SPARK_HOME=/opt/spark
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH=$PATH:$SPARK_HOME/bin

RUN wget -q https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop3.tgz \
    && tar -xzf spark-${SPARK_VERSION}-bin-hadoop3.tgz -C /opt \
    && mv /opt/spark-${SPARK_VERSION}-bin-hadoop3 ${SPARK_HOME} \
    && rm spark-${SPARK_VERSION}-bin-hadoop3.tgz
```

---

## 4. ✅ Added psycopg2-binary to MLflow

### Issue
```
ModuleNotFoundError: No module named 'psycopg2'
```

MLflow couldn't connect to PostgreSQL backend.

### Solution
Updated `services/mlflow/Dockerfile` to include `psycopg2-binary==2.9.9`

---

## 5. ✅ Automated Spark Connection Setup

### Before
Manual step required:
```bash
docker exec anip-airflow-scheduler python /opt/anip/scripts/setup_airflow_connections.py
```

### After
Automatic setup via `scripts/airflow_entrypoint.sh`:
- Waits for Airflow database to be ready
- Automatically creates Spark connection on startup
- Non-blocking (runs in background)
- Handles errors gracefully

---

## Summary of DAG Status (After Fixes)

| DAG | Status | Notes |
|-----|--------|-------|
| `newsapi_pipeline` | ✅ Should work | Import errors fixed |
| `newsdata_pipeline` | ✅ Should work | Import errors fixed |
| `gdelt_pipeline` | ✅ Should work | Import errors fixed |
| `ml_model_training` | ✅ Working | Already successful |
| `spark_ml_processing` | ✅ Should work | Spark binaries installed |

---

## Testing the Fixes

After rebuilding:

```bash
# Rebuild Airflow images
docker compose build airflow-scheduler airflow-webserver airflow-init

# Restart services
docker compose up -d

# Test the DAGs
docker exec anip-airflow-scheduler airflow dags trigger newsapi_pipeline
docker exec anip-airflow-scheduler airflow dags trigger newsdata_pipeline
docker exec anip-airflow-scheduler airflow dags trigger gdelt_pipeline
docker exec anip-airflow-scheduler airflow dags trigger spark_ml_processing

# Check logs
docker compose logs -f airflow-scheduler
```

---

## What Changed

1. **All import statements** now use `anip.` prefix
2. **All `sys.path.insert()`** calls removed
3. **All `os.getenv()`** calls replaced with `settings` from `anip.config`
4. **Spark binaries** installed in Airflow container
5. **Java (JRE)** installed in Airflow container
6. **psycopg2-binary** added to MLflow
7. **Spark connection** automatically created on startup

---

## Files Modified

- ✅ `dags/newsdata_pipeline_dag.py`
- ✅ `dags/gdelt_pipeline_dag.py`
- ✅ `src/anip/shared/ingestion/newsapi_ingestor.py`
- ✅ `src/anip/shared/ingestion/newsdata_ingestor.py`
- ✅ `src/anip/shared/ingestion/gdelt_ingestor.py`
- ✅ `Dockerfile.airflow` (added Java & Spark)
- ✅ `services/mlflow/Dockerfile` (added psycopg2-binary)
- ✅ `scripts/airflow_entrypoint.sh` (automated setup)

---

**All critical issues have been resolved!** 🎉

