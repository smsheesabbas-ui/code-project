# CashFlow AI Railway Deployment Guide

## 🚀 Quick Deploy to Railway (New Project)

### Prerequisites
- Railway account (https://railway.app)
- GitHub account

### Step 1: Create New Railway Project
1. Go to https://railway.app
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository (or create new one)
4. Choose "New Project" (don't update existing)

### Step 2: Configure Backend Service
1. Click "Add Service" → "GitHub Repo"
2. Select your repository
3. Set root directory: `/backend`
4. Railway will detect `railway.toml` and `Dockerfile`
5. Click "Deploy"

### Step 3: Configure Frontend Service
1. Click "Add Service" → "GitHub Repo"
2. Select same repository
3. Set root directory: `/frontend`
4. Railway will detect `railway.toml` and `package.json`
5. Click "Deploy"

### Step 4: Set Environment Variables
For Backend Service:
- `GEMINI_API_KEY`: Your Google Gemini API key
- `SECRET_KEY`: Generate random secret (use: openssl rand -hex 32)
- `MONGODB_URL`: Railway MongoDB addon URL
- `REDIS_URL`: Railway Redis addon URL

### Step 5: Add Database Addons
1. Click "Add Service" → "MongoDB"
2. Click "Add Service" → "Redis"
3. Railway will automatically connect them

### Step 6: Update Frontend URL
1. Get backend Railway URL (e.g., `backend-production.up.railway.app`)
2. Frontend will automatically connect via API_BASE_URL logic

### Step 7: Test Deployment
1. Visit your frontend Railway URL
2. Test all features:
   - Dashboard loads
   - CSV import works
   - AI assistant responds
   - Insights show Gemini branding

## 🔧 Configuration Files Created

### Backend: `/backend/railway.toml`
```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "Dockerfile"

[deploy]
startCommand = "gunicorn app.main:app -w 1 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10

[env]
MONGODB_URL = "${{MONGO_URL}}"
REDIS_URL = "${{REDIS_URL}}"
SECRET_KEY = "${{SECRET_KEY}}"
GEMINI_API_KEY = "${{GEMINI_API_KEY}}"
```

### Frontend: `/frontend/railway.toml`
```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "npx serve -s . -l 3000"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
```

## 🌐 URLs After Deployment
- Frontend: `https://your-app-name.up.railway.app`
- Backend: `https://your-backend-name.up.railway.app`
- MongoDB: Railway internal connection
- Redis: Railway internal connection

## ✅ Success Indicators
- Frontend loads and shows dashboard
- API calls work (check browser console)
- AI assistant responds with demo data
- CSV import functions correctly
- No CORS errors in console

## 🚨 Troubleshooting
- If frontend can't reach backend: Check CORS settings
- If AI doesn't work: Verify GEMINI_API_KEY is set
- If database errors: Check MongoDB/Redis addon connections
- Check Railway logs for detailed error messages
