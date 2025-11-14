"""
Spark ML Processing Pipeline for News Articles.

This module processes news articles using Apache Spark with ML models:
- Topic classification
- Sentiment analysis  
- Embedding generation
"""
from typing import List, Dict, Any

from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col
from pyspark.sql.types import StringType, FloatType, ArrayType, StructType, StructField, IntegerType, TimestampType
from anip.config import settings

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

# ==================== Import ML Models ====================

# Import models from anip package
from anip.ml.classification.inference import predict_topic
from anip.ml.sentiment.inference import predict_sentiment
from anip.ml.embedding import generate_embedding as embedding_model

# ==================== ML Model Wrapper Functions ====================

def classify_topic(title: str, content: str) -> str:
    """
    Classify article topic using ML model.
    Returns the top predicted topic.
    """
    text = f"{title} {content}"
    result = predict_topic(text, top_k=1)
    
    if result and "predictions" in result and len(result["predictions"]) > 0:
        topic = result["predictions"][0]["topic"]
        # Capitalize first letter to match expected format
        return topic.capitalize()
    
    return "World"

def analyze_sentiment(content: str) -> Dict[str, Any]:
    """
    Analyze sentiment of article content using ML model.
    Returns sentiment label and score.
    """
    result = predict_sentiment(content)
    
    if result:
        # Find the sentiment with highest score
        scores = {
            "positive": result.get("positive", 0.0),
            "neutral": result.get("neutral", 0.0),
            "negative": result.get("negative", 0.0)
        }
        sentiment = max(scores, key=scores.get)
        score = scores[sentiment]
        
        return {
            "sentiment": sentiment,
            "score": float(score)
        }
    
    return {
        "sentiment": "neutral",
        "score": 0.5
    }

def generate_embedding(title: str, content: str) -> List[float]:
    """
    Generate text embedding using ML model.
    Returns 384-dimensional embedding vector.
    """
    text = f"{title} {content}"
    embedding = embedding_model(text, dimension=384)
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
            return None  # Don't store invalid embeddings
        embedding = generate_embedding(title, content)
        # Validate embedding - don't store zero vectors
        if embedding and sum(abs(x) for x in embedding) > 0.001:  # Not all zeros
            return embedding
        return None
    except Exception as e:
        print(f"Error in embedding generation: {e}")
        return None  # Don't store failed embeddings

# ==================== Database Operations ====================

def save_articles_to_db_sqlalchemy(df):
    """
    Update existing articles with ML predictions using SQLAlchemy.
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
    
    # Use db_utils to update existing articles with ML predictions
    from anip.shared.utils.db_utils import update_articles_ml_predictions
    total_updated = update_articles_ml_predictions(articles_dicts)
    
    return total_updated

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
        
        # Use pydantic settings for database connection
        db_url = settings.database.url
        
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
        
        # Define explicit schema for Spark DataFrame
        schema = StructType([
            StructField("id", IntegerType(), False),
            StructField("title", StringType(), False),
            StructField("content", StringType(), False),
            StructField("source", StringType(), False),
            StructField("author", StringType(), True),
            StructField("url", StringType(), False),
            StructField("published_at", TimestampType(), True),
            StructField("language", StringType(), False),
            StructField("region", StringType(), True)
        ])
        
        # Convert rows to list of tuples matching the schema
        articles_data = []
        for row in rows:
            articles_data.append((
                int(row[0]),
                str(row[1] or ''),
                str(row[2] or ''),
                str(row[3] or ''),
                row[4],  # author can be None
                str(row[5] or ''),
                row[6],  # published_at datetime
                str(row[7] or 'en'),
                row[8]   # region can be None
            ))
        
        # Create Spark DataFrame with explicit schema
        df = spark.createDataFrame(articles_data, schema=schema)
            
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
    
    # Update existing articles with ML predictions
    print("\n💾 Updating articles with ML predictions in database...")
    total_updated = save_articles_to_db_sqlalchemy(df)
    
    print(f"\n✅ Successfully updated {total_updated} articles with ML predictions")
    
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

