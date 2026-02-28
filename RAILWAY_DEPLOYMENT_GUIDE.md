# Railway Deployment Guide

## 🚨 **Current Issues Fixed**

1. **Backend start command**: Changed from uvicorn to gunicorn for Railway compatibility
2. **Frontend configuration**: Added proper deployment settings
3. **Environment variables**: Added missing RESEND_API_KEY

## 📋 **Step-by-Step Railway Setup**

### **1. Create Services in Railway Dashboard**

1. Go to your Railway project
2. Click `+ New` → Add these services:
   - **MongoDB**: Search "MongoDB" template
   - **Redis**: Search "Redis" template  
   - **Backend**: Connect to your backend repo
   - **Frontend**: Connect to your frontend repo

### **2. Set Environment Variables**

In Railway dashboard, set these variables for **Backend** service:

```bash
# Auto-populated by Railway (no need to set):
MONGO_URL=auto_filled
REDIS_URL=auto_filled

# Required (set these manually):
SECRET_KEY=your-secure-random-string-here
GROQ_API_KEY=your-groq-api-key-here

# Optional (if using OAuth):
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret
RESEND_API_KEY=your-resend-api-key
```

### **3. Deploy Order**

Deploy in this order:
1. **MongoDB** (will provide MONGO_URL)
2. **Redis** (will provide REDIS_URL)  
3. **Backend** (needs both DB services)
4. **Frontend** (needs backend URL)

### **4. Verify Deployment**

After deployment:
- Backend: `https://your-backend-url.railway.app/health`
- Frontend: `https://your-frontend-url.railway.app/`

### **5. Common Issues & Solutions**

#### **Issue: Build stuck at "Installing dependencies"**
- Solution: Check requirements.txt for conflicting packages
- Fixed: Updated Dockerfile to use proper caching

#### **Issue: MongoDB connection failed**
- Solution: Ensure MongoDB service is deployed first
- Fixed: Using Railway's MONGO_URL variable

#### **Issue: Frontend not loading**
- Solution: Update frontend API calls to use Railway backend URL
- Fixed: Added proper start command for static files

### **6. Testing the Deployment**

```bash
# Test backend health
curl https://your-backend.railway.app/health

# Test frontend
curl https://your-frontend.railway.app/
```

## 🔧 **What Was Fixed**

1. **Backend railway.toml**:
   - Changed start command to gunicorn (Railway preferred)
   - Added RESEND_API_KEY environment variable

2. **Frontend railway.toml**:
   - Added proper deployment configuration
   - Set start command for static file serving

3. **Environment Variables**:
   - Mapped Railway's MONGO_URL to your MONGODB_URL
   - Added all required environment variables

## 🚀 **Next Steps**

1. Push these changes to your repository
2. Redeploy both services in Railway
3. Check deployment logs for any remaining errors
4. Test the live application

The deployment should now work properly without getting stuck!
