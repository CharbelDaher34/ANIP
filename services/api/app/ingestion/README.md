# 📰 News Ingestion Layer

Modular, testable news ingestors for various data sources.

## 🏗️ Architecture

Each ingestor:
- ✅ Is a **self-contained class** inheriting from `BaseIngestor`
- ✅ Returns a list of `NewsArticleBase` objects (no DB writes)
- ✅ Can be tested independently or integrated into Airflow DAGs
- ✅ Handles its own API authentication and error handling

## 📦 Available Ingestors

### 1. **NewsAPIIngestor** - `newsapi_ingestor.py`
Fetches articles from [NewsAPI.org](https://newsapi.org/)

```python
from app.ingestion import NewsAPIIngestor

ingestor = NewsAPIIngestor(api_key="YOUR_KEY")
articles = ingestor.fetch(query="AI", country="us", page_size=10)
```

**Requirements:** NewsAPI key (get one at https://newsapi.org/)

---

### 2. **RedditIngestor** - `reddit_ingestor.py`
Fetches hot posts from Reddit subreddits

```python
from app.ingestion import RedditIngestor

ingestor = RedditIngestor()
articles = ingestor.fetch(subreddit="technology", limit=10)
```

**Requirements:** None (uses public JSON API)

---

### 3. **GDELTIngestor** - `gdelt_ingestor.py`
Fetches real-time events from [GDELT Project](https://www.gdeltproject.org/)

```python
from app.ingestion import GDELTIngestor

ingestor = GDELTIngestor()
articles = ingestor.fetch(limit=10)
```

**Requirements:** `pandas` package

---

## 🧪 Testing

### Run all tests:
```bash
# From container or virtual environment
python -m app.tests.test_ingestion
```

### Run standalone test script:
```bash
cd services/api/app/tests
python test_ingestion_standalone.py

# Test specific ingestor
python test_ingestion_standalone.py --reddit
python test_ingestion_standalone.py --newsapi --key YOUR_KEY
```

---

## 🛠️ Utilities

`utils.py` contains helper functions:

```python
from app.ingestion.utils import deduplicate_articles, filter_by_language

# Remove duplicate URLs
unique_articles = deduplicate_articles(articles)

# Filter by language
english_articles = filter_by_language(articles, language="en")
```

---

## 🔌 Integration Examples

### With FastAPI endpoint:
```python
from fastapi import APIRouter
from app.ingestion import RedditIngestor

router = APIRouter()

@router.post("/ingest/reddit")
def ingest_reddit():
    ingestor = RedditIngestor()
    articles = ingestor.fetch(subreddit="worldnews", limit=50)
    # Save to DB or send to Kafka
    return {"articles_fetched": len(articles)}
```

### With Airflow DAG:
```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from app.ingestion import NewsAPIIngestor

def fetch_news():
    ingestor = NewsAPIIngestor(api_key=Variable.get("NEWSAPI_KEY"))
    articles = ingestor.fetch(query="politics", page_size=100)
    # Process and store articles
    return len(articles)

with DAG("news_ingestion", schedule_interval="@hourly") as dag:
    fetch_task = PythonOperator(
        task_id="fetch_news",
        python_callable=fetch_news
    )
```

---

## 🚀 Adding New Ingestors

1. Create a new file in `ingestion/` (e.g., `twitter_ingestor.py`)
2. Inherit from `BaseIngestor` and implement the `fetch()` method
3. Return a list of `NewsArticleBase` objects
4. Add tests in `tests/test_ingestion.py`
5. Export in `ingestion/__init__.py`

Example:
```python
from app.ingestion.base import BaseIngestor
from app.models.news import NewsArticleBase

class TwitterIngestor(BaseIngestor):
    def fetch(self, query: str, limit: int = 10) -> List[NewsArticleBase]:
        # Your implementation here
        pass
```

---

## 📋 Dependencies

Add to your `requirements.txt` or `pyproject.toml`:
```
requests>=2.31.0
pandas>=2.0.0  # For GDELT ingestor
```

---

## 🔐 Environment Variables

```bash
# .env file
NEWSAPI_KEY=your_newsapi_key_here
```

---

## ⚠️ Error Handling

All ingestors raise standard `requests` exceptions:
- `requests.exceptions.HTTPError` - HTTP error (4xx, 5xx)
- `requests.exceptions.Timeout` - Request timeout
- `requests.exceptions.ConnectionError` - Network error

Handle them in your calling code:
```python
try:
    articles = ingestor.fetch()
except requests.exceptions.HTTPError as e:
    logger.error(f"HTTP error: {e}")
except requests.exceptions.Timeout:
    logger.error("Request timed out")
```

