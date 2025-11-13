"""
Airflow DAG for Mediastack data pipeline.
Free tier: 100 requests/month (very limited)
Topic: Natural Language Processing (NLP)
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

def ingest_mediastack():
    """Ingest articles from Mediastack about Natural Language Processing."""
    from anip.shared.ingestion.mediastack_ingestor import MediastackIngestor
    from anip.shared.utils.db_utils import save_articles_batch
    
    print("📰 Starting Mediastack ingestion (Topic: Natural Language Processing)...")
    ingestor = MediastackIngestor()
    # Fetch NLP-related articles, minimal due to 100 requests/month limit
    articles = ingestor.fetch(countries="us", keywords="natural language processing NLP", limit=10)
    
    print(f"✅ Fetched {len(articles)} articles from Mediastack")
    
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
# Schedule: Once per day (30 requests/month, safe for 100/month limit)
dag = DAG(
    'mediastack_pipeline',
    default_args=default_args,
    description='Ingest NLP news from Mediastack (100 req/month limit)',
    schedule_interval=timedelta(days=1),  # Once per day
    catchup=False,
    tags=['ingestion', 'mediastack', 'nlp', 'limited'],
)

# Define tasks
ingest_task = PythonOperator(
    task_id='ingest_mediastack',
    python_callable=ingest_mediastack,
    dag=dag,
)

ingest_task

