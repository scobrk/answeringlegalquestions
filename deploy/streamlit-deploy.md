# Streamlit Community Cloud Deployment Guide

## Prerequisites
1. Public GitHub repository
2. Streamlit Community Cloud account
3. Backend services deployed (Railway)

## Deployment Steps

### 1. Repository Setup
```bash
# Ensure repository is public
git remote -v
git push origin main
```

### 2. Streamlit Cloud Deployment
1. Go to https://share.streamlit.io
2. Click "New app"
3. Connect GitHub repository
4. Set deployment settings:
   - Repository: `your-username/askinglegalquestions`
   - Branch: `main`
   - Main file path: `ui/main.py`
   - Python version: `3.11`

### 3. Environment Variables
Set in Streamlit Cloud dashboard:
```
BACKEND_URL=https://backend-revenue-nsw.up.railway.app
ENVIRONMENT=production
```

### 4. App Configuration
Create `ui/.streamlit/config.toml`:
```toml
[server]
headless = true
port = 8501
enableCORS = false

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
```

## Access URLs
- Production: `https://revenue-nsw-assistant.streamlit.app`
- Admin: Streamlit Cloud dashboard
- Logs: Available in dashboard