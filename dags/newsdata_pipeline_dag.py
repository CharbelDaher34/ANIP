"""
Airflow DAG for NewsData.io data pipeline.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from anip.config import settings

def ingest_newsdata():
    """Ingest articles from NewsData.io."""
    from anip.shared.ingestion.newsdata_ingestor import NewsDataIngestor
    from anip.shared.utils.db_utils import save_articles_batch
    
    api_key = settings.news_api.newsdata_api_key
    if not api_key:
        raise ValueError("NEWSDATA_API_KEY not set in configuration")
    
    print("📰 Starting NewsData ingestion...")
    ingestor = NewsDataIngestor(api_key=api_key)
    articles = ingestor.fetch(query="technology", country="us", page_size=20)
    
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
dag = DAG(
    'newsdata_pipeline',
    default_args=default_args,
    description='Ingest news from NewsData.io',
    schedule_interval=timedelta(hours=6),
    catchup=False,
    tags=['ingestion', 'newsdata'],
)

# Define tasks
ingest_task = PythonOperator(
    task_id='ingest_newsdata',
    python_callable=ingest_newsdata,
    dag=dag,
)

ingest_task

