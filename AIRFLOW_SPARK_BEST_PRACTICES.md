# Airflow + Spark Integration Best Practices

## Current Setup Analysis

### ✅ What You Have (SparkSubmitOperator)

**Architecture:**
```
Airflow Scheduler (with Spark client)
    ↓ spark-submit
Spark Master (spark://spark-master:7077)
    ↓ distributes work
Spark Workers (execute tasks)
```

**Verdict:** This is a **solid approach** for Docker Compose deployments! ✅

---

## Recommended Improvements

### 1. **Optimize Spark Installation in Airflow** (Keep current approach)

Instead of full Spark, install only client:

```dockerfile
# Dockerfile.airflow - OPTIMIZED VERSION
FROM apache/airflow:2.9.3

USER root

# Install only Java (smaller footprint)
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jre-headless \
    && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

USER airflow

# Install Spark provider (includes spark-submit wrapper)
RUN pip install --no-cache-dir \
    apache-airflow-providers-apache-spark==4.10.0 \
    pyspark==3.5.0  # Just the Python client, not full Spark
```

**Benefits:**
- Reduces image size by ~400MB
- Still uses SparkSubmitOperator
- Airflow just needs PySpark client, not full Spark distribution

---

### 2. **Alternative: Use Livy (REST API)** (Better decoupling)

**Setup:**

```yaml
# docker-compose.yml - Add Livy service
services:
  livy:
    image: apache/livy:latest
    container_name: anip-livy
    depends_on:
      - spark-master
    environment:
      SPARK_MASTER: spark://spark-master:7077
    ports:
      - "8998:8998"
    networks:
      - anip-net
```

**DAG:**

```python
from airflow.providers.apache.livy.operators.livy import LivyOperator

spark_task = LivyOperator(
    task_id='spark_ml_processing',
    file='/opt/anip/spark/ml_processing.py',
    proxy_user='airflow',
    livy_conn_id='livy_default',
    dag=dag,
)
```

**Benefits:**
- ✅ No Spark binaries in Airflow at all
- ✅ REST-based (can call from anywhere)
- ✅ Better for multi-tenant environments
- ✅ Session management built-in

---

### 3. **For Production: Kubernetes** (Best scalability)

When you're ready to scale:

```yaml
# kubernetes/spark-operator.yaml
apiVersion: sparkoperator.k8s.io/v1beta2
kind: SparkApplication
metadata:
  name: anip-ml-processing
spec:
  type: Python
  pythonVersion: "3"
  mode: cluster
  image: "anip-spark:latest"
  mainApplicationFile: "local:///opt/anip/spark/ml_processing.py"
  sparkVersion: "3.5.0"
  driver:
    cores: 1
    memory: "2g"
  executor:
    cores: 1
    instances: 2
    memory: "2g"
```

**Airflow DAG:**

```python
from airflow.providers.cncf.kubernetes.operators.spark_kubernetes import SparkKubernetesOperator

spark_task = SparkKubernetesOperator(
    task_id='spark_ml_processing',
    namespace='default',
    application_file='kubernetes/spark-operator.yaml',
    kubernetes_conn_id='kubernetes_default',
)
```

---

## Comparison Table

| Approach | Complexity | Airflow Image Size | Scalability | Production Ready | Best For |
|----------|-----------|-------------------|-------------|------------------|----------|
| **SparkSubmitOperator** (Current) | ⭐⭐ | Large (~1.5GB) | ⭐⭐⭐ | ⭐⭐⭐ | Docker Compose |
| **SparkSubmitOperator + PySpark only** | ⭐⭐ | Medium (~1GB) | ⭐⭐⭐ | ⭐⭐⭐⭐ | Docker Compose |
| **Livy** | ⭐⭐⭐ | Small (~800MB) | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Multi-tenant |
| **SparkKubernetesOperator** | ⭐⭐⭐⭐ | Small | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Cloud/K8s |
| **KubernetesPodOperator** | ⭐⭐⭐⭐ | Small | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Cloud/K8s |
| **DockerOperator** | ⭐ | Small | ⭐⭐ | ⭐ | Dev only |

---

## My Recommendation

### For Your Current Docker Compose Setup:

**Keep SparkSubmitOperator but optimize:**

1. **Install only PySpark client** in Airflow (not full Spark)
2. **Use the optimization** shown in section 1 above
3. **Consider Livy** if you want lighter Airflow images

### For Future/Production:

**Migrate to Kubernetes + SparkKubernetesOperator:**

Benefits:
- Auto-scaling Spark executors
- Better resource utilization  
- Dynamic allocation
- Industry standard for production ML pipelines

---

## Additional Best Practices

### 1. **Connection Management**

✅ Use Airflow Connections (you're doing this now):
```python
conn_id='spark_default'  # Managed in Airflow UI/DB
```

### 2. **Resource Management**

```python
# In your DAG
spark_task = SparkSubmitOperator(
    ...
    conf={
        'spark.executor.memory': '2g',
        'spark.driver.memory': '2g',
        'spark.dynamicAllocation.enabled': 'true',  # ✅ Enable
        'spark.shuffle.service.enabled': 'true',
        'spark.dynamicAllocation.minExecutors': '1',
        'spark.dynamicAllocation.maxExecutors': '5',
    }
)
```

### 3. **Error Handling**

```python
spark_task = SparkSubmitOperator(
    ...
    retries=2,
    retry_delay=timedelta(minutes=5),
    email_on_failure=True,
    email_on_retry=False,
)
```

### 4. **Monitoring**

Add Spark History Server:

```yaml
# docker-compose.yml
services:
  spark-history:
    image: apache/spark:4.0.0
    container_name: spark-history
    command: /opt/spark/bin/spark-class org.apache.spark.deploy.history.HistoryServer
    ports:
      - "18080:18080"
    environment:
      SPARK_HISTORY_OPTS: "-Dspark.history.fs.logDirectory=/tmp/spark-events"
    volumes:
      - ./volumes/spark-events:/tmp/spark-events
    networks:
      - anip-net
```

### 5. **Separate Concerns**

```python
# Good: Spark for heavy compute, Airflow for orchestration
spark_heavy_ml = SparkSubmitOperator(...)

# Bad: Running ML in PythonOperator (defeats purpose of Spark)
python_ml = PythonOperator(
    python_callable=run_ml_model  # ❌ Don't do heavy compute here
)
```

---

## Migration Path

### Phase 1: Optimize Current Setup (Now)
- Use PySpark-only in Airflow
- Add Spark History Server
- Improve monitoring

### Phase 2: Consider Livy (3-6 months)
- If you need multi-tenancy
- If Airflow image size is a concern
- If you want REST-based submission

### Phase 3: Move to Kubernetes (6-12 months)
- When scaling becomes an issue
- When you need auto-scaling
- When moving to cloud

---

## Code Examples

### Optimized Dockerfile.airflow

```dockerfile
FROM apache/airflow:2.9.3

USER root

# Minimal Java install
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jre-headless \
    && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

USER airflow

# Install anip package
COPY --chown=airflow:root pyproject.toml setup.py /opt/anip/
COPY --chown=airflow:root src/ /opt/anip/src/
WORKDIR /opt/anip
RUN pip install --no-cache-dir -e ".[airflow,ml]"

# Install Spark provider + PySpark client only
RUN pip install --no-cache-dir \
    apache-airflow-providers-apache-spark==4.10.0 \
    pyspark==3.5.0

# Copy scripts
COPY --chown=airflow:root scripts/ /opt/anip/scripts/
RUN chmod +x /opt/anip/scripts/airflow_entrypoint.sh

WORKDIR /opt/airflow
```

### Dynamic Resource Allocation

```python
# dags/spark_ml_processing_dag.py
spark_ml_task = SparkSubmitOperator(
    task_id='spark_ml_processing',
    application='/opt/anip/spark/ml_processing.py',
    conn_id='spark_default',
    conf={
        # Memory
        'spark.executor.memory': '2g',
        'spark.driver.memory': '2g',
        
        # Dynamic allocation (adjust based on workload)
        'spark.dynamicAllocation.enabled': 'true',
        'spark.dynamicAllocation.minExecutors': '1',
        'spark.dynamicAllocation.maxExecutors': '10',
        'spark.dynamicAllocation.initialExecutors': '2',
        
        # Timeouts
        'spark.network.timeout': '800s',
        'spark.executor.heartbeatInterval': '60s',
        
        # Optimization
        'spark.sql.adaptive.enabled': 'true',
        'spark.sql.adaptive.coalescePartitions.enabled': 'true',
    },
    verbose=True,
    dag=dag,
)
```

---

## Summary

**Your current approach is GOOD!** ✅

For Docker Compose deployments, SparkSubmitOperator with a separate Spark cluster is a **standard, production-ready pattern**.

**Quick wins:**
1. Optimize Airflow Dockerfile (use PySpark only)
2. Add Spark History Server for monitoring
3. Enable dynamic resource allocation

**Future considerations:**
- Livy if you need lighter Airflow
- Kubernetes when you need to scale beyond single-node

You're on the right track! 🎉

