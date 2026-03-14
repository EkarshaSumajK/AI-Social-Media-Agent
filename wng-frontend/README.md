# WNG Content Platform - Frontend

Reviewer dashboard for the WNG Content Platform - a Next.js application for reviewing, editing, and approving AI-generated mental health content before publication.

## What's Included

- **Content Review Dashboard** - Review and edit AI-generated drafts
- **Approval Workflow** - Approve or reject content with comments
- **Rich Text Editor** - TipTap editor for content refinement
- **Audit Logs** - Track all content actions and changes
- **Campaign Management** - Organize content by campaigns
- **Competitor Analysis** - Monitor competitor content
- **Social Media Management** - Schedule and track social posts

## Stack

- Next.js 14+ (App Router)
- TypeScript
- TailwindCSS
- TipTap (Rich Text Editor)
- Shadcn/ui components
- React Query for data fetching

## Quick Start

### Prerequisites
- Node.js 18+ (recommend using Node 20)
- npm or yarn package manager

### Option 1: One-Command Setup (Recommended)

```bash
./start.sh
```

This automatically:
- Creates `.env.local` from `.env.example`
- Installs npm dependencies
- Starts Next.js development server on port 3000

**Access:** http://localhost:3000

Press `Ctrl+C` to stop the development server.

### Option 2: Manual Setup (Step by Step)

1. **Install dependencies:**
```bash
npm install
# OR
yarn install
```

2. **Copy and configure environment:**
```bash
cp .env.example .env.local
```

3. **Edit `.env.local` with your backend API URL:**
```bash
# For local development (if backend is running locally)
NEXT_PUBLIC_API_URL=http://localhost:8000

# For production (replace with your deployed backend URL)
NEXT_PUBLIC_API_URL=https://your-backend-api.com
```

4. **Start development server:**
```bash
npm run dev
# OR
yarn dev
```

Frontend will be available at http://localhost:3000

### Option 3: Production Build

```bash
# Build for production
npm run build

# Start production server
npm start
```

### Option 4: Docker Setup

```bash
# Build and run with Docker
docker compose up --build
```

## Environment Variables

See `.env.frontend.example` for configuration options.

Key variables:
- `NEXT_PUBLIC_API_URL` - Backend API endpoint (default: http://localhost:8000)

## Default Login

Use the credentials configured in the backend:
- Email: Value from backend's `ADMIN_EMAIL`
- Password: Value from backend's `ADMIN_PASSWORD`

## Available Scripts

```bash
# Development server
npm run dev

# Production build
npm run build

# Start production server
npm start

# Lint code
npm run lint

# Type check
npm run type-check
```

## Features

### Content Review
- View all pending drafts
- Edit content with rich text editor
- Preview formatted content
- Approve or reject with comments

### Article Pipeline
- Track content generation status
- Monitor quality scores
- View duplicate detection results
- See compliance checks

### Campaign Management
- Create and manage campaigns
- Organize content by campaign
- Track campaign performance

### Competitor Analysis
- Monitor competitor content
- Analyze competitor strategies
- Track trending topics

### Social Media
- Schedule posts across platforms
- Track engagement metrics
- Manage social accounts

### Audit Logs
- View all system actions
- Track user activities
- Monitor content lifecycle

## Project Structure

```
app/
  dashboard/              # Dashboard pages
    article-pipeline/     # Content generation pipeline
    audience-content/     # Audience-specific content
    audit/                # Audit logs
    campaigns/            # Campaign management
    competitors/          # Competitor analysis
    drafts/               # Draft review
    social/               # Social media management
  api/                    # API route handlers (if any)
components/               # Reusable React components
  ui/                     # Shadcn/ui components
hooks/                    # Custom React hooks
lib/                      # Utility functions
public/                   # Static assets
```

## Deployment

### Vercel (Recommended)

1. Push code to GitHub
2. Import project in Vercel
3. Set environment variables
4. Deploy

### Docker

```bash
docker build -t wng-frontend .
docker run -p 3000:3000 -e NEXT_PUBLIC_API_URL=https://your-api.com wng-frontend
```

### Other Platforms

- **Netlify** - Connect GitHub repo and deploy
- **Cloudflare Pages** - Connect GitHub repo and deploy

## Development Notes

- Uses Next.js App Router (not Pages Router)
- TypeScript strict mode enabled
- TailwindCSS for styling
- Shadcn/ui for component library
- TipTap for rich text editing

## License

Proprietary
## Connecting to Backend

The frontend needs to connect to the backend API. Configure this in `.env.local`:

**For local development:**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**For production:**
```bash
NEXT_PUBLIC_API_URL=https://your-deployed-backend.com
```

**Important:** Make sure your backend is running before starting the frontend!

## Default Login Credentials

Use the same credentials configured in your backend:
- **Email:** Value from backend's `ADMIN_EMAIL` environment variable
- **Password:** Value from backend's `ADMIN_PASSWORD` environment variable

## Stopping the Application

Press `Ctrl+C` in the terminal to stop the development server.

## Troubleshooting

**Common issues:**

1. **Port 3000 already in use:**
   ```bash
   # Check what's using port 3000
   lsof -i :3000
   # Kill the process or Next.js will suggest an alternative port
   ```

2. **API connection failed:**
   - Check that `NEXT_PUBLIC_API_URL` in `.env.local` is correct
   - Verify the backend is running and accessible
   - Check browser console for CORS errors

3. **Build errors:**
   ```bash
   # Clear Next.js cache
   rm -rf .next
   # Reinstall dependencies
   rm -rf node_modules package-lock.json
   npm install
   ```

4. **TypeScript errors:**
   ```bash
   # Run type checking
   npm run type-check
   # Fix any TypeScript errors before building
   ```

5. **Login not working:**
   - Verify backend is running and accessible
   - Check that admin credentials match between frontend and backend
   - Check browser network tab for API request errors