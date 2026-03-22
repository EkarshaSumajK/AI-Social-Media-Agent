# WIM Backend - Deployment Guide

## Free Deployment Options

### Option 1: Render.com (Recommended)

1. **Push code to GitHub**
2. **Connect to Render:**
   - Go to [render.com](https://render.com)
   - Connect your GitHub account
   - Import this repository

3. **Use the render.yaml config:**
   - Render will automatically detect the `render.yaml` file
   - This creates: API service, worker, beat scheduler, PostgreSQL, Redis

4. **Set environment variables:**
   ```
   SECRET_KEY=your-secret-key-here
   LLM_API_KEY=your-llm-api-key
   WORDPRESS_URL=https://your-site.com
   WORDPRESS_USERNAME=your-username
   WORDPRESS_APP_PASSWORD=your-app-password
   ADMIN_EMAIL=admin@example.com
   ADMIN_PASSWORD=secure-password
   ```

5. **Deploy:**
   - Render will build and deploy automatically
   - Database migrations run automatically

**Free tier limits:**
- 750 hours/month
- Services sleep after 15 min inactivity
- PostgreSQL expires after 90 days (upgrade to paid or use external DB)

### Option 2: Railway.app

1. **Push code to GitHub**
2. **Connect to Railway:**
   - Go to [railway.app](https://railway.app)
   - Connect GitHub and import repo

3. **Add services:**
   - Web service (FastAPI API)
   - Worker service (Celery worker)
   - Worker service (Celery beat)
   - PostgreSQL database
   - Redis database

4. **Configure each service:**
   
   **API Service:**
   ```
   Build Command: pip install -e .
   Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
   
   **Worker Service:**
   ```
   Build Command: pip install -e .
   Start Command: celery -A app.core.celery_app.celery_app worker --loglevel=info
   ```
   
   **Beat Service:**
   ```
   Build Command: pip install -e .
   Start Command: celery -A app.core.celery_app.celery_app beat --loglevel=info
   ```

5. **Set environment variables** (same as Render)

**Free tier:** $5 credit/month (usually sufficient for hobby projects)

### Option 3: Fly.io

1. **Install flyctl:**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Login and create app:**
   ```bash
   fly auth login
   fly launch
   ```

3. **Configure fly.toml** (generated automatically, customize as needed)

4. **Add PostgreSQL and Redis:**
   ```bash
   fly postgres create
   fly redis create
   ```

5. **Set secrets:**
   ```bash
   fly secrets set SECRET_KEY=your-secret-key
   fly secrets set LLM_API_KEY=your-api-key
   # ... other secrets
   ```

6. **Deploy:**
   ```bash
   fly deploy
   ```

### Option 4: Split Services (Mix & Match)

**API:** Render Web Service
**Database:** Supabase (free PostgreSQL) or Neon
**Redis:** Upstash (free tier)
**Workers:** Render Background Workers

## Environment Variables Reference

```bash
# Required
DATABASE_URL=postgresql://user:pass@host:port/db
REDIS_URL=redis://host:port/db
SECRET_KEY=your-secret-key
LLM_API_KEY=your-llm-api-key
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=secure-password

# WordPress (if using)
WORDPRESS_URL=https://your-site.com
WORDPRESS_USERNAME=username
WORDPRESS_APP_PASSWORD=app-password

# Social Media (optional)
META_ACCESS_TOKEN=
LINKEDIN_ACCESS_TOKEN=
X_API_KEY=

# Notifications (optional)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

## Database Migrations

Migrations run automatically on deployment. To run manually:

```bash
python -m alembic upgrade head
```

## Health Checks

- API health: `GET /health`
- Database: `GET /health/db`
- Redis: `GET /health/redis`

## Monitoring

- Check logs in your platform's dashboard
- Monitor API response times
- Watch Celery task queues
- Set up alerts for failed tasks

## Scaling

**Render/Railway:**
- Upgrade to paid plans for more resources
- Add more worker instances
- Use external managed databases

**Fly.io:**
- Scale with `fly scale count 2`
- Add more regions with `fly regions add`

## Troubleshooting

**Common issues:**
1. **Cold starts** - Services sleep on free tiers
2. **Database connections** - Check connection limits
3. **Memory limits** - Optimize code or upgrade plan
4. **Worker timeouts** - Increase timeout settings

**Debug commands:**
```bash
# Check service status
curl https://your-api.com/health

# View logs (platform-specific)
render logs
railway logs
fly logs
```