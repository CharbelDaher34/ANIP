"""
Airflow DAG for NewsData.io data pipeline.
Free tier: 200 API credits/day (10 articles per credit)
Topic: Machine Learning (ML)
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

def ingest_newsdata():
    """Ingest articles from NewsData.io about Machine Learning."""
    from anip.shared.ingestion.newsdata_ingestor import NewsDataIngestor
    from anip.shared.utils.db_utils import save_articles_batch
    
    print("📰 Starting NewsData ingestion (Topic: Machine Learning)...")
    ingestor = NewsDataIngestor()
    # Fetch ML-related articles
    articles = ingestor.fetch(country="us", language="en", q="machine learning", category="top")
    
    print(f"✅ Fetched {len(articles)} articles from NewsData")
    
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
# Schedule: Every 6 hours (4 times/day = 4 credits/day, safe for 200 credits/day limit)
dag = DAG(
    'newsdata_pipeline',
    default_args=default_args,
    description='Ingest ML news from NewsData.io (200 credits/day limit)',
    schedule_interval=timedelta(hours=6),
    catchup=False,
    tags=['ingestion', 'newsdata', 'machine-learning'],
)

# Define tasks
ingest_task = PythonOperator(
    task_id='ingest_newsdata',
    python_callable=ingest_newsdata,
    dag=dag,
)

ingest_task

