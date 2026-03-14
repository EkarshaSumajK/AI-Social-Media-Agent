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
command -v node    >/dev/null 2>&1 || fail "node is not installed"
command -v npm     >/dev/null 2>&1 || fail "npm is not installed"

# ── 1. Create .env.local if missing ──
if [ ! -f .env.local ]; then
  if [ -f .env.example ]; then
    cp .env.example .env.local
    warn "Created .env.local from .env.example — edit it with your backend API URL if needed"
  else
    fail ".env.example not found; cannot create .env.local"
  fi
else
  info ".env.local already exists"
fi

# ── 2. Install dependencies ──
info "Installing frontend dependencies..."
npm install

# ── 3. Start development server ──
info "Starting Next.js development server..."
npm run dev