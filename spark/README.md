# Spark Jobs

Batch processing jobs for news data.

## Jobs

- `data_cleaning.py`: Clean and deduplicate articles
- `aggregation.py`: Aggregate statistics by source

## Running Locally

```bash
spark-submit --master spark://spark-master:7077 \
  spark/data_cleaning.py \
  /data/raw/articles.parquet \
  /data/clean/articles.parquet
```

## Running from Airflow

Use SparkSubmitOperator in your DAGs.
