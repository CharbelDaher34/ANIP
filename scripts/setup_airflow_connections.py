"""
Setup Airflow connections for Spark.
This script runs automatically on Airflow startup via entrypoint.
"""
import sys
from airflow import settings
from airflow.models import Connection


def create_spark_connection():
    """Create Spark connection in Airflow."""
    try:
        session = settings.Session()
        
        # Check if connection exists
        conn = session.query(Connection).filter(Connection.conn_id == 'spark_default').first()
        
        if conn is None:
            # Create new connection
            conn = Connection(
                conn_id='spark_default',
                conn_type='spark',
                host='spark://spark-master',
                port=7077,
                extra='{"queue": "root.default"}'
            )
            session.add(conn)
            session.commit()
            print("✅ Created Spark connection 'spark_default'")
            return True
        else:
            print("ℹ️  Spark connection 'spark_default' already exists")
            return True
        
    except Exception as e:
        print(f"⚠️  Warning: Could not setup Spark connection: {e}")
        print("   This is usually fine if Airflow is still initializing.")
        return False
    finally:
        try:
            session.close()
        except:
            pass


if __name__ == "__main__":
    success = create_spark_connection()
    sys.exit(0 if success else 1)

