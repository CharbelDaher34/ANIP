"""
Airflow DAG for NewsAPI data pipeline.
Free tier: 100 requests/day
Topic: Artificial Intelligence (AI)
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

def ingest_newsapi():
    """Ingest articles from NewsAPI about Artificial Intelligence."""
    from anip.shared.ingestion.newsapi_ingestor import NewsAPIIngestor
    from anip.shared.utils.db_utils import save_articles_batch
    
    print("📰 Starting NewsAPI ingestion (Topic: Artificial Intelligence)...")
    ingestor = NewsAPIIngestor()
    # Fetch AI-related articles using query parameter
    articles = ingestor.fetch(query="artificial intelligence AI", page_size=20)
    
    print(f"✅ Fetched {len(articles)} articles from NewsAPI")
    
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
    'newsapi_pipeline',
    default_args=default_args,
    description='Ingest AI news from NewsAPI (100 req/day limit)',
    schedule_interval=timedelta(hours=6),
    catchup=False,
    tags=['ingestion', 'newsapi', 'ai'],
)

# Define tasks
ingest_task = PythonOperator(
    task_id='ingest_newsapi',
    python_callable=ingest_newsapi,
    dag=dag,
)

ingest_task

