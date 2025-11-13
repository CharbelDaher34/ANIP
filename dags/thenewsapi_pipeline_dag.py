"""
Airflow DAG for TheNewsAPI.com data pipeline.
Free tier: 100 requests/day (3 articles per request)
Topic: Computer Vision
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

def ingest_thenewsapi():
    """Ingest articles from TheNewsAPI.com about Computer Vision."""
    from anip.shared.ingestion.thenewsapi_ingestor import TheNewsAPIIngestor
    from anip.shared.utils.db_utils import save_articles_batch
    
    print("📰 Starting TheNewsAPI ingestion (Topic: Computer Vision)...")
    ingestor = TheNewsAPIIngestor()
    # Fetch computer vision articles (max 3 per request on free tier)
    articles = ingestor.fetch(locale="us", search="computer vision", limit=3)
    
    print(f"✅ Fetched {len(articles)} articles from TheNewsAPI")
    
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
# Schedule: Every 6 hours (4 times/day = 4 requests/day, safe for 100/day limit)
dag = DAG(
    'thenewsapi_pipeline',
    default_args=default_args,
    description='Ingest computer vision news from TheNewsAPI.com (100 req/day limit)',
    schedule_interval=timedelta(hours=6),  # Every 6 hours
    catchup=False,
    tags=['ingestion', 'thenewsapi', 'computer-vision'],
)

# Define tasks
ingest_task = PythonOperator(
    task_id='ingest_thenewsapi',
    python_callable=ingest_thenewsapi,
    dag=dag,
)

ingest_task

