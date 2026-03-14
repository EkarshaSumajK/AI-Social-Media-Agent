#!/bin/bash
set -e

# Use Railway's PORT or default to 8000
export PORT=${PORT:-8000}

echo "🚀 Starting services on port $PORT..."

# Start Celery Beat in background (lightweight scheduler)
echo "⏰ Starting Celery Beat..."
celery -A app.core.celery_app.celery_app beat --loglevel=info &

# Start Celery Worker with limited concurrency to save memory
echo "🔄 Starting Celery Worker (2 workers)..."
celery -A app.core.celery_app.celery_app worker --loglevel=info --concurrency=2 --max-tasks-per-child=50 &

# Give workers time to start
sleep 2

# Start FastAPI in foreground (keeps container alive)
echo "🌐 Starting FastAPI on port $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1
