#!/usr/bin/env bash
# Airflow entrypoint script that automatically sets up Spark connection

set -e

# Create necessary log directories (permissions already set on host volume)
echo "📁 Creating Airflow log directories..."
mkdir -p /opt/airflow/logs/scheduler /opt/airflow/logs/dag_processor_manager 2>/dev/null || true

# Function to setup Spark connection
setup_spark_connection() {
    echo "🔧 Setting up Spark connection..."
    
    # Wait for Airflow database to be ready
    echo "⏳ Waiting for Airflow database to be ready..."
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if airflow db check > /dev/null 2>&1; then
            echo "✅ Airflow database is ready"
            break
        fi
        attempt=$((attempt + 1))
        echo "   Attempt $attempt/$max_attempts..."
        sleep 2
    done
    
    if [ $attempt -eq $max_attempts ]; then
        echo "⚠️  Warning: Airflow database check timed out, but continuing..."
    fi
    
    # Wait a bit more for full initialization
    sleep 3
    
    # Setup Spark connection
    python /opt/anip/scripts/setup_airflow_connections.py || {
        echo "⚠️  Warning: Failed to setup Spark connection (may already exist)"
    }
}

# Setup Spark connection in background (non-blocking)
setup_spark_connection &

# Execute the original command
exec "$@"

