# 🏗️ Ingestion Layer Architecture

## Design Philosophy

The ingestion layer follows these core principles:

### ✅ **Separation of Concerns**
- **Ingestors** → Fetch data only
- **Database layer** → Store data only  
- **API layer** → Expose endpoints only
- **Airflow DAGs** → Schedule tasks only

Each component can be tested and deployed independently.

---

## 🧩 Component Breakdown

### 1. **Base Ingestor** (`base.py`)
Abstract class that all ingestors inherit from.

```python
class BaseIngestor(ABC):
    @abstractmethod
    def fetch(self, **kwargs) -> List[NewsArticleBase]:
        """Fetch and return a list of NewsArticleBase objects."""
        ...
```

**Why?** Ensures consistent interface across all data sources.

---

### 2. **Concrete Ingestors**
Each ingestor implements `fetch()` and returns `NewsArticleBase` objects.

| Ingestor | Source | API Key Required | Rate Limit |
|----------|--------|------------------|------------|
| `NewsAPIIngestor` | NewsAPI.org | ✅ Yes | 500/day (free) |
| `RedditIngestor` | Reddit JSON | ❌ No | ~60/min |
| `GDELTIngestor` | GDELT Project | ❌ No | Unlimited |

**Why separate classes?**
- Each source has different auth, rate limits, response formats
- Easy to test each ingestor independently
- Can enable/disable sources without affecting others
- Can run different sources on different schedules in Airflow

---

### 3. **Data Flow**

```
┌─────────────┐
│  NewsAPI    │
│  Reddit     │──┐
│  GDELT      │  │
└─────────────┘  │
                 │ fetch()
                 ▼
         ┌───────────────┐
         │  Ingestor     │
         │  (returns)    │
         │ NewsArticleBase│
         │   objects      │
         └───────────────┘
                 │
                 ├──→ Save to PostgreSQL
                 ├──→ Send to Kafka
                 ├──→ Process with ML model
                 └──→ Return via API
```

**Key insight:** Ingestors return **data objects**, not database records.  
This makes them **composable** and **testable**.

---

## 🔄 Integration Patterns

### Pattern 1: **Direct DB Write**
```python
from app.ingestion import RedditIngestor
from app.models.news import NewsArticle
from app.db import get_session

ingestor = RedditIngestor()
articles = ingestor.fetch(subreddit="worldnews", limit=50)

with get_session() as session:
    for article_base in articles:
        article = NewsArticle(**article_base.dict())
        session.add(article)
    session.commit()
```

### Pattern 2: **Kafka Stream**
```python
from app.ingestion import NewsAPIIngestor
from kafka import KafkaProducer
import json

ingestor = NewsAPIIngestor(api_key="...")
articles = ingestor.fetch(query="AI", page_size=100)

producer = KafkaProducer(bootstrap_servers=['kafka:9092'])
for article in articles:
    producer.send('raw-news', value=json.dumps(article.dict()).encode())
```

### Pattern 3: **API Endpoint**
```python
from fastapi import APIRouter
from app.ingestion import RedditIngestor

@app.post("/ingest/reddit")
def trigger_ingestion(subreddit: str = "news"):
    ingestor = RedditIngestor()
    articles = ingestor.fetch(subreddit=subreddit, limit=100)
    # Process articles...
    return {"count": len(articles)}
```

### Pattern 4: **Airflow DAG** (Recommended)
```python
from airflow import DAG
from airflow.operators.python import PythonOperator

def ingest_news():
    ingestor = NewsAPIIngestor(api_key=Variable.get("NEWSAPI_KEY"))
    articles = ingestor.fetch(query="technology", page_size=100)
    # Save to DB or Kafka
    return len(articles)

with DAG("news_ingestion", schedule_interval="@hourly") as dag:
    PythonOperator(task_id="fetch", python_callable=ingest_news)
```

---

## 🧪 Testing Strategy

### Level 1: **Unit Tests** (Individual Ingestors)
```python
def test_reddit_ingestor():
    ingestor = RedditIngestor()
    articles = ingestor.fetch(subreddit="python", limit=5)
    
    assert len(articles) > 0
    assert all(isinstance(a, NewsArticleBase) for a in articles)
    assert all(a.source.startswith("r/") for a in articles)
```

### Level 2: **Integration Tests** (DB Writing)
```python
def test_ingest_and_save():
    ingestor = RedditIngestor()
    articles = ingestor.fetch(subreddit="test", limit=1)
    
    # Save to test database
    with get_test_session() as session:
        article = NewsArticle(**articles[0].dict())
        session.add(article)
        session.commit()
    
    # Verify saved
    assert session.query(NewsArticle).count() == 1
```

### Level 3: **Standalone Scripts** (Manual Testing)
```bash
python app/tests/test_ingestion_standalone.py --reddit --limit 3
```

---

## 🚀 Scaling Considerations

### **Rate Limiting**
Each ingestor handles rate limits internally:
```python
import time
from functools import wraps

def rate_limit(calls_per_minute):
    min_interval = 60.0 / calls_per_minute
    
    def decorator(func):
        last_called = [0.0]
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            
            result = func(*args, **kwargs)
            last_called[0] = time.time()
            return result
        
        return wrapper
    return decorator

class NewsAPIIngestor(BaseIngestor):
    @rate_limit(calls_per_minute=30)  # Free tier limit
    def fetch(self, **kwargs):
        # ... implementation
```

### **Parallel Ingestion**
Run multiple ingestors concurrently:
```python
from concurrent.futures import ThreadPoolExecutor

ingestors = [
    RedditIngestor(),
    NewsAPIIngestor(api_key="..."),
    GDELTIngestor()
]

with ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(ing.fetch) for ing in ingestors]
    all_articles = [f.result() for f in futures]
```

### **Error Handling**
```python
import logging

logger = logging.getLogger(__name__)

def safe_ingest(ingestor, **kwargs):
    try:
        return ingestor.fetch(**kwargs)
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error in {ingestor.__class__.__name__}: {e}")
        return []
    except Exception as e:
        logger.exception(f"Unexpected error in {ingestor.__class__.__name__}")
        return []
```

---

## 📊 Monitoring

Track ingestion metrics:
```python
from prometheus_client import Counter, Histogram

articles_fetched = Counter(
    'news_articles_fetched_total',
    'Total articles fetched',
    ['source']
)

fetch_duration = Histogram(
    'news_fetch_duration_seconds',
    'Time to fetch articles',
    ['source']
)

# In ingestor
def fetch(self, **kwargs):
    with fetch_duration.labels(source=self.__class__.__name__).time():
        articles = self._fetch_impl(**kwargs)
        articles_fetched.labels(source=self.__class__.__name__).inc(len(articles))
        return articles
```

---

## 🔮 Future Extensions

### Add More Sources
- Twitter/X API
- RSS feeds (generic)
- Google News
- Bloomberg API
- Financial Times

### Add Features
- Incremental fetching (only new articles)
- Deduplication at fetch time
- Language detection
- Content cleaning/normalization
- Image extraction

### Advanced Patterns
- Circuit breaker for failing sources
- Exponential backoff for retries
- Health checks for each ingestor
- A/B testing different sources

---

## 📖 Related Documentation

- `README.md` - Usage guide and API reference
- `INGESTION_QUICKSTART.md` - Getting started guide
- `/app/models/news.py` - Data models
- `/app/tests/test_ingestion.py` - Test examples

---

**Built with ❤️ for the ANIP project**

