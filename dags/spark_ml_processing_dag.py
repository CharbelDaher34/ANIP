"""
Airflow DAG for Spark ML Processing Pipeline.

This DAG runs the Spark ML processing job that:
- Loads articles from the database
- Applies ML transformations (topic classification, sentiment analysis, embedding generation)
- Saves the results back to the database
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from anip.config import settings

# Default args for the DAG
default_args = {
    'owner': 'anip',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# Create the DAG
dag = DAG(
    'spark_ml_processing',
    default_args=default_args,
    description='Process articles with Spark ML models (topic, sentiment, embeddings)',
    schedule_interval=timedelta(hours=1),  # Run every hour
    catchup=False,
    tags=['ml', 'spark', 'processing'],
)

def check_articles_to_process():
    """
    Check if there are articles that need ML processing.
    Returns True if there are articles to process, False otherwise.
    """
    from sqlalchemy import create_engine, text
    
    # Use pydantic settings for database connection
    db_url = settings.database.url
    engine = create_engine(db_url)
    
    # Check for articles that need ML processing
    query = text("""
        SELECT COUNT(*) as count
        FROM newsarticle
        WHERE topic IS NULL OR sentiment IS NULL OR embedding IS NULL
    """)
    
    with engine.connect() as conn:
        result = conn.execute(query)
        row = result.fetchone()
        count = row[0] if row else 0
    
    print(f"📊 Found {count} articles that need ML processing")
    
    if count == 0:
        print("✅ No articles to process - all articles have ML predictions")
        return False
    
    return True

# Task to check if there are articles to process
check_task = PythonOperator(
    task_id='check_articles_to_process',
    python_callable=check_articles_to_process,
    dag=dag,
)

# Spark task using SparkSubmitOperator
spark_ml_task = SparkSubmitOperator(
    task_id='spark_ml_processing',
    application='/opt/anip/spark/ml_processing.py',
    conn_id='spark_default',
    conf={
        'spark.executor.memory': '2g',
        'spark.driver.memory': '2g',
        'spark.sql.execution.arrow.pyspark.enabled': 'false',
    },
    env_vars={
        'POSTGRES_HOST': settings.database.host,
        'POSTGRES_PORT': str(settings.database.port),
        'POSTGRES_DB': settings.database.db,
        'POSTGRES_USER': settings.database.user,
        'POSTGRES_PASSWORD': settings.database.password,
        'MLFLOW_TRACKING_URI': settings.mlflow.tracking_uri,
    },
    name='anip-ml-processing',
    verbose=True,
    dag=dag,
)

# Set task dependencies
check_task >> spark_ml_task

