#!/bin/bash
set -e

# Use Railway's PORT or default to 8000
export PORT=${PORT:-8000}

echo "🚀 Starting services on port $PORT..."

# Start Celery Beat in background
echo "⏰ Starting Celery Beat..."
celery -A app.core.celery_app.celery_app beat --loglevel=info &

# Start Celery Worker in background
echo "🔄 Starting Celery Worker..."
celery -A app.core.celery_app.celery_app worker --loglevel=info &

# Start FastAPI in foreground (keeps container alive)
echo "🌐 Starting FastAPI on port $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
