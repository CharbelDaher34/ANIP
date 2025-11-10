"""
Airflow DAG for Spark ML Processing Pipeline.

This DAG runs the Spark ML processing job that:
- Loads articles from the database
- Applies ML transformations (topic classification, sentiment analysis, embedding generation)
- Saves the results back to the database
"""
import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

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
    import sys
    sys.path.insert(0, '/opt/airflow')
    
    from sqlalchemy import create_engine, text
    
    # Get database connection details from environment
    postgres_user = os.getenv('POSTGRES_USER')
    postgres_password = os.getenv('POSTGRES_PASSWORD')
    postgres_host = os.getenv('POSTGRES_HOST', 'postgres')
    postgres_port = os.getenv('POSTGRES_PORT', '5432')
    postgres_db = os.getenv('POSTGRES_DB', 'anip')
    
    if not postgres_user or not postgres_password:
        raise ValueError("POSTGRES_USER and POSTGRES_PASSWORD environment variables are required")
    
    db_url = f"postgresql+psycopg2://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"
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

# Spark task using docker exec
spark_ml_task = BashOperator(
    task_id='spark_ml_processing',
    bash_command='''
    docker exec spark-master /opt/spark/bin/spark-submit \
        --master spark://spark-master:7077 \
        --conf spark.executor.memory=2g \
        --conf spark.driver.memory=2g \
        --conf spark.sql.execution.arrow.pyspark.enabled=false \
        --name anip-ml-processing \
        /opt/anip/spark/ml_processing.py
    ''',
    dag=dag,
)

# Set task dependencies
check_task >> spark_ml_task

