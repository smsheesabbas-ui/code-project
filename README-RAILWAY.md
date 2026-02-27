# Railway Deployment Guide

## Issue Resolution

Railway couldn't determine how to build your app because you have multiple applications (backend, frontend) in the same repository. Here's how to fix it:

## Option 1: Deploy Backend Only (Recommended)

1. **Create Railway Configuration Files** ✅
   - `railway.toml` (created)
   - `Dockerfile.railway` (created)
   - `railway.json` (created)

2. **Backend Deployment**
   ```bash
   # Connect your GitHub repo to Railway
   # Railway will automatically detect the backend service
   # It will use the Railway-specific Dockerfile
   ```

## Option 2: Separate Repositories

1. **Split into two repositories:**
   - `cashflow-backend` (backend code only)
   - `cashflow-frontend` (frontend code only)

2. **Deploy each separately**

## Option 3: Monorepo Structure

1. **Restructure repository:**
   ```
   cashflow/
   ├── apps/
   │   ├── backend/
   │   └── frontend/
   ├── railway.json (backend config)
   └── railway-frontend.json (frontend config)
   ```

## Railway Configuration Files

### Backend Config (railway.toml)
```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10

[env]
PORT = "8000"
```

### Environment Variables Needed
Set these in Railway dashboard:
- `MONGODB_URL` - Your MongoDB connection string
- `REDIS_URL` - Your Redis connection string  
- `SECRET_KEY` - Your app secret key
- `GROQ_API_KEY` - Your Groq API key
- `RESEND_API_KEY` - Your Resend API key
- `GOOGLE_CLIENT_ID` - Google OAuth client ID
- `GOOGLE_CLIENT_SECRET` - Google OAuth client secret
- `MICROSOFT_CLIENT_ID` - Microsoft OAuth client ID
- `MICROSOFT_CLIENT_SECRET` - Microsoft OAuth client secret

## Deployment Steps

1. **Push to GitHub** (if not already)
2. **Connect to Railway**
3. **Set Environment Variables**
4. **Deploy** - Railway will build and deploy

## Health Check

Once deployed, your app will be available at:
`https://your-app-name.up.railway.app`

Health endpoint: `https://your-app-name.up.railway.app/health`

## Troubleshooting

### Build Issues
- Check that `railway.toml` is in root directory
- Verify `Dockerfile.railway` exists in backend folder
- Check Railway logs for specific errors

### Runtime Issues
- Verify all environment variables are set
- Check MongoDB and Redis connectivity
- Review application logs

### Database Connection
Make sure your MongoDB URL includes:
- Database name
- Authentication credentials
- Proper connection string format

## Next Steps

After successful backend deployment:
1. Test API endpoints
2. Deploy frontend separately (connect to backend API)
3. Configure domain names
4. Set up monitoring

## Support

- Railway docs: https://docs.railway.app/
- Your app logs: Railway dashboard → Logs tab
