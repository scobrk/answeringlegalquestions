# Railway Deployment Guide

## Prerequisites
1. Railway account (free tier: 500 hours/month)
2. GitHub repository (public for easy deployment)
3. Environment variables configured

## Deployment Steps

### 1. Railway Setup
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Create new project
railway new revenue-nsw-assistant
```

### 2. Backend Deployment
```bash
# Deploy FastAPI backend
railway add --service backend
railway up --service backend --dockerfile docker/railway.dockerfile

# Set environment variables
railway variables set SUPABASE_URL=your-supabase-url
railway variables set SUPABASE_ANON_KEY=your-anon-key
railway variables set OPENAI_API_KEY=your-openai-key
railway variables set RAGFLOW_URL=https://your-ragflow-service.railway.app
```

### 3. RAGflow Deployment
```bash
# Deploy RAGflow service
railway add --service ragflow
railway deploy --service ragflow --dockerfile docker/ragflow.dockerfile
```

### 4. Environment Configuration
- Backend: `https://backend-revenue-nsw.up.railway.app`
- RAGflow: `https://ragflow-revenue-nsw.up.railway.app`
- Custom domain: Configure in Railway dashboard

## Health Monitoring
- Health checks: `/health` endpoints
- Uptime monitoring: Railway dashboard
- Logs: `railway logs --service backend`