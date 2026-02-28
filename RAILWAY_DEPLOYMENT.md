# Railway Deployment Guide

## Issues Fixed

Your Railway deployment was failing due to these issues:

1. **Missing Database Services** - Railway needs MongoDB and Redis services added
2. **Incorrect Environment Variables** - Localhost URLs don't work in Railway
3. **Missing CORS Configuration** - Railway domains weren't allowed
4. **Build Configuration** - NIXPACKS builder wasn't optimal for your setup

## Files Created/Modified

### 1. Updated `railway.toml`
- Changed to DOCKERFILE builder
- Added Railway service definitions
- Added environment variable placeholders

### 2. Created `backend/Dockerfile.railway`
- Railway-optimized Docker configuration
- Health checks included
- Uses Railway-specific requirements

### 3. Created `backend/requirements-railway.txt`
- Streamlined dependencies for Railway
- Removed unnecessary testing packages

### 4. Updated `backend/app/core/config.py`
- Added Railway domains to CORS
- Better production compatibility

## Deployment Steps

### 1. Authenticate with Railway
```bash
railway login
```

### 2. Link Your Project
```bash
railway link
```

### 3. Add Required Services
```bash
railway add mongodb
railway add redis
```

### 4. Set Environment Variables
In your Railway dashboard, set these variables:

```
SECRET_KEY=ckirPDRRA1ailSX7WBMbBKFv1Ms0YdSfhUj0IsMmIKw
MONGODB_URL=mongodb://mongo:mongo@mongo.railway.internal:27017/cashflow?authSource=admin
REDIS_URL=redis://redis.railway.internal:6379
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret
GROQ_API_KEY=your-groq-api-key
```

### 5. Deploy
```bash
railway up
```

## What Was Fixed

### Database Connections
- MongoDB: Uses Railway's internal MongoDB service
- Redis: Uses Railway's internal Redis service
- URLs updated to Railway's internal network

### CORS Issues
- Added `*.railway.app` and `*.up.railway.app` to allowed origins
- Frontend can now communicate with backend

### Build Process
- Custom Dockerfile for better control
- Health checks for monitoring
- Optimized for Railway's infrastructure

### Environment Variables
- All required variables properly configured
- Railway-specific variable references
- Generated secure secret key

## Troubleshooting

### If deployment still fails:
1. Check Railway logs: `railway logs`
2. Verify services are running: `railway status`
3. Check environment variables in Railway dashboard
4. Ensure MongoDB and Redis services are added

### Common Issues:
- **Database connection errors**: Make sure MongoDB and Redis services are added
- **CORS errors**: Verify Railway domains are in CORS configuration
- **Build failures**: Check Dockerfile and requirements files

## Next Steps

After successful deployment:
1. Test your application at the Railway URL
2. Set up custom domain if needed
3. Configure monitoring and alerts
4. Set up automated deployments from GitHub

Your CashFlow AI application should now deploy successfully on Railway!
