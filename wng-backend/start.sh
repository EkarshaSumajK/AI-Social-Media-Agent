#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

# ── Colors ──
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${GREEN}[✔]${NC} $*"; }
warn()  { echo -e "${YELLOW}[!]${NC} $*"; }
fail()  { echo -e "${RED}[✘]${NC} $*"; exit 1; }

# ── Preflight checks ──
command -v docker  >/dev/null 2>&1 || fail "docker is not installed"
command -v uv      >/dev/null 2>&1 || fail "uv is not installed (brew install uv)"

# ── 1. Create .env if missing ──
if [ ! -f .env ]; then
  if [ -f .env.minimal ]; then
    cp .env.minimal .env
    warn "Created .env from .env.minimal — add your OpenAI API key to enable content generation"
  elif [ -f .env.example ]; then
    cp .env.example .env
    warn "Created .env from .env.example — edit it with your API keys and settings"
  else
    fail ".env.minimal or .env.example not found; cannot create .env"
  fi
else
  info ".env already exists"
fi

# ── 2. Python venv + deps (uses uv.lock) ──
info "Syncing Python dependencies (uv sync)..."
uv sync

# ── 3. Start Redis (only) ──
info "Starting Redis container..."
docker compose up -d redis

# Wait for Redis to be ready
echo -n "Waiting for Redis"
for i in $(seq 1 10); do
  if docker compose exec -T redis redis-cli ping >/dev/null 2>&1; then
    echo ""
    info "Redis is ready"
    break
  fi
  echo -n "."
  sleep 1
  if [ "$i" -eq 10 ]; then
    echo ""
    fail "Redis did not become ready in 10 seconds"
  fi
done

# ── 4. Using Neon database ──
info "Using Neon database - connection will be tested when API starts..."

# ── 5. Start all services ──
info "Starting all services..."

# Trap to kill background processes on exit
cleanup() {
  echo ""
  warn "Shutting down..."
  kill 0 2>/dev/null
  exit 0
}
trap cleanup SIGINT SIGTERM

# API server
.venv/bin/python main.py &
API_PID=$!
info "API server started (PID $API_PID) → http://localhost:8000"

# Celery worker
.venv/bin/celery -A app.core.celery_app.celery_app worker --loglevel=info &
WORKER_PID=$!
info "Celery worker started (PID $WORKER_PID)"

# Celery beat
.venv/bin/celery -A app.core.celery_app.celery_app beat --loglevel=info &
BEAT_PID=$!
info "Celery beat started (PID $BEAT_PID)"

echo ""
info "Backend services running:"
info "  API: http://localhost:8000"
info "  API Docs: http://localhost:8000/docs"
info "  PostgreSQL: localhost:5432"
info "  Redis: localhost:6379"
echo ""
info "Press Ctrl+C to stop everything."
echo ""

# Wait for any process to exit
wait