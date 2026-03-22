# WIM Frontend - Deployment Guide

## Free Deployment Options

### Option 1: Vercel (Recommended)

1. **Push code to GitHub**
2. **Import to Vercel:**
   - Go to [vercel.com](https://vercel.com)
   - Connect GitHub account
   - Import this repository

3. **Configure environment variables:**
   ```
   NEXT_PUBLIC_API_URL=https://your-backend-api.com
   ```

4. **Deploy:**
   - Vercel automatically builds and deploys
   - Uses `vercel.json` configuration
   - Automatic deployments on git push

**Free tier:**
- Unlimited personal projects
- 100GB bandwidth/month
- Serverless functions included
- Custom domains supported

### Option 2: Netlify

1. **Push code to GitHub**
2. **Connect to Netlify:**
   - Go to [netlify.com](https://netlify.com)
   - Connect GitHub and import repo

3. **Build settings:**
   ```
   Build command: npm run build
   Publish directory: .next
   ```

4. **Environment variables:**
   ```
   NEXT_PUBLIC_API_URL=https://your-backend-api.com
   ```

**Free tier:**
- 100GB bandwidth/month
- 300 build minutes/month
- Form handling included

### Option 3: Cloudflare Pages

1. **Push code to GitHub**
2. **Connect to Cloudflare Pages:**
   - Go to Cloudflare dashboard
   - Pages → Create project → Connect to Git

3. **Build configuration:**
   ```
   Framework preset: Next.js
   Build command: npm run build
   Build output directory: .next
   ```

4. **Environment variables:**
   ```
   NEXT_PUBLIC_API_URL=https://your-backend-api.com
   ```

**Free tier:**
- Unlimited bandwidth
- 500 builds/month
- Global CDN included