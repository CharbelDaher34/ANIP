#!/bin/bash
# Fix volume permissions for Docker containers
# This script ensures all volume directories have correct ownership

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🔧 Fixing volume permissions..."

# Create directories if they don't exist
mkdir -p "$PROJECT_ROOT/volumes/airflow/logs"
mkdir -p "$PROJECT_ROOT/volumes/airflow/plugins"
mkdir -p "$PROJECT_ROOT/volumes/mlruns"
mkdir -p "$PROJECT_ROOT/volumes/postgres"

# Airflow needs UID 50000 (airflow user)
echo "  📁 Setting Airflow volumes (UID 50000)..."
sudo chown -R 50000:0 "$PROJECT_ROOT/volumes/airflow/"

# MLflow runs as root, but needs to be writable by Spark (UID 185) and Airflow (UID 50000)
echo "  📁 Setting MLruns volume (world-writable)..."
sudo chmod -R 777 "$PROJECT_ROOT/volumes/mlruns/"

# Postgres manages its own permissions
echo "  📁 Postgres volume (managed by container)..."

echo "✅ Volume permissions fixed!"
echo ""
echo "Volume ownership:"
ls -lh "$PROJECT_ROOT/volumes/"

