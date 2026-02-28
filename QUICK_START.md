# CashFlow AI - Quick Start Guide

## 🚀 Run Locally for Testing

### Option 1: Docker Compose (Recommended)

**Prerequisites:**
- Docker and Docker Compose installed

**Steps:**
```bash
# 1. Start all services
docker-compose up -d

# 2. Wait for services to start (30 seconds)
docker-compose logs -f

# 3. Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Documentation: http://localhost:8000/docs
```

**Services Started:**
- MongoDB (port 27017)
- Redis (port 6379) 
- Backend API (port 8000)
- Frontend (port 3000)

### Option 2: Manual Setup

**Prerequisites:**
- Python 3.11+
- Node.js 18+
- MongoDB and Redis running locally

**Backend Setup:**
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env

# Start backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend Setup:**
```bash
cd frontend

# Install dependencies
npm install

# Start frontend server
npm run dev
```

## 🧪 Run Tests

**All Tests:**
```bash
cd backend
python run_tests.py
```

**Specific Test Categories:**
```bash
# Authentication tests
python -m pytest test_iteration_1.py::TestIteration1Authentication -v

# CSV ingestion tests
python -m pytest test_iteration_1.py::TestIteration1CSVIngestion -v

# Dashboard tests
python -m pytest test_iteration_1.py::TestIteration1Dashboard -v
```

## 📊 Test the Application

### 1. Test Authentication
- **Register:** http://localhost:3000/register
- **Login:** http://localhost:3000/login
- **API Docs:** http://localhost:8000/docs

### 2. Test CSV Import
```bash
# Use sample test data
curl -X POST "http://localhost:8000/api/v1/imports/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@backend/test_data/sample_transactions.csv"
```

### 3. Test Dashboard
- **Overview:** http://localhost:8000/api/v1/dashboard/overview
- **Transactions:** http://localhost:8000/api/v1/transactions

## 🔧 Environment Setup

Create `.env` file in backend directory:
```bash
# Database
MONGODB_URL=mongodb://admin:password@localhost:27017/cashflow?authSource=admin
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key-change-in-production
DEBUG=true

# File Upload
UPLOAD_DIR=uploads
MAX_FILE_SIZE=10485760
```

## 🐛 Troubleshooting

### MongoDB Connection Issues
```bash
# Reset MongoDB
docker-compose down -v
docker-compose up -d mongo
```

### Port Conflicts
```bash
# Check what's using ports
netstat -tulpn | grep :8000
netstat -tulpn | grep :3000

# Kill processes if needed
sudo kill -9 <PID>
```

### Backend Won't Start
```bash
# Check logs
docker-compose logs backend

# Restart backend
docker-compose restart backend
```

### Frontend Build Issues
```bash
# Clear node modules
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

## 📱 Access Points

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | React application |
| Backend API | http://localhost:8000 | FastAPI server |
| API Docs | http://localhost:8000/docs | Swagger documentation |
| Health Check | http://localhost:8000/health | Service status |

## 🧪 Sample Data

Test with provided CSV files:
- `backend/test_data/sample_transactions.csv` - Standard format
- `backend/test_data/complex_format.csv` - Debit/Credit format

## ✅ Verification

Once running, verify:

1. **Services Status:**
   ```bash
   docker-compose ps
   ```

2. **API Health:**
   ```bash
   curl http://localhost:8000/health
   ```

3. **Frontend Access:**
   - Open http://localhost:3000 in browser

4. **Run Tests:**
   ```bash
   cd backend && python run_tests.py
   ```

## 🚀 Ready for Development

Your local CashFlow AI environment is now ready! You can:
- Test all Iteration 1 features
- Run the comprehensive test suite
- Develop new features
- Debug and troubleshoot

**Next Steps:**
1. Run the test suite to verify everything works
2. Test CSV upload with sample data
3. Explore the API documentation
4. Start building additional features
