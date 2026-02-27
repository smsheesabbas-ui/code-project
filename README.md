# CashFlow AI - AI-Powered Cashflow Management

## Overview

CashFlow AI is an intelligent cashflow management system that helps businesses track, analyze, and optimize their financial data with AI-powered insights.

## Features

### Iteration 1 (Foundation)
- ✅ **Authentication**: Email, Google OAuth, Microsoft OAuth
- ✅ **CSV Import**: Smart column detection and data normalization
- ✅ **Dashboard**: Real-time financial overview with KPIs
- ✅ **Transaction Management**: View, edit, and organize transactions
- ✅ **Duplicate Detection**: Automatic duplicate transaction flagging

### Tech Stack

**Backend:**
- **FastAPI** - Modern Python web framework
- **MongoDB** - NoSQL database for financial data
- **Redis** - Caching and session management
- **Motor** - Async MongoDB driver
- **Pandas** - CSV processing and data analysis

**Frontend:**
- **HTML/CSS/JavaScript** - Your existing UX1 design
- **Canvas API** - Interactive charts
- **Responsive Design** - Mobile-friendly interface

**Infrastructure:**
- **Docker** - Containerized deployment
- **Docker Compose** - Local development setup
- **GitHub Actions** - CI/CD pipeline

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Git

### Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd cashflow-ai
```

2. **Start the application**
```bash
docker-compose up -d
```

3. **Access the application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Environment Variables

Create a `.env` file in the root directory:

```bash
# Database
MONGODB_URL=mongodb://admin:password@localhost:27017/cashflow?authSource=admin
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key-change-in-production

# OAuth (Optional for local development)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret
```

## API Documentation

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login user
- `POST /api/v1/auth/logout` - Logout user
- `GET /api/v1/auth/google` - Google OAuth login
- `GET /api/v1/auth/microsoft` - Microsoft OAuth login

### CSV Import
- `POST /api/v1/imports/upload` - Upload CSV file
- `GET /api/v1/imports/{id}/preview` - Get import preview
- `PUT /api/v1/imports/{id}/column-mapping` - Update column mapping
- `POST /api/v1/imports/{id}/confirm` - Confirm import
- `GET /api/v1/imports/` - List all imports

### Dashboard
- `GET /api/v1/dashboard/overview` - Get dashboard overview
- `GET /api/v1/dashboard/top-customers` - Get top customers
- `GET /api/v1/dashboard/top-suppliers` - Get top suppliers
- `GET /api/v1/dashboard/transactions` - Get transactions

## Development

### Backend Development

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload

# Run tests
pytest
```

### Frontend Development

The frontend uses your existing UX1 design. Files are located in the `frontend/` directory:

- `frontend/public/index.html` - Main entry point
- `frontend/js/` - JavaScript modules
- `frontend/css/` - Styling (your existing design)

### Database Management

```bash
# Connect to MongoDB
docker exec -it cashflow-mongo mongosh -u admin -p password

# View collections
use cashflow
show collections
```

## Testing

### Backend Tests

```bash
cd backend
pytest app/tests/ -v
```

### Test Coverage

- Authentication flows (email, OAuth)
- CSV upload and processing
- Column detection accuracy
- Data validation
- API security

## Deployment

### Production Deployment

1. **Update environment variables**
   - Set strong `SECRET_KEY`
   - Configure OAuth credentials
   - Update database URLs

2. **Build and deploy**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Monitoring

- Application logs: `docker-compose logs -f`
- Database logs: `docker logs cashflow-mongo`
- Redis logs: `docker logs cashflow-redis`

## Architecture

### Database Schema

**Users Collection:**
```javascript
{
  email: String (unique),
  full_name: String,
  auth_provider: String,
  auth_provider_id: String,
  hashed_password: String,
  is_active: Boolean,
  timezone: String,
  currency: String
}
```

**Transactions Collection:**
```javascript
{
  user_id: String,
  transaction_date: Date,
  description: String,
  amount: Number,
  entity_id: String,
  import_id: String,
  is_duplicate: Boolean
}
```

**CSV Imports Collection:**
```javascript
{
  user_id: String,
  filename: String,
  status: String,
  column_mapping: Object,
  detection_confidence: Number,
  total_rows: Number,
  processed_rows: Number
}
```

## Security

- JWT-based authentication
- OAuth 2.0 integration
- Input validation and sanitization
- File upload restrictions
- CORS protection
- Rate limiting (in production)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions:
- Create an issue in the repository
- Check the API documentation at `/docs`
- Review the test cases for usage examples

---

**Built with ❤️ for modern businesses**
