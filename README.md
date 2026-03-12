# WNG Content Platform

Semi-automated trending mental-health content generation and publishing platform with mandatory human review.

## What This Implements

- Daily trend collection from RSS + News API (scheduler-driven via Celery Beat)
- LangGraph sequential content workflow:
  1. Key points extraction
  2. Unique rewrite
  3. Context explanation
  4. Mental health implications
  5. Professional insight
  6. Service-as-solution mapping
  7. CTA generation
  8. SEO metadata generation
  9. Social post generation
- Duplicate detection with embeddings similarity checks
- Compliance insertion:
  - Source citation
  - Mandatory disclaimer: `This content is for educational purposes only`
- Draft-only storage until explicit human approval
- Reviewer dashboard (Next.js + Tailwind + TipTap)
- WordPress publishing (REST API) only after approval
- Social posting workers (Meta / LinkedIn / X) after publish
- Reviewer notification (Telegram or SMTP)
- Audit logs for approvals, publishing, and social outcomes
- Redis-backed queues and distributed locks

## Hard Guardrails Enforced

- No auto-publish path exists in backend code
- Publish endpoint rejects non-approved drafts
- Publishing requires `approved_by` and `approved_at`
- Near-duplicate topics are blocked from draft generation
- Disclaimer is always appended if missing

## Stack

- Frontend: Next.js, TailwindCSS, TipTap
- Backend: FastAPI, SQLAlchemy, PostgreSQL
- Queue + Locks: Redis, Celery
- Workflow: LangGraph + LLM API
- CMS: WordPress REST API
- Monitoring: Sentry + audit log table

## Repo Structure

```text
backend/
  app/
    api/            # FastAPI routes
    core/           # config, DB, security, celery
    models/         # SQLAlchemy entities
    schemas/        # API DTOs
    services/       # trend collector, pipeline, cms, social, notifications
    workflows/      # LangGraph content graph
    workers/        # Celery tasks
  scripts/
  tests/
frontend/
  app/
  components/
  lib/
infra/sql/
```

## Quick Start (macOS / Linux)

One command to set up and run everything:

```bash
./start.sh
```

This will:
- Create `.env` from `.env.example` (if missing)
- Create a Python 3.11 venv and install all dependencies via `uv`
- Start Postgres + Redis via Docker
- Run Alembic migrations
- Install frontend npm packages
- Launch the API (`localhost:8000`), Celery worker, Celery beat, and frontend (`localhost:3000`)

Press `Ctrl+C` to stop all services.

> **Prerequisites:** `docker`, `uv`, `node`, and `npm` must be installed.

---

## Local Setup (Manual Steps)

### 1. Install backend dependencies

**macOS / Linux:**

```bash
.venv/bin/python -m pip install -e .
```

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
```

### 2. Copy env file

**macOS / Linux:**

```bash
cp .env.example .env
```

**Windows (PowerShell):**

```powershell
Copy-Item .env.example .env
```

### 3. Start Postgres + Redis (Docker)

```bash
docker compose up -d postgres redis
```

### 4. Apply migrations

**macOS / Linux:**

```bash
.venv/bin/python -m alembic upgrade head
```

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

### 5. Run API

**macOS / Linux:**

```bash
.venv/bin/python main.py
```

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\python.exe main.py
```

### 6. Run Celery worker

**macOS / Linux:**

```bash
.venv/bin/celery -A app.core.celery_app.celery_app worker --loglevel=info
```

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\celery.exe -A app.core.celery_app.celery_app worker --loglevel=info
```

### 7. Run Celery beat scheduler

**macOS / Linux:**

```bash
.venv/bin/celery -A app.core.celery_app.celery_app beat --loglevel=info
```

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\celery.exe -A app.core.celery_app.celery_app beat --loglevel=info
```

### 8. Run frontend

```bash
cd frontend
npm install
npm run dev
```

## Reviewer Login

- Email: value from `ADMIN_EMAIL` in `.env`
- Password: value from `ADMIN_PASSWORD` in `.env`

The admin user is auto-seeded on API startup using those environment values.

## API Highlights

- `POST /api/v1/auth/login`
- `GET /api/v1/topics`
- `POST /api/v1/topics/collect`
- `POST /api/v1/topics/{topic_id}/generate-draft`
- `GET /api/v1/drafts`
- `PUT /api/v1/drafts/{article_id}`
- `POST /api/v1/drafts/{article_id}/approve`
- `POST /api/v1/drafts/{article_id}/reject`
- `POST /api/v1/drafts/{article_id}/publish`
- `POST /api/v1/drafts/{article_id}/social/publish`
- `GET /api/v1/audit`

## Alembic Commands

**macOS / Linux:**

```bash
.venv/bin/python -m alembic upgrade head
.venv/bin/python -m alembic downgrade -1
.venv/bin/python -m alembic revision --autogenerate -m "describe change"
```

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic downgrade -1
.\.venv\Scripts\python.exe -m alembic revision --autogenerate -m "describe change"
```

## Full Docker Stack

```bash
docker compose up --build
```

This starts:
- `postgres`
- `redis`
- `backend`
- `worker`
- `beat`
- `frontend`

## Notes

- Instagram publishing requires `INSTAGRAM_IMAGE_URL` for media creation.
- X and LinkedIn posting require valid production tokens/scopes.
- WordPress publishing requires an application password.
- Schema management is Alembic-first; no runtime `create_all` table creation is used.
