# Quick Reference: Triggering Methods

## 🚀 Airflow DAGs (Automatic)

### Check Status
```bash
# List all DAGs
docker-compose exec airflow-scheduler airflow dags list | grep pipeline

# Check if running
docker-compose ps airflow-scheduler airflow-webserver
```

### Trigger Manually
```bash
# Via CLI
docker-compose exec airflow-scheduler airflow dags trigger newsapi_pipeline
docker-compose exec airflow-scheduler airflow dags trigger newsdata_pipeline
docker-compose exec airflow-scheduler airflow dags trigger gdelt_pipeline

# Via UI
# http://localhost:8080 → Click DAG → Trigger DAG
```

### Monitor
```bash
# View logs
docker-compose logs airflow-scheduler | tail -50

# Check DAG runs
docker-compose exec airflow-scheduler airflow dags list-runs -d newsapi_pipeline
```

---

## ⚡ Spark Processing (Manual)

### Start Spark
```bash
docker-compose up -d spark-master spark-worker
```

### Process from Database
```bash
docker-compose exec spark-master spark-submit \
    --master spark://spark-master:7077 \
    /opt/anip/spark/ml_processing.py
```

### Process from Parquet
```bash
docker-compose exec spark-master spark-submit \
    --master spark://spark-master:7077 \
    /opt/anip/spark/ml_processing.py \
    /data/input.parquet \
    /data/output.parquet
```

### Monitor
```bash
# Spark UI
http://localhost:8081

# Logs
docker-compose logs spark-master | tail -50
```

---

## 📊 View Results

### CLI Script
```bash
python scripts/view_results.py stats
python scripts/view_results.py recent 20
python scripts/view_results.py search "AI"
```

### API
```bash
curl http://localhost:8000/api/v1/statistics
curl http://localhost:8000/api/v1/articles?limit=10
```

### Database
```bash
docker-compose exec postgres psql -U anip -d anip -c \
  "SELECT COUNT(*) FROM newsarticle;"
```

---

## 🔧 Common Commands

### Start Everything
```bash
docker-compose up -d
```

### Restart Services
```bash
docker-compose restart airflow-scheduler airflow-webserver
docker-compose restart spark-master spark-worker
docker-compose restart api
```

### Check Logs
```bash
docker-compose logs -f airflow-scheduler
docker-compose logs -f spark-master
docker-compose logs -f api
```

### Stop Everything
```bash
docker-compose down
```
