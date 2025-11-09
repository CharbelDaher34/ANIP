"""
Airflow DAG for GDELT data pipeline.
"""
import os
import sys
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

# Add shared module to path
sys.path.insert(0, '/opt/airflow')

def ingest_gdelt():
    """Ingest articles from GDELT."""
    from shared.ingestion.gdelt_ingestor import GDELTIngestor
    from shared.utils.db_utils import save_articles_batch
    
    print("📰 Starting GDELT ingestion...")
    ingestor = GDELTIngestor()
    articles = ingestor.fetch(query="technology", max_records=20)
    
    print(f"✅ Fetched {len(articles)} articles from GDELT")
    
    saved = save_articles_batch(articles)
    print(f"✅ Saved {saved} articles to database")
    
    return saved

# Default args for the DAG
default_args = {
    'owner': 'anip',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Create the DAG
dag = DAG(
    'gdelt_pipeline',
    default_args=default_args,
    description='Ingest news from GDELT',
    schedule_interval=timedelta(hours=12),
    catchup=False,
    tags=['ingestion', 'gdelt'],
)

# Define tasks
ingest_task = PythonOperator(
    task_id='ingest_gdelt',
    python_callable=ingest_gdelt,
    dag=dag,
)

ingest_task

