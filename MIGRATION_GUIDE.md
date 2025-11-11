# ANIP Infrastructure Migration Guide

## Summary of Changes

This document outlines the major infrastructure improvements made to the ANIP project.

---

## 1. ✅ Package Structure (Path Management Fixed)

### Before
```
anip/
├── shared/          # No package structure
├── ml/              # Absolute imports broken
└── dags/            # sys.path.insert everywhere
```

### After
```
anip/
├── src/anip/        # Proper Python package
│   ├── __init__.py
│   ├── config.py    # Centralized config
│   ├── shared/      # Database & models
│   └── ml/          # ML models
├── pyproject.toml   # Modern packaging
└── setup.py         # Backward compatibility
```

**Benefits:**
- ✅ No more `sys.path.insert(0, ...)` hacks
- ✅ Consistent imports: `from anip.shared.database import Base`
- ✅ Works in development and production
- ✅ Testable and maintainable

---

## 2. ✅ Pydantic Settings (Configuration Management)

### Before
```python
# Scattered os.getenv() calls everywhere
postgres_user = os.getenv("POSTGRES_USER")
postgres_password = os.getenv("POSTGRES_PASSWORD")
mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
```

### After
```python
# Centralized configuration with validation
from anip.config import settings

db_url = settings.database.url
mlflow_uri = settings.mlflow.tracking_uri
api_key = settings.news_api.newsapi_key
```

**Benefits:**
- ✅ Type-safe configuration
- ✅ Automatic validation
- ✅ Single source of truth
- ✅ Easy to test with different configs

---

## 3. ✅ Docker Volume Mounts (Standardized)

### Before
```yaml
# Inconsistent mounts across services
airflow:
  volumes:
    - ./shared:/opt/airflow/shared
    - ./ml:/opt/anip/ml

spark:
  volumes:
    - ./shared:/opt/anip/shared
    - ./ml:/opt/anip/ml

api:
  volumes:
    - ./shared:/shared  # Different path!
```

### After
```yaml
# Standard mounts using YAML anchors
x-anip-volumes: &anip-volumes
  - ./src/anip:/opt/anip/src/anip:ro
  - ./volumes/mlruns:/mlruns

services:
  airflow-scheduler:
    volumes:
      <<: *anip-volumes
      - ./dags:/opt/airflow/dags:ro
  
  spark-master:
    volumes:
      <<: *anip-volumes
      - ./spark:/opt/anip/spark:ro
```

**Benefits:**
- ✅ Consistent paths across all containers
- ✅ Read-only mounts for safety
- ✅ DRY principle (Don't Repeat Yourself)
- ✅ Easy to maintain

---

## 4. ✅ Service Communication (Fixed)

### Before
```python
# ❌ BAD: Docker exec from Airflow to Spark
spark_task = BashOperator(
    bash_command='docker exec spark-master spark-submit...'
)

# Required mounting Docker socket (security risk)
volumes:
  - /var/run/docker.sock:/var/run/docker.sock
```

### After
```python
# ✅ GOOD: Use SparkSubmitOperator
spark_task = SparkSubmitOperator(
    application='/opt/anip/spark/ml_processing.py',
    conn_id='spark_default',
    conf={'spark.executor.memory': '2g'},
)

# No Docker socket needed!
```

**Benefits:**
- ✅ No Docker-in-Docker security risks
- ✅ Proper Airflow-Spark integration
- ✅ Better error handling
- ✅ Can run as non-root user

---

## 5. ✅ ML Model Management (Thread-Safe)

### Before
```python
# Global singleton (not thread-safe)
_model = None
_mlflow_tracking_uri = os.getenv("MLFLOW_TRACKING_URI")

def get_model():
    global _model
    if _model is None:
        _model = mlflow.pyfunc.load_model(...)
    return _model
```

### After
```python
# Thread-safe model manager
class ModelManager:
    def __init__(self):
        self._model = None
        self._lock = threading.Lock()
    
    def get_model(self):
        if self._model is None:
            with self._lock:
                if self._model is None:  # Double-check locking
                    self._model = self._load_model()
        return self._model

_manager = ModelManager()
```

**Benefits:**
- ✅ Thread-safe for Spark workers
- ✅ Double-check locking pattern
- ✅ Prevents race conditions
- ✅ Production-ready

---

## 6. ✅ MLflow with PostgreSQL Backend

### Before
```yaml
mlflow:
  command: >
    mlflow server
    --backend-store-uri sqlite:////mlflow/mlflow.db  # ❌ SQLite
```

### After
```yaml
mlflow:
  command: >
    mlflow server
    --backend-store-uri postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
```

**Benefits:**
- ✅ Production-ready database
- ✅ ACID transactions
- ✅ Better concurrency
- ✅ Supports multiple users

---

## 7. ✅ Environment Variables (YAML Anchors)

### Before
```yaml
# Duplicated across 6 services
airflow-scheduler:
  environment:
    POSTGRES_HOST: postgres
    POSTGRES_PORT: "5432"
    POSTGRES_DB: ${POSTGRES_DB:-anip}
    # ... repeated everywhere
```

### After
```yaml
x-common-env: &common-env
  POSTGRES_HOST: postgres
  POSTGRES_PORT: "5432"
  POSTGRES_DB: ${POSTGRES_DB:-anip}
  MLFLOW_TRACKING_URI: "http://mlflow:5000"

services:
  airflow-scheduler:
    environment:
      <<: *common-env
```

**Benefits:**
- ✅ Single source of truth
- ✅ Easy to update
- ✅ No inconsistencies
- ✅ DRY principle

---

## 8. ✅ Dockerfiles (Package Installation)

### Before
```dockerfile
# Hardcoded dependencies
RUN pip install --no-cache-dir \
    psycopg2-binary==2.9.9 \
    sqlalchemy==1.4.52 \
    ...  # 15+ packages hardcoded

ENV PYTHONPATH="${PYTHONPATH}:/opt/airflow:/opt/anip"
```

### After
```dockerfile
# Install anip as package
COPY pyproject.toml setup.py /opt/anip/
COPY src/ /opt/anip/src/

RUN pip install --no-cache-dir -e ".[airflow,ml]"

# No PYTHONPATH manipulation needed!
```

**Benefits:**
- ✅ Dependencies managed in pyproject.toml
- ✅ Service-specific extras
- ✅ Proper package installation
- ✅ No path hacks

---

## Migration Steps

### 1. Rebuild All Images

```bash
cd /storage/hussein/anip

# Stop existing containers
docker-compose down

# Rebuild all images
docker-compose build --no-cache

# Start services
docker-compose up -d
```

### 2. Setup Airflow Spark Connection

```bash
# After Airflow is initialized, run:
docker exec anip-airflow-scheduler python /opt/anip/scripts/setup_airflow_connections.py
```

### 3. Verify Services

```bash
# Check all services are running
docker-compose ps

# Check Airflow
curl http://localhost:8080/health

# Check API
curl http://localhost:8000/health

# Check MLflow
curl http://localhost:5000/health

# Check Spark Master
curl http://localhost:8080
```

### 4. Test the Pipeline

```bash
# Trigger ingestion DAG
docker exec anip-airflow-scheduler airflow dags trigger newsapi_pipeline

# Wait a few minutes, then trigger ML processing
docker exec anip-airflow-scheduler airflow dags trigger spark_ml_processing

# Check results via API
curl http://localhost:8000/api/articles?limit=5
```

---

## Breaking Changes

### Import Paths
- **Old:** `from shared.database import Base`
- **New:** `from anip.shared.database import Base`

### Configuration
- **Old:** `os.getenv("POSTGRES_USER")`
- **New:** `settings.database.user`

### File Locations
- **Old:** `shared/`, `ml/` at project root
- **New:** `src/anip/shared/`, `src/anip/ml/`

---

## Rollback Plan

If issues arise:

```bash
# Rollback to previous version
git checkout <previous-commit>
docker-compose down
docker-compose build
docker-compose up -d
```

---

## Key Improvements Summary

| Issue | Before | After |
|-------|--------|-------|
| **Path Management** | sys.path hacks | Proper package |
| **Configuration** | Scattered os.getenv | Pydantic Settings |
| **Volume Mounts** | Inconsistent paths | Standardized with anchors |
| **Service Communication** | Docker exec | SparkSubmitOperator |
| **ML Models** | Not thread-safe | Thread-safe manager |
| **MLflow Backend** | SQLite | PostgreSQL |
| **Environment Variables** | Duplicated 6x | YAML anchors |
| **Dockerfiles** | Hardcoded deps | Package installation |

---

## Support

For issues or questions, refer to:
- [Main README](README.md)
- [Pydantic Settings Docs](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [Airflow Spark Provider](https://airflow.apache.org/docs/apache-airflow-providers-apache-spark/)

