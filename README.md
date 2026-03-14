# WNG Content Generator

AI-powered content generation platform with topic collection, quality scoring, and multi-platform publishing.

## 📁 Repository Structure

This workspace contains two independent applications:

- **wng-backend/** - FastAPI backend with Celery workers
- **wng-frontend/** - Next.js frontend application

## 🚀 Quick Start

### Local Development

**Backend:**
```bash
cd wng-backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
redis-server  # In another terminal
./start.sh
```
→ Backend: http://localhost:8000
→ API Docs: http://localhost:8000/docs

**Frontend:**
```bash
cd wng-frontend
npm install
cp .env.example .env.local
# Edit .env.local
npm run dev
```
→ Frontend: http://localhost:3000

## 🌐 Deployment

**Choose your guide:**

- 🚀 [**QUICK_DEPLOY.md**](./QUICK_DEPLOY.md) - Step-by-step checklist (30 min)
- 📖 [**DEPLOYMENT_GUIDE.md**](./DEPLOYMENT_GUIDE.md) - Complete detailed guide
- 📋 [**DEPLOYMENT_SUMMARY.md**](./DEPLOYMENT_SUMMARY.md) - Overview & architecture

### Free Hosting Setup
- Backend → Render.com (free)
- Frontend → Vercel (free)
- Database → Neon (already configured)
- Redis → Upstash (free)

**Total Cost: $0/month** 🎉

## 📚 Documentation

- [**QUICK_DEPLOY.md**](./QUICK_DEPLOY.md) - 30-minute deployment checklist ⚡
- [**DEPLOYMENT_GUIDE.md**](./DEPLOYMENT_GUIDE.md) - Complete detailed guide 📖
- [**DEPLOYMENT_SUMMARY.md**](./DEPLOYMENT_SUMMARY.md) - Overview & architecture 📋
- [**RENDER_SETUP.md**](./RENDER_SETUP.md) - Render.com service types explained 🔧
- [**RENDER_VS_UPSTASH.md**](./RENDER_VS_UPSTASH.md) - Why Upstash for Redis 💡
- [Backend README](./wng-backend/README.md) - Backend architecture
- [Frontend README](./wng-frontend/README.md) - Frontend features
- [Separation Summary](./SEPARATION_SUMMARY.md) - Repository separation details
- [Enum Migration](./wng-backend/ENUM_MIGRATION.md) - Database compatibility

## ✨ Features

- 📝 AI-powered content generation
- 🔍 Topic collection and screening
- 📊 Content quality scoring
- 🎯 SEO optimization
- 📱 Social media post generation
- 🔄 Background task processing
- 👥 User management
- 📈 Audit logging

## 🛠️ Tech Stack

**Backend:** FastAPI, SQLAlchemy, Celery, Redis, PostgreSQL
**Frontend:** Next.js 14, TypeScript, Tailwind CSS, Shadcn/ui

## 🗄️ Database

Uses existing Neon PostgreSQL database:
- Auto-creates tables on startup
- No migrations needed
- All existing data preserved

## 📝 Default Login

- Email: `admin@horizontherapy.example`
- Password: Check your database or `.env` file

## 🆘 Troubleshooting

**Backend won't start:**
- Check Redis is running: `redis-cli ping`
- Verify DATABASE_URL in `.env`

**Frontend can't connect:**
- Check `NEXT_PUBLIC_API_URL` in `.env.local`
- Ensure backend is running

**Database errors:**
- Use `postgresql+asyncpg://` format
- Verify Neon database is active

## 📄 License

[Your License]

---

**Ready to deploy?** → See [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)
