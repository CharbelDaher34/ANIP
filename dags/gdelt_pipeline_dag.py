"""
Airflow DAG for GDELT data pipeline.
Free tier: Unlimited (completely free, no API key required)
Topic: Deep Learning & Neural Networks
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

def ingest_gdelt():
    """Ingest articles from GDELT about Deep Learning."""
    from anip.shared.ingestion.gdelt_ingestor import GDELTIngestor
    from anip.shared.utils.db_utils import save_articles_batch
    
    print("📰 Starting GDELT ingestion (Topic: Deep Learning)...")
    ingestor = GDELTIngestor()
    # Fetch deep learning and neural networks articles
    articles = ingestor.fetch(query="deep learning neural networks", max_records=20)
    
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
# Schedule: Every 12 hours (2 times/day, GDELT has no rate limits)
dag = DAG(
    'gdelt_pipeline',
    default_args=default_args,
    description='Ingest deep learning news from GDELT (unlimited free tier)',
    schedule_interval=timedelta(hours=12),
    catchup=False,
    tags=['ingestion', 'gdelt', 'deep-learning'],
)

# Define tasks
ingest_task = PythonOperator(
    task_id='ingest_gdelt',
    python_callable=ingest_gdelt,
    dag=dag,
)

ingest_task

