"""
Spark ML Processing Pipeline for News Articles.

This module processes news articles using Apache Spark with ML models:
- Topic classification
- Sentiment analysis  
- Embedding generation
"""
import os
import sys
import random
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, '/opt/anip')

from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col
from pyspark.sql.types import StringType, FloatType, ArrayType, StructType, StructField

# ==================== Spark Session ====================

def create_spark_session():
    """Create and configure Spark session."""
    return SparkSession.builder \
        .appName("ANIP-ML-Processing") \
        .master("spark://spark-master:7077") \
        .config("spark.executor.memory", "2g") \
        .config("spark.driver.memory", "2g") \
        .config("spark.sql.execution.arrow.pyspark.enabled", "false") \
        .getOrCreate()

# ==================== ML Models (Simplified) ====================

# Topic categories
TOPICS = [
    "Politics", "Business", "Technology", "Sports", "Entertainment",
    "Health", "Science", "Environment", "Education", "World"
]

def classify_topic(title: str, content: str) -> str:
    """
    Classify article topic based on keywords.
    Simplified keyword-based classification.
    """
    text = (title + " " + content).lower()
    
    # Keyword-based classification
    if any(word in text for word in ["election", "government", "politics", "congress", "senate"]):
        return "Politics"
    elif any(word in text for word in ["stock", "market", "economy", "business", "trade", "company"]):
        return "Business"
    elif any(word in text for word in ["tech", "ai", "software", "digital", "computer", "internet"]):
        return "Technology"
    elif any(word in text for word in ["game", "player", "team", "sport", "championship"]):
        return "Sports"
    elif any(word in text for word in ["movie", "music", "celebrity", "entertainment", "film"]):
        return "Entertainment"
    elif any(word in text for word in ["health", "medical", "disease", "hospital", "doctor"]):
        return "Health"
    elif any(word in text for word in ["science", "research", "study", "discovery"]):
        return "Science"
    elif any(word in text for word in ["climate", "environment", "pollution", "green"]):
        return "Environment"
    elif any(word in text for word in ["school", "education", "university", "student"]):
        return "Education"
    else:
        return "World"

def analyze_sentiment(content: str) -> Dict[str, Any]:
    """
    Analyze sentiment of article content.
    Simplified keyword-based sentiment analysis.
    """
    text = content.lower()
    
    # Positive keywords
    positive_words = ["good", "great", "excellent", "positive", "success", "win", "best", "happy"]
    # Negative keywords
    negative_words = ["bad", "terrible", "negative", "fail", "worst", "sad", "crisis"]
    
    pos_count = sum(1 for word in positive_words if word in text)
    neg_count = sum(1 for word in negative_words if word in text)
    
    if pos_count > neg_count:
        sentiment = "positive"
        score = min(0.5 + (pos_count * 0.1), 1.0)
    elif neg_count > pos_count:
        sentiment = "negative"
        score = max(0.5 - (neg_count * 0.1), 0.0)
    else:
        sentiment = "neutral"
        score = 0.5
    
    return {
        "sentiment": sentiment,
        "score": float(score)
    }

def generate_embedding(title: str, content: str) -> List[float]:
    """
    Generate simple text embedding.
    Simplified version - in production would use actual embedding model.
    """
    # Simple hash-based embedding (512 dimensions)
    text = title + " " + content
    embedding = []
    
    for i in range(512):
        # Simple deterministic "embedding" based on text hash
        hash_val = hash(text + str(i)) % 1000
        embedding.append(hash_val / 1000.0)
    
    return embedding

# ==================== Spark UDFs ====================

def classify_topic_udf(title: str, content: str) -> str:
    """UDF wrapper for topic classification."""
    try:
        if not title or not content:
            return "World"
        return classify_topic(title, content)
    except Exception as e:
        print(f"Error in topic classification: {e}")
        return "World"

def analyze_sentiment_udf(content: str) -> Dict[str, Any]:
    """UDF wrapper for sentiment analysis."""
    try:
        if not content:
            return {"sentiment": "neutral", "score": 0.5}
        return analyze_sentiment(content)
    except Exception as e:
        print(f"Error in sentiment analysis: {e}")
        return {"sentiment": "neutral", "score": 0.5}

def generate_embedding_udf(title: str, content: str) -> List[float]:
    """UDF wrapper for embedding generation."""
    try:
        if not title or not content:
            return [0.0] * 512
        return generate_embedding(title, content)
    except Exception as e:
        print(f"Error in embedding generation: {e}")
        return [0.0] * 512

# ==================== Database Operations ====================

def save_articles_to_db_sqlalchemy(df):
    """
    Save processed articles back to database using SQLAlchemy.
    Converts Spark DataFrame to Python dictionaries and uses db_utils.
    """
    # Collect data to driver (for small to medium datasets)
    articles_list = df.collect()
    
    # Convert to list of dictionaries
    articles_dicts = []
    for row in articles_list:
        article_dict = {
            'id': row.id,
            'title': row.title,
            'content': row.content,
            'source': row.source,
            'author': row.author,
            'url': row.url,
            'published_at': row.published_at,
            'language': row.language,
            'region': row.region,
            'topic': row.topic,
            'sentiment': row.sentiment,
            'sentiment_score': float(row.sentiment_score) if row.sentiment_score else None,
            'embedding': list(row.embedding) if row.embedding else None
        }
        articles_dicts.append(article_dict)
    
    # Use db_utils to save
    from shared.utils.db_utils import save_articles_batch
    total_saved = save_articles_batch(articles_dicts)
    
    return total_saved

# ==================== Main Processing Pipeline ====================

def load_from_database_and_process():
    """
    Load articles from database, process with ML using Spark, and save back using SQLAlchemy.
    Processes articles that don't have ML predictions yet.
    """
    spark = create_spark_session()
    
    print("📖 Reading articles from database using SQLAlchemy...")
    
    # Use SQLAlchemy to read from database (no JDBC driver needed)
    try:
        from sqlalchemy import create_engine, text
        
        # Create database connection string
        postgres_user = os.getenv('POSTGRES_USER')
        postgres_password = os.getenv('POSTGRES_PASSWORD')
        postgres_host = os.getenv('POSTGRES_HOST', 'postgres')
        postgres_port = os.getenv('POSTGRES_PORT', '5432')
        postgres_db = os.getenv('POSTGRES_DB', 'anip')
        
        if not postgres_user or not postgres_password:
            raise ValueError("POSTGRES_USER and POSTGRES_PASSWORD environment variables are required")
        
        db_url = f"postgresql+psycopg2://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"
        
        # Create engine with connection pooling for better performance
        engine = create_engine(
            db_url,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True
        )
        
        # Read articles that need ML processing
        query = text("""
            SELECT id, title, content, source, author, url, published_at, language, region
            FROM newsarticle
            WHERE topic IS NULL OR sentiment IS NULL OR embedding IS NULL
        """)
        
        with engine.connect() as conn:
            result = conn.execute(query)
            rows = result.fetchall()
        
        if not rows:
            print("✅ No articles to process - all articles have ML predictions")
            spark.stop()
            return
        
        print(f"📊 Found {len(rows)} articles to process")
        
        # Convert rows to list of dictionaries for Spark DataFrame
        articles_data = []
        for row in rows:
            articles_data.append({
                'id': row[0],
                'title': row[1] or '',
                'content': row[2] or '',
                'source': row[3] or '',
                'author': row[4],
                'url': row[5] or '',
                'published_at': row[6],
                'language': row[7] or 'en',
                'region': row[8]
            })
        
        # Create Spark DataFrame from list of dictionaries
        df = spark.createDataFrame(articles_data)
            
    except Exception as e:
        print(f"❌ Error reading from database: {e}")
        import traceback
        traceback.print_exc()
        spark.stop()
        return
    
    # Register UDFs
    classify_udf_func = udf(classify_topic_udf, StringType())
    sentiment_schema = StructType([
        StructField("sentiment", StringType()),
        StructField("score", FloatType())
    ])
    sentiment_udf_func = udf(analyze_sentiment_udf, sentiment_schema)
    embedding_udf_func = udf(generate_embedding_udf, ArrayType(FloatType()))
    
    # Apply ML transformations
    print("🔬 Applying ML transformations...")
    df = df.withColumn("topic", classify_udf_func(col("title"), col("content")))
    df = df.withColumn("sentiment_result", sentiment_udf_func(col("content")))
    df = df.withColumn("sentiment", col("sentiment_result.sentiment"))
    df = df.withColumn("sentiment_score", col("sentiment_result.score"))
    df = df.drop("sentiment_result")
    df = df.withColumn("embedding", embedding_udf_func(col("title"), col("content")))
    
    # Show sample
    print("\n✅ Sample processed articles:")
    df.select("title", "topic", "sentiment", "sentiment_score").show(5, truncate=50)
    
    # Show statistics
    print("\n📊 Processing Statistics:")
    print("\nBy Topic:")
    df.groupBy("topic").count().orderBy(col("count").desc()).show(10)
    print("\nBy Sentiment:")
    df.groupBy("sentiment").count().show()
    
    # Save back to database using SQLAlchemy
    print("\n💾 Saving ML predictions to database using SQLAlchemy...")
    total_saved = save_articles_to_db_sqlalchemy(df)
    
    print(f"\n✅ Successfully processed and saved {total_saved} articles")
    
    spark.stop()

# ==================== Entry Point ====================

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Starting Spark ML Processing Pipeline")
    print("=" * 60)
    
    load_from_database_and_process()
    
    print("=" * 60)
    print("✅ Spark ML Processing Complete")
    print("=" * 60)

