"""
Airflow DAG for WorldNewsAPI.com data pipeline.
Free tier: 100 requests/day (limited)
Topic: Robotics & Automation
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

def ingest_worldnewsapi():
    """Ingest articles from WorldNewsAPI.com about Robotics and Automation."""
    from anip.shared.ingestion.worldnewsapi_ingestor import WorldNewsAPIIngestor
    from anip.shared.utils.db_utils import save_articles_batch
    
    print("📰 Starting WorldNewsAPI ingestion (Topic: Robotics & Automation)...")
    ingestor = WorldNewsAPIIngestor()
    # Fetch robotics and automation articles
    articles = ingestor.fetch(text="robotics automation AI", language="en", number=10)
    
    print(f"✅ Fetched {len(articles)} articles from WorldNewsAPI")
    
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
# Schedule: Every 12 hours (2 times/day = 2 requests/day, safe for 100/day limit)
dag = DAG(
    'worldnewsapi_pipeline',
    default_args=default_args,
    description='Ingest robotics news from WorldNewsAPI.com (100 req/day limit)',
    schedule_interval=timedelta(hours=12),  # Twice per day
    catchup=False,
    tags=['ingestion', 'worldnewsapi', 'robotics', 'limited'],
)

# Define tasks
ingest_task = PythonOperator(
    task_id='ingest_worldnewsapi',
    python_callable=ingest_worldnewsapi,
    dag=dag,
)

ingest_task

