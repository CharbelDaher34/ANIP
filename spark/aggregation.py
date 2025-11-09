"""
Spark job for aggregating news statistics.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, avg, length
import sys


def aggregate_stats(input_path: str, output_path: str):
    """
    Aggregate statistics from news data.
    
    Args:
        input_path: Path to input data (parquet)
        output_path: Path to output data (parquet)
    """
    spark = SparkSession.builder \
        .appName("news_aggregation") \
        .master("spark://spark-master:7077") \
        .getOrCreate()
    
    print(f"📥 Reading data from {input_path}")
    df = spark.read.parquet(input_path)
    
    # Aggregate by source
    stats = df.groupBy("source").agg(
        count("*").alias("article_count"),
        avg(length("content")).alias("avg_content_length")
    )
    
    stats.show()
    
    # Write output
    stats.write.mode("overwrite").parquet(output_path)
    print(f"💾 Saved to {output_path}")
    
    spark.stop()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: spark-submit aggregation.py <input_path> <output_path>")
        sys.exit(1)
    
    aggregate_stats(sys.argv[1], sys.argv[2])
