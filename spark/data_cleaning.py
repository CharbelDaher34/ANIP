"""
Spark job for cleaning news data.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, trim, lower
import sys


def clean_data(input_path: str, output_path: str):
    """
    Clean news data.
    
    Args:
        input_path: Path to input data (parquet)
        output_path: Path to output data (parquet)
    """
    spark = SparkSession.builder \
        .appName("news_data_cleaning") \
        .master("spark://spark-master:7077") \
        .getOrCreate()
    
    print(f"📥 Reading data from {input_path}")
    df = spark.read.parquet(input_path)
    
    print(f"📊 Initial count: {df.count()} articles")
    
    # Cleaning operations
    df_cleaned = df \
        .dropDuplicates(["url"]) \
        .filter(col("title").isNotNull()) \
        .filter(col("content").isNotNull()) \
        .withColumn("title", trim(col("title"))) \
        .withColumn("content", trim(col("content")))
    
    print(f"✅ Cleaned count: {df_cleaned.count()} articles")
    
    # Write output
    df_cleaned.write.mode("overwrite").parquet(output_path)
    print(f"💾 Saved to {output_path}")
    
    spark.stop()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: spark-submit data_cleaning.py <input_path> <output_path>")
        sys.exit(1)
    
    clean_data(sys.argv[1], sys.argv[2])
