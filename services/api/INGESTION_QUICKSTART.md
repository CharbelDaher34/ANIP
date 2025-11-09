# 🚀 News Ingestion Layer - Quick Start

Your modular, testable news ingestion system is ready!

## 📁 Folder Structure

```
services/api/app/
├── main.py
├── db.py
├── models/
│   ├── __init__.py
│   └── news.py                     # NewsArticleBase model
├── ingestion/                       # ✨ NEW: Ingestion layer
│   ├── __init__.py
│   ├── base.py                     # Abstract base class
│   ├── newsapi_ingestor.py         # NewsAPI.org ingestor
│   ├── reddit_ingestor.py          # Reddit JSON API ingestor
│   ├── gdelt_ingestor.py           # GDELT real-time events
│   ├── utils.py                    # Helper functions
│   └── README.md                   # Full documentation
└── tests/                           # ✨ NEW: Tests
    ├── __init__.py
    ├── test_ingestion.py           # Module-style tests
    └── test_ingestion_standalone.py # Standalone script
```

---

## 🧪 Test It Now!

### Option 1: Run the test module
```bash
# From your API container or venv
cd /storage/hussein/anip
docker-compose exec api python -m app.tests.test_ingestion
```

### Option 2: Run the standalone script
```bash
# Test Reddit (no API key needed!)
docker-compose exec api python app/tests/test_ingestion_standalone.py --reddit --limit 5

# Test all ingestors
export NEWSAPI_KEY="your_key_here"
docker-compose exec api python app/tests/test_ingestion_standalone.py
```

---

## 💡 Usage Examples

### 1. **Fetch from Reddit** (simplest, no API key)
```python
from app.ingestion import RedditIngestor

ingestor = RedditIngestor()
articles = ingestor.fetch(subreddit="worldnews", limit=25)

for article in articles:
    print(f"{article.title} - {article.url}")
```

### 2. **Fetch from NewsAPI**
```python
from app.ingestion import NewsAPIIngestor
import os

api_key = os.getenv("NEWSAPI_KEY")
ingestor = NewsAPIIngestor(api_key)
articles = ingestor.fetch(query="artificial intelligence", page_size=50)
```

### 3. **Fetch from GDELT** (real-time global events)
```python
from app.ingestion import GDELTIngestor

ingestor = GDELTIngestor()
articles = ingestor.fetch(limit=100)
```

### 4. **Deduplicate & Filter**
```python
from app.ingestion import RedditIngestor
from app.ingestion.utils import deduplicate_articles, filter_by_language

ingestor = RedditIngestor()
articles = ingestor.fetch(subreddit="news", limit=100)

# Remove duplicates by URL
unique_articles = deduplicate_articles(articles)

# Filter by language
english_articles = filter_by_language(unique_articles, "en")

print(f"Fetched: {len(articles)}, Unique: {len(unique_articles)}")
```

---

## 🔌 Integrate with FastAPI

Add to your `main.py`:

```python
from fastapi import APIRouter
from app.ingestion import RedditIngestor, NewsAPIIngestor
from app.models.news import NewsArticle
from app.db import get_session

router = APIRouter(prefix="/ingest", tags=["ingestion"])

@router.post("/reddit")
def ingest_reddit(subreddit: str = "worldnews", limit: int = 50):
    """Fetch and store Reddit posts."""
    ingestor = RedditIngestor()
    articles = ingestor.fetch(subreddit=subreddit, limit=limit)
    
    # Save to database
    with get_session() as session:
        for article_base in articles:
            article = NewsArticle(**article_base.dict())
            session.add(article)
        session.commit()
    
    return {"status": "success", "articles_fetched": len(articles)}

@router.post("/newsapi")
def ingest_newsapi(query: str, limit: int = 50, api_key: str = None):
    """Fetch and store NewsAPI articles."""
    import os
    api_key = api_key or os.getenv("NEWSAPI_KEY")
    
    ingestor = NewsAPIIngestor(api_key)
    articles = ingestor.fetch(query=query, page_size=limit)
    
    # Save to database (same as above)
    # ... or send to Kafka
    
    return {"status": "success", "articles_fetched": len(articles)}
```

---

## 🤖 Integrate with Airflow

Create an Airflow DAG:

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import os
import sys

sys.path.insert(0, "/path/to/anip/services/api")

from app.ingestion import NewsAPIIngestor, RedditIngestor

def fetch_news():
    """Fetch news from multiple sources."""
    # Reddit
    reddit_ingestor = RedditIngestor()
    reddit_articles = reddit_ingestor.fetch(subreddit="worldnews", limit=100)
    
    # NewsAPI
    newsapi_key = os.getenv("NEWSAPI_KEY")
    news_ingestor = NewsAPIIngestor(newsapi_key)
    news_articles = news_ingestor.fetch(query="global", page_size=100)
    
    all_articles = reddit_articles + news_articles
    
    # Save to DB or send to Kafka
    # from app.db import save_articles
    # save_articles(all_articles)
    
    return len(all_articles)

default_args = {
    "owner": "anip",
    "depends_on_past": False,
    "start_date": datetime(2025, 1, 1),
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    "news_ingestion",
    default_args=default_args,
    description="Ingest news from multiple sources",
    schedule_interval="@hourly",  # Run every hour
    catchup=False,
) as dag:

    ingest_task = PythonOperator(
        task_id="ingest_news",
        python_callable=fetch_news,
    )
```

---

## 📊 Next Steps

### 1. **Test the ingestors**
```bash
docker-compose exec api python app/tests/test_ingestion_standalone.py --reddit
```

### 2. **Add API endpoints** (optional)
Integrate ingestors into your FastAPI `main.py`

### 3. **Schedule with Airflow** (recommended)
Create DAGs to run ingestors on a schedule

### 4. **Send to Kafka** (for real-time processing)
```python
from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers=['kafka:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

for article in articles:
    producer.send('news-topic', value=article.dict())
```

### 5. **Add more sources**
Create new ingestors by inheriting from `BaseIngestor`

---

## 🔐 API Keys

Get your free API keys:

- **NewsAPI**: https://newsapi.org/ (500 requests/day free)
- **Reddit**: No API key needed for public JSON endpoints
- **GDELT**: Free, no API key needed

Add to your `.env` file:
```bash
NEWSAPI_KEY=your_newsapi_key_here
```

---

## 📚 Full Documentation

See `services/api/app/ingestion/README.md` for detailed documentation.

---

## ✅ What You Have Now

✅ **Modular ingestors** - Easy to test, extend, and maintain  
✅ **No DB coupling** - Returns `NewsArticleBase` objects  
✅ **Test scripts** - Verify everything works independently  
✅ **Ready for Airflow** - Can be scheduled as DAG tasks  
✅ **Ready for Kafka** - Can stream to Kafka topics  
✅ **Ready for FastAPI** - Can be triggered via API endpoints  

---

🎉 **You're all set! Start by testing with Reddit (no API key needed):**

```bash
docker-compose exec api python app/tests/test_ingestion_standalone.py --reddit
```

