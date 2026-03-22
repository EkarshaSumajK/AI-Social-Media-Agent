#!/bin/bash
set -e

export PORT=${PORT:-8000}

echo "🚀 Starting services on port $PORT..."

cleanup() {
    echo "Shutting down..."
    kill "$CELERY_BEAT_PID" "$CELERY_WORKER_PID" 2>/dev/null || true
    wait "$CELERY_BEAT_PID" "$CELERY_WORKER_PID" 2>/dev/null || true
    exit 0
}
trap cleanup SIGTERM SIGINT

echo "⏰ Starting Celery Beat..."
celery -A app.core.celery_app.celery_app beat --loglevel=info &
CELERY_BEAT_PID=$!

echo "🔄 Starting Celery Worker (2 workers)..."
celery -A app.core.celery_app.celery_app worker --loglevel=info --concurrency=2 --max-tasks-per-child=50 &
CELERY_WORKER_PID=$!

sleep 2

echo "🌐 Starting FastAPI on port $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1
