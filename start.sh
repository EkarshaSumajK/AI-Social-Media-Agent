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
command -v node    >/dev/null 2>&1 || fail "node is not installed"
command -v npm     >/dev/null 2>&1 || fail "npm is not installed"

# ── 1. Create .env if missing ──
if [ ! -f .env ]; then
  if [ -f .env.example ]; then
    cp .env.example .env
    warn "Created .env from .env.example — edit it with your secrets before running again if needed"
  else
    fail ".env.example not found; cannot create .env"
  fi
else
  info ".env already exists"
fi

# ── 2. Python venv + deps (uses uv.lock) ──
info "Syncing Python dependencies (uv sync)..."
uv sync

# ── 3. Start Postgres + Redis ──
info "Starting Postgres and Redis containers..."
docker compose up -d postgres redis

# Wait for Postgres to be ready
echo -n "Waiting for Postgres"
for i in $(seq 1 30); do
  if docker compose exec -T postgres pg_isready -U postgres >/dev/null 2>&1; then
    echo ""
    info "Postgres is ready"
    break
  fi
  echo -n "."
  sleep 1
  if [ "$i" -eq 30 ]; then
    echo ""
    fail "Postgres did not become ready in 30 seconds"
  fi
done

# ── 4. Run migrations ──
info "Running Alembic migrations..."
.venv/bin/python -m alembic upgrade head

# ── 5. Install frontend deps ──
info "Installing frontend dependencies..."
(cd frontend && npm install)

# ── 6. Start all services ──
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
PYTHONPATH="$ROOT_DIR/backend" .venv/bin/celery -A app.core.celery_app.celery_app worker --loglevel=info &
WORKER_PID=$!
info "Celery worker started (PID $WORKER_PID)"

# Celery beat
PYTHONPATH="$ROOT_DIR/backend" .venv/bin/celery -A app.core.celery_app.celery_app beat --loglevel=info &
BEAT_PID=$!
info "Celery beat started (PID $BEAT_PID)"

# Frontend dev server
(cd frontend && npm run dev) &
FRONTEND_PID=$!
info "Frontend dev server started (PID $FRONTEND_PID) → http://localhost:3000"

echo ""
info "All services running. Press Ctrl+C to stop everything."
echo ""

# Wait for any process to exit
wait
