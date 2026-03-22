# Wellnest Intelligent Marketing (WIM) - Backend

Backend API and worker services for Wellnest Intelligent Marketing (WIM) - a semi-automated trending mental-health content generation and publishing platform with mandatory human review.

## What's Included

- **FastAPI REST API** - Content management, authentication, approval workflows
- **Celery Workers** - Background tasks for trend collection, content generation, social posting
- **LangGraph Workflows** - AI-powered content generation pipeline
- **Database** - PostgreSQL with auto-created tables
- **Cache & Queue** - Redis for Celery and distributed locks

## Stack

- Python 3.11+
- FastAPI
- SQLAlchemy + PostgreSQL
- Redis + Celery
- LangGraph + LLM API
- WordPress REST API integration
- Social media APIs (Meta, LinkedIn, X)

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- `uv` package manager (install with `brew install uv` on macOS)

### Option 1: One-Command Setup (Recommended)

```bash
./start.sh
```

This automatically:
- Creates `.env` from `.env.minimal` (minimal working config)
- Sets up Python virtual environment with `uv`
- Starts PostgreSQL + Redis containers
- Auto-creates database tables on first start
- Launches API server on port 8000
- Launches Celery worker for background tasks
- Launches Celery beat scheduler for periodic tasks

**⚠️ Important:** You'll need to add your OpenAI API key to `.env` for content generation to work.

**Access points:**
- API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- PostgreSQL: localhost:5432
- Redis: localhost:6379

Press `Ctrl+C` to stop all services.

### Option 2: Manual Setup (Step by Step)

1. **Copy and configure environment:**
```bash
# Option 1: Minimal config (fastest way to start)
cp .env.minimal .env

# Option 2: Full config (all options)
cp .env.example .env

# Edit .env with your actual values (at minimum: OpenAI API key)
```

2. **Create Python virtual environment:**
```bash
# Using uv (recommended)
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv sync

# OR using standard Python
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .
```

3. **Start database services:**
```bash
docker compose up -d postgres redis
```

4. **Database auto-initializes on first start:**
```bash
# No manual setup needed - tables are created automatically
python main.py
```

5. **Start the API server:**
```bash
python main.py
```
API will be available at http://localhost:8000

6. **In a new terminal, start Celery worker:**
```bash
source .venv/bin/activate
celery -A app.core.celery_app.celery_app worker --loglevel=info
```

7. **In another terminal, start Celery beat scheduler:**
```bash
source .venv/bin/activate
celery -A app.core.celery_app.celery_app beat --loglevel=info
```

### Option 3: Full Docker Setup

```bash
docker compose up --build
```

This starts all services in containers:
- API server (port 8000)
- Celery worker
- Celery beat scheduler  
- PostgreSQL database
- Redis cache

## API Endpoints

- `POST /api/v1/auth/login` - Authentication
- `GET /api/v1/topics` - List collected trends
- `POST /api/v1/topics/collect` - Trigger trend collection
- `POST /api/v1/topics/{topic_id}/generate-draft` - Generate article draft
- `GET /api/v1/drafts` - List drafts pending review
- `PUT /api/v1/drafts/{article_id}` - Update draft
- `POST /api/v1/drafts/{article_id}/approve` - Approve draft
- `POST /api/v1/drafts/{article_id}/reject` - Reject draft
- `POST /api/v1/drafts/{article_id}/publish` - Publish to WordPress
- `POST /api/v1/drafts/{article_id}/social/publish` - Post to social media
- `GET /api/v1/audit` - View audit logs

API docs available at: `http://localhost:8000/docs`

## Environment Configuration

### Required Variables (Minimum to Start)

The app needs these variables to start:

```bash
# Database (auto-configured for local development)
DATABASE_URL_DASHBOARD=postgresql://wng_user:wng_password@localhost:5432/wng_content

# Redis (auto-configured for local development)  
REDIS_URL=redis://localhost:6379/0

# JWT Security (CHANGE THIS!)
JWT_SECRET_KEY=your-very-long-random-secret-key

# Admin Login (CHANGE THESE!)
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=changeme123

# OpenAI API (Required for content generation)
LLM_API_KEY=your-openai-api-key
```

### Quick Setup for Testing

1. **Copy minimal config:**
```bash
cp .env.minimal .env
```

2. **Add your OpenAI API key:**
   - Get key from: https://platform.openai.com/api-keys
   - Edit `.env` and replace `your-openai-api-key-here`

3. **Change admin credentials:**
   - Edit `ADMIN_EMAIL` and `ADMIN_PASSWORD` in `.env`

### Optional Integrations

These are optional and can be added later:

- **WordPress** - For publishing articles
- **Social Media APIs** - For social posting (Meta, LinkedIn, X)
- **News APIs** - For trend collection
- **Email/Notifications** - For reviewer alerts
- **Cloudinary** - For image handling

## Stopping Services

**If using start.sh:** Press `Ctrl+C` to stop all services

**If running manually:** Stop each terminal process with `Ctrl+C`, then:
```bash
docker compose down  # Stop PostgreSQL and Redis
```

## Troubleshooting

**Common issues:**

1. **Port already in use:**
   ```bash
   # Check what's using port 8000
   lsof -i :8000
   # Kill the process or change the port in main.py
   ```

2. **PostgreSQL connection failed:**
   ```bash
   # Check if PostgreSQL is running
   docker compose ps
   # Restart if needed
   docker compose restart postgres
   ```

3. **Redis connection failed:**
   ```bash
   # Check Redis status
   docker compose ps
   # Restart if needed  
   docker compose restart redis
   ```

4. **Database reset (if needed):**
   ```bash
   # Reset database (WARNING: deletes all data)
   docker compose down -v
   docker compose up -d postgres redis
   # Tables will be recreated on next API start
   ```

5. **Import errors:**
   ```bash
   # Make sure virtual environment is activated
   source .venv/bin/activate
   # Reinstall dependencies
   uv sync
   ```

## Database Migrations

## Docker Deployment

```bash
docker compose up --build
```

Services:
- `backend` - FastAPI API (port 8000)
- `worker` - Celery worker
- `beat` - Celery beat scheduler
- `postgres` - PostgreSQL database
- `redis` - Redis cache/queue

## Hard Guardrails

- No auto-publish path exists
- Publishing requires explicit approval (`approved_by` + `approved_at`)
- Near-duplicate detection blocks similar content
- Mandatory disclaimer appended to all content
- All actions logged in audit table

## Project Structure

```
app/
  api/            # FastAPI routes and dependencies
  core/           # Config, database, security, Celery
  models/         # SQLAlchemy database models
  schemas/        # Pydantic API schemas
  services/       # Business logic services
  workflows/      # LangGraph content generation
  workers/        # Celery background tasks
prompts/          # LLM prompt templates organized by feature
scripts/          # Utility scripts
tests/            # Test suite
```

## License

Proprietary
