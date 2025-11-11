# Python Version Mismatch Fix

## 🐛 Problem

The Spark job failed with:

```
PySparkRuntimeError: [PYTHON_VERSION_MISMATCH] 
Python in worker has different version: 3.10 than that in driver: 3.12
PySpark cannot run with different minor versions.
```

### Version Mismatch

- **Airflow (Driver):** Python 3.12 (`apache/airflow:2.9.3` base image)
- **Spark (Worker):** Python 3.10 (`apache/spark:4.0.0` base image)

### Why This Fails

PySpark requires **exact minor version match** between:
- **Driver:** Where `spark-submit` runs (Airflow container)
- **Workers:** Where Spark executors run (Spark worker containers)

The Python interpreter serialization format changes between minor versions, causing incompatibility.

---

## ✅ Solution

### Updated `Dockerfile.spark`

```dockerfile
FROM apache/spark:4.0.0

USER root

# Install Python 3.12 to match Airflow
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y --no-install-recommends \
    python3.12 \
    python3.12-distutils \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3.12 as default
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1 \
    && update-alternatives --set python3 /usr/bin/python3.12

# Copy package files
COPY pyproject.toml setup.py /opt/anip/
COPY src/ /opt/anip/src/

# Install anip package with ML extras
WORKDIR /opt/anip
RUN pip3 install --no-cache-dir -e ".[ml]"

USER spark

# Set Python 3.12 for Spark workers
ENV PYSPARK_PYTHON=python3.12
ENV PYSPARK_DRIVER_PYTHON=python3.12

# Set PYTHONPATH for Spark
ENV PYTHONPATH="/opt/anip:${PYTHONPATH}"
```

### Key Changes

1. **Install Python 3.12** via `deadsnakes/ppa`
2. **Set as default** using `update-alternatives`
3. **Set environment variables:**
   - `PYSPARK_PYTHON=python3.12` - For Spark workers
   - `PYSPARK_DRIVER_PYTHON=python3.12` - For Spark driver (consistency)

---

## 🚀 Apply the Fix

```bash
# Rebuild Spark images
docker compose build spark-master spark-worker

# Restart Spark services
docker compose up -d spark-master spark-worker

# Verify Python version
docker exec spark-master python3 --version
# Should output: Python 3.12.x

docker exec spark-worker python3 --version
# Should output: Python 3.12.x

# Test the Spark job
docker exec anip-airflow-scheduler airflow dags trigger spark_ml_processing
```

---

## 📊 Verification

### Check Python Versions

```bash
# Airflow container
docker exec anip-airflow-scheduler python --version
# Output: Python 3.12.x

# Spark master
docker exec spark-master python3 --version
# Output: Python 3.12.x

# Spark worker
docker exec spark-worker python3 --version
# Output: Python 3.12.x
```

### Check Environment Variables

```bash
# Spark worker environment
docker exec spark-worker env | grep PYSPARK
# Should show:
# PYSPARK_PYTHON=python3.12
# PYSPARK_DRIVER_PYTHON=python3.12
```

### Monitor Spark Job

```bash
# Watch the task logs
docker compose logs -f airflow-scheduler

# Check Spark UI
open http://localhost:8080  # Spark Master UI
```

---

## 🎯 Why This Works

### Python Version Consistency

| Component | Python Version | Image Base |
|-----------|---------------|------------|
| **Airflow** | 3.12 | `apache/airflow:2.9.3` |
| **Spark Master** | 3.12 ✅ | `apache/spark:4.0.0` + Python 3.12 |
| **Spark Worker** | 3.12 ✅ | `apache/spark:4.0.0` + Python 3.12 |

### PySpark Communication Flow

```
┌─────────────────────────────────┐
│   Airflow Container             │
│   Python 3.12                   │
│   ┌──────────────────────────┐  │
│   │ spark-submit             │  │
│   │ (Driver - Python 3.12)   │  │
│   └──────────┬───────────────┘  │
└──────────────┼──────────────────┘
               │ Serialize Python objects
               │ Using Python 3.12 format
               ▼
┌──────────────────────────────────┐
│   Spark Cluster                  │
│   ┌────────────┐  ┌────────────┐│
│   │  Master    │  │  Worker    ││
│   │ Python 3.12│  │ Python 3.12││ ✅ Match!
│   └────────────┘  └────────────┘│
└──────────────────────────────────┘
```

---

## 📝 Alternative Solutions

### Option 1: Use Same Base Image (Not Recommended)

Build both Airflow and Spark from the same Python base image. This requires more maintenance.

### Option 2: Downgrade Airflow to Python 3.10 (Not Recommended)

```dockerfile
FROM python:3.10-slim
# Install Airflow manually
```

**Problems:**
- Loses official Airflow image benefits
- More complex setup
- Airflow 2.9.3 is designed for Python 3.12

### Option 3: Use Conda/Pyenv in Spark (Overcomplicated)

Install version managers in Spark containers. Adds unnecessary complexity.

### ✅ Option 4: Install Python 3.12 in Spark (CHOSEN)

- Minimal changes
- Uses official images
- Clear and maintainable
- Best practice for PySpark version matching

---

## 🔍 Troubleshooting

### Error: "python3.12: command not found"

```bash
# Check if Python 3.12 is installed
docker exec spark-master which python3.12

# If not found, rebuild Spark images
docker compose build --no-cache spark-master spark-worker
```

### Error: "No module named 'distutils'"

Add `python3.12-distutils` to Dockerfile:

```dockerfile
RUN apt-get install -y python3.12-distutils
```

### Error: "pip: command not found"

Reinstall pip for Python 3.12:

```bash
docker exec spark-master python3.12 -m ensurepip
```

---

## 📚 Related Documentation

- [PySpark Version Requirements](https://spark.apache.org/docs/latest/api/python/getting_started/install.html)
- [Spark Configuration](https://spark.apache.org/docs/latest/configuration.html#environment-variables)
- [Python Version Compatibility](https://docs.python.org/3/c-api/stable.html)

---

## 🎓 Lessons Learned

1. **Always match Python minor versions** between Spark driver and workers
2. **Use environment variables** (`PYSPARK_PYTHON`, `PYSPARK_DRIVER_PYTHON`) to explicitly set Python paths
3. **Verify versions** before running production workloads
4. **Document version requirements** in your project README
5. **Test end-to-end** after version changes

---

**Status:** ✅ Fixed  
**Priority:** Critical (Blocking)  
**Category:** Environment / Compatibility

