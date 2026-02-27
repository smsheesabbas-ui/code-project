# 3-Iteration Development Plan

## Overview
This plan breaks down the CashFlow AI platform into 3 logical iterations. After **Iteration 1**, you can run the application locally with MongoDB Docker, Google/Microsoft OAuth, and basic CSV import functionality.

## MVP Architecture Principles (Option A)
- **Source of truth for MVP**: This file. The detailed system design document remains a longer-term reference and is not required to ship the MVP.
- **Architecture**: Modular monolith.
  - One FastAPI backend with feature modules (auth, ingestion, entities, intelligence, chat, dashboard).
  - No microservices for MVP.
- **Database**: MongoDB for MVP.
  - All user data access is enforced by application-layer checks (every query scoped by `user_id`).
- **Async**: Iteration 1 is synchronous for simplicity; introduce Celery + Redis worker in Iteration 2 when workloads justify it.
- **AI**: Groq for NLP/classification tasks; local Python for forecasting/anomaly detection.
- **Storage**: Local file storage for MVP (Docker volume). Cloud storage is out of scope for MVP.

## Global Definition of Done (Quality Gates)
- **Security**
  - All non-`/auth/*` endpoints require JWT.
  - All data access is scoped to `user_id`.
  - Basic rate limiting applied to auth + import endpoints (target: protect against brute force and accidental retries).
  - Upload validation checks MIME/content (not only filename extension) and enforces max size (10MB) and max row count (configurable).
- **Reliability**
  - Consistent error response shape across endpoints.
  - Import pipeline is idempotent where possible (retries do not create duplicate transactions).
  - CSV import status transitions are consistent and auditable (pending → processing → preview_ready → confirmed/failed).
- **Testing**
  - Each iteration adds/maintains integration tests for its critical flows.
  - Minimum coverage expectation: critical path tests exist for auth + import + dashboard aggregates (not line coverage targets).
- **Observability**
  - Structured logs for imports, background jobs (Iteration 2+), and auth events.
  - Errors include correlation identifiers (e.g., `import_id`, `user_id`) to support debugging.

---

## Architecture Changes from Original Design

### Database: PostgreSQL → MongoDB
| PostgreSQL Table | MongoDB Collection | Notes |
|------------------|-------------------|-------|
| users | users | Auth providers: email, google, microsoft |
| csv_imports | csv_imports | Store file in GridFS or local disk |
| transactions | transactions | Embed tags, entity refs |
| entities | entities | Denormalized counters |
| revenue_streams | revenue_streams | User-scoped |
| expense_categories | expense_categories | User-scoped with defaults |
| tags | tags | Simple collection |
| ai_insights | ai_insights | Plain text + data payload |
| alerts | alerts | User-scoped |
| cashflow_forecasts | forecasts | Time-series data |
| chat_sessions | chat_sessions | Embed messages array |
| notification_preferences | user_preferences | Single doc per user |
| dashboard_layouts | user_preferences | Embedded layout config |

### AI API: GPT-4o → Free Alternatives
**Option 1: Groq (Recommended - Fast & Free Tier)**
- 1,000,000 tokens/minute free
- Models: Llama 3, Mixtral, Gemma
- Perfect for classification + chat

**Option 2: Hugging Face Inference API (Free)**
- Limited requests but no credit card
- Use for entity extraction: `facebook/bart-large-mnli`

**Option 3: OpenAI (Free tier - $5 credit)**
- Use sparingly for summaries only

**Selected Approach:** Groq for real-time tasks (classification, chat) + local ML for forecasting (Prophet doesn't need API)

### Auth: Add OAuth Providers
- Google OAuth 2.0
- Microsoft/Azure AD OAuth
- Keep email/password as fallback

---

## Iteration 1: Foundation (Local Ready)

### Goal
After this iteration, you can:
- `docker-compose up` and have full stack running locally
- Login with Google, Microsoft, or email
- Upload CSV, see preview, confirm import
- View transactions list
- Basic dashboard with real data

### Duration
**2-3 weeks** (part-time)

### Components

#### 1.1 Infrastructure Setup
```
docker-compose.yml:
  - mongo (MongoDB 7)
  - redis (for Celery)
  - backend (FastAPI)
  - frontend (Next.js)
```

#### 1.2 Database Layer (MongoDB)
**Collections to implement:**
- `users` - with OAuth provider fields
- `csv_imports` - import job tracking
- `transactions` - core financial data
- `entities` - customers/suppliers
- `expense_categories` - with default seeding
- `revenue_streams` - user-defined
- `tags` - simple labels
- `user_preferences` - notifications + dashboard layout

**Indexes:**
```javascript
// transactions
db.transactions.createIndex({ user_id: 1, transaction_date: -1 })
db.transactions.createIndex({ user_id: 1, entity_id: 1 })
db.transactions.createIndex({ user_id: 1, import_id: 1 })

// entities
db.entities.createIndex({ user_id: 1, normalized_name: 1 }, { unique: true })
```

#### 1.3 Authentication (OAuth + JWT)
**Endpoints:**
- `POST /auth/register` - Email signup
- `POST /auth/login` - Email login
- `GET /auth/google` - Google OAuth redirect
- `GET /auth/google/callback` - Google callback
- `GET /auth/microsoft` - Microsoft OAuth redirect
- `GET /auth/microsoft/callback` - Microsoft callback
- `POST /auth/refresh` - Refresh token

**User Model (MongoDB):**
```javascript
{
  _id: ObjectId,
  email: String,  // unique
  full_name: String,
  auth_provider: "email" | "google" | "microsoft",
  auth_provider_id: String,  // Google/Microsoft sub ID
  hashed_password: String,  // null for OAuth users
  is_active: Boolean,
  timezone: String,  // default "UTC"
  currency: String,  // default "USD"
  created_at: Date,
  updated_at: Date
}
```

**OAuth Setup:**
- Google: Create project in Google Cloud Console → OAuth 2.0 credentials
- Microsoft: Register app in Azure AD → Add redirect URI

#### 1.4 Feature 1: CSV Ingestion (Core)
**Endpoints:**
- `POST /imports/upload` - Upload CSV (multipart, max 10MB)
- `GET /imports/:id/preview` - Get preview + column mapping
- `PUT /imports/:id/column-mapping` - Correct column mapping
- `POST /imports/:id/confirm` - Commit transactions
- `GET /imports` - List imports
- `GET /transactions` - List transactions (paginated, filterable)
- `PUT /transactions/:id` - Edit transaction

**CSV Processing (Column Detection):**
- Use heuristics (not AI yet) for detection:
  - Date: Column with date patterns (regex for MM/DD/YYYY, DD/MM/YYYY, YYYY-MM-DD)
  - Amount: Numeric columns with +/- or separate debit/credit
  - Description: Longest text column
  - Confidence score based on pattern match percentage

**CSV Normalization Requirements (Iteration 1 scope):**
- Accept common encodings: `utf-8`, `utf-8-sig`, `latin-1`.
- Normalize amount into a single signed `amount` field.
  - Support `Amount` column OR `Debit`/`Credit` columns.
  - Handle currency symbols and thousands separators.
  - Handle negative formats like `(123.45)` and trailing `-`.
- Date parsing supports multiple formats and rejects invalid dates with row-level errors.
- Headerless CSV fallback: allow user to map columns even if headers are missing.

**Duplicate Detection (Iteration 1):**
- Flag duplicates using `(user_id, transaction_date, amount, normalized_description)` with a conservative match.
- Do not auto-delete; allow skipping duplicates at confirm time.

**File Storage:**
- Local: `uploads/` directory (for local dev)
- Docker volume mounted

**No Celery yet** - process sync for iteration 1 (switch to Celery in iteration 2)

#### 1.5 Simple Dashboard (Read-Only)
**Endpoints:**
- `GET /dashboard/overview` - Basic KPIs
  - Current cash balance
  - Total revenue (this month)
  - Total expenses (this month)
  - Net income
- `GET /dashboard/top-customers` - Simple aggregation
- `GET /dashboard/top-suppliers` - Simple aggregation

**Frontend:**
- Login page (with Google/Microsoft buttons)
- CSV upload page (drag + drop)
- Preview page (table with column mapping)
- Transactions list page (table with filters)
- Simple dashboard (cards + basic tables)

### Tech Stack - Iteration 1
| Layer | Technology |
|-------|------------|
| Backend | Python + FastAPI |
| Database | MongoDB (Docker) |
| Cache/Queue | Redis (Docker) |
| Frontend | Next.js 14 + Tailwind + shadcn/ui |
| Auth | JWT + Google OAuth + Microsoft OAuth |
| CSV Parsing | Pandas |
| File Storage | Local disk (Docker volume) |

### Local Development Setup
```bash
# Clone repo
git clone <repo>
cd cashflow-ai

# Start infrastructure
docker-compose up -d mongo redis

# Install backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Install frontend (new terminal)
cd frontend
npm install
npm run dev

# App running at http://localhost:3000
```

### Success Criteria - Iteration 1
- [ ] `docker-compose up` starts all services
- [ ] Can register/login with email
- [ ] Can login with Google OAuth
- [ ] Can login with Microsoft OAuth
- [ ] Can upload CSV (any format)
- [ ] Column detection works (heuristics-based)
- [ ] CSV normalization handles debit/credit vs amount, common encodings, and negative formats
- [ ] Duplicate transactions are flagged (not silently removed)
- [ ] Can preview and confirm import
- [ ] Transactions saved to MongoDB
- [ ] Can view transactions list
- [ ] Dashboard shows real data (cash balance, revenue, expenses)
- [ ] Top customers/suppliers visible
- [ ] Integration tests cover: auth (email), CSV upload->preview->confirm, transactions list

---

## Iteration 2: Intelligence Layer

### Goal
Add AI features using **free AI APIs** (Groq) + local ML for forecasting.

### Duration
**2-3 weeks**

### Components

#### 2.1 Setup Free AI API (Groq)
**Sign up:** https://console.groq.com
- Free tier: 1M tokens/min, no credit card required
- Models: `llama3-8b-8192` (fast), `mixtral-8x7b-32768` (smart)

**Implementation:**
```python
import groq

client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))

# Entity extraction
response = client.chat.completions.create(
    model="llama3-8b-8192",
    messages=[{
        "role": "system",
        "content": "Extract company name from transaction. Return ONLY the company name."
    }, {
        "role": "user",
        "content": "ACME CORP PAYMENT - INV#1234"
    }]
)
# Response: "ACME Corp"
```

#### 2.2 Add Celery + Background Jobs
**Why now:** AI classification is slow, should be async

**Docker Compose additions:**
```yaml
services:
  worker:
    build: ./backend
    command: celery -A app.celery_app worker --loglevel=info
    depends_on:
      - redis
      - mongo
```

**Tasks:**
- `process_csv_import(import_id)` - Parse CSV, detect columns
- `classify_transactions(import_id)` - AI entity + category classification
- `update_entity_counters(user_id)` - Recalculate denormalized totals

**Idempotency expectation:**
- Re-running `process_csv_import` or `classify_transactions` should not create duplicate entities or duplicate transaction updates.

#### 2.3 Feature 2: Entity AI Classification
**AI-Powered:**
- Entity extraction from descriptions (Groq)
- Category classification (Groq)
- Confidence scoring

**Endpoints:**
- `GET /entities` - List entities
- `POST /entities` - Create manual entity
- `PUT /entities/:id` - Update entity
- `POST /entities/:id/correct` - Log correction for learning
- `GET /entities/top-customers` - Ranked by revenue
- `GET /entities/top-suppliers` - Ranked by expense
- `GET /revenue-streams` - CRUD
- `GET /expense-categories` - CRUD + defaults
- `GET /tags` - CRUD
- `POST /transactions/:id/tags` - Add tags

**Entity Classification Logic:**
```python
# 1. Try exact match on normalized name
entity = db.entities.find_one({
    user_id: user_id,
    normalized_name: normalize(description)
})

# 2. Try fuzzy match (MongoDB text search)
if not entity:
    matches = db.entities.find(
        { $text: { $search: description } },
        { score: { $meta: "textScore" } }
    ).sort({ score: { $meta: "textScore" } }).limit(1)

# 3. Use AI to extract + create new
if not entity or confidence < 0.85:
    extracted_name = groq_extract_entity(description)
    entity = create_entity(extracted_name)
```

**Default Categories (seeded on signup):**
- Software & Subscriptions
- Office Expenses
- Marketing
- Professional Services
- Travel & Transport
- Meals & Entertainment
- Rent/Utilities
- Equipment
- Taxes
- Other

#### 2.4 Feature 3: AI Intelligence (Basic)
**Local ML (no API cost):**
- **Forecasting:** Facebook Prophet (Python library, runs locally)
  - 30-day cashflow forecast
  - No API calls needed
- **Anomaly Detection:** Simple Z-score or IQR method (local)

**AI-Powered (Groq API):**
- **Weekly Summary:** Generate plain-language summary
- **Recommendations:** Risk alerts, actionable advice

**Endpoints:**
- `GET /insights/weekly-summary` - AI-generated summary
- `GET /forecasts/cashflow` - Prophet forecast
- `GET /alerts` - Active alerts (concentration risk, cashflow risk)
- `PUT /alerts/:id/acknowledge` - Dismiss alert

**Forecasting Minimum-Data Gate (Iteration 2):**
- Only generate Prophet forecasts if there is sufficient history (example rule):
  - At least 60 days between earliest and latest transactions, and
  - At least 50 transactions.
- If insufficient data, return a clear response indicating more history is needed (no fake forecasts).

**Prophet Forecast Example:**
```python
from prophet import Prophet

# Prepare data
df = transactions_to_dataframe(user_transactions)
df = df.rename(columns={'transaction_date': 'ds', 'amount': 'y'})

# Fit model
model = Prophet()
model.fit(df)

# Predict 30 days
future = model.make_future_dataframe(periods=30)
forecast = model.predict(future)
```

#### 2.5 Simple Alert System
**Alert Types:**
- `cashflow_risk` - Projected balance below threshold
- `customer_concentration` - Single customer > 50% revenue
- `spending_spike` - Category spend > 200% of average

**Check scheduled:** Hourly (Celery beat)

### Frontend Additions
- Entity management page
- Category management
- Insights panel with weekly summary
- Alerts/notifications dropdown
- Basic cashflow chart (using Recharts or Chart.js)

### Environment Variables
```bash
# AI
GROQ_API_KEY=gsk_xxxxxxxx

# OAuth (from iteration 1, now required)
GOOGLE_CLIENT_ID=xxx
GOOGLE_CLIENT_SECRET=xxx
MICROSOFT_CLIENT_ID=xxx
MICROSOFT_CLIENT_SECRET=xxx
```

### Success Criteria - Iteration 2
- [ ] Celery worker runs background jobs
- [ ] CSV upload triggers async processing
- [ ] AI extracts entities from descriptions (Groq)
- [ ] AI categorizes expenses (Groq)
- [ ] Prophet generates 30-day forecast
- [ ] Forecasting is gated by minimum history rules and returns a clear “insufficient data” response when needed
- [ ] Weekly AI summary generated
- [ ] Alerts trigger for cashflow risk
- [ ] Top customers show correct ranking
- [ ] Entity corrections logged
- [ ] Background jobs are observable (basic status + error logging)

---

## Iteration 3: Conversational + Polish

### Goal
Add chat assistant, notifications, mobile responsiveness, and advanced features.

### Duration
**2-3 weeks**

### Components

#### 3.1 Feature 4: Conversational Assistant
**LangChain-like pattern (simplified for Groq):**
```python
# Define tools
async def get_revenue_summary(user_id, period):
    return db.transactions.aggregate([...])

async def get_entity_summary(user_id, entity_name):
    return db.entities.find_one(...)

# Agent loop
async def chat_agent(query, user_id, context):
    # 1. Classify intent (Groq)
    intent = classify_intent(query)  # "revenue_query", "expense_query", etc.
    
    # 2. Execute tool
    if intent == "revenue_query":
        data = await get_revenue_summary(user_id, extract_period(query))
    elif intent == "entity_query":
        data = await get_entity_summary(user_id, extract_entity(query))
    
    # 3. Generate response (Groq)
    response = groq_generate_response(query, data, context)
    
    return response
```

**Endpoints:**
- `POST /chat/sessions` - Create chat session
- `GET /chat/sessions` - List sessions
- `POST /chat/sessions/:id/messages` - Send message, get AI reply
- `GET /chat/sessions/:id/messages` - History

**Intents to support (20+):**
- revenue_query: "What was my revenue?"
- expense_query: "What did I spend?"
- top_customer_query: "Who is my top customer?"
- cashflow_query: "How is my cashflow?"
- trend_query: "How are we trending?"
- forecast_query: "Will I run out of cash?"
- comparison_query: "Compare this month to last"
- entity_breakdown: "Show me Acme Corp transactions"

**MVP Intent Scope (Iteration 3):**
- Implement 8-10 intents first, then expand.
- Recommended initial set:
  - `revenue_query`, `expense_query`
  - `top_customer_query`, `top_supplier_query`
  - `comparison_query` (this period vs last)
  - `entity_breakdown`
  - `forecast_query`
  - `cashflow_query`
  - `trend_query`

**Response safety rule:**
- Assistant responses must be grounded in computed data returned from backend aggregation/tool calls; no fabricated numbers.

#### 3.2 Notifications System
**Email (Resend.com - free tier: 100/day):**
- Weekly summary email
- Alert emails

**Implementation:**
```python
import resend

resend.api_key = os.getenv("RESEND_API_KEY")

resend.Emails.send({
    "from": "CashFlow AI <alerts@cashflow.ai>",
    "to": user.email,
    "subject": "Your Weekly Financial Summary",
    "html": render_template("weekly_summary.html", data=data)
})
```

**Scheduled Tasks (Celery Beat):**
```python
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Every Monday 8am
    sender.add_periodic_task(
        crontab(hour=8, minute=0, day_of_week=1),
        send_weekly_summaries.s()
    )
```

**Endpoints:**
- `GET /notifications/preferences`
- `PUT /notifications/preferences`

#### 3.3 Feature 5: Advanced Dashboard
**Endpoints:**
- `GET /dashboard/trends` - Chart data (time series)
- `GET /dashboard/cashflow-timeline` - Historical + projected
- `GET /dashboard/anomalies` - Recent anomalies
- `GET /dashboard/layout` - Get saved layout
- `PUT /dashboard/layout` - Save layout

**Frontend:**
- Drag-and-drop dashboard cards (react-grid-layout)
- Date range picker
- Tag filters
- Interactive charts (Recharts)
- Mobile-responsive layout

#### 3.4 Performance Optimizations
- Database query optimization (add missing indexes)
- API response caching (Redis)
- Frontend code splitting
- Image optimization

#### 3.5 Testing & QA
- Run all test plans from `/test plans/`
- Fix critical bugs
- Performance testing

### Success Criteria - Iteration 3
- [ ] Chat supports the MVP intent set with correct tool/aggregation grounding
- [ ] Chat maintains context across messages
- [ ] Weekly emails sent automatically
- [ ] Dashboard is customizable (drag-drop)
- [ ] Mobile-responsive design
- [ ] Cashflow timeline with projections
- [ ] Anomalies highlighted on dashboard
- [ ] All test plans passing

---

## Summary: 3-Iteration Roadmap

| Iteration | Focus | Key Deliverables | Duration |
|-----------|-------|------------------|----------|
| **1** | Foundation | MongoDB, OAuth, CSV upload, basic dashboard | 2-3 weeks |
| **2** | Intelligence | Groq AI, Prophet forecasting, entity classification, alerts | 2-3 weeks |
| **3** | Conversational | Chat assistant, email notifications, advanced dashboard, mobile | 2-3 weeks |

**Total: 6-9 weeks** for complete MVP

---

## Free Resources Used

| Service | Free Tier | Usage |
|---------|-----------|-------|
| **Groq** | 1M tokens/min | AI classification, chat, summaries |
| **Prophet** | Free (local) | Time-series forecasting |
| **MongoDB** | Docker local | Database |
| **Redis** | Docker local | Cache + Celery broker |
| **Resend** | 100 emails/day | Transactional emails |
| **Google OAuth** | Free | Social login |
| **Microsoft OAuth** | Free | Social login |

---

## Quick Start Commands (Iteration 1)

```bash
# 1. Clone and setup
git clone <repo>
cd cashflow-ai

# 2. Start MongoDB + Redis
docker-compose up -d mongo redis

# 3. Setup backend
cd backend
cp .env.example .env
# Edit .env with your OAuth credentials
pip install -r requirements.txt

# 4. Run backend
uvicorn app.main:app --reload --port 8000

# 5. Setup frontend (new terminal)
cd frontend
npm install
npm run dev

# 6. Open http://localhost:3000
```

**Iteration 1 is the hardest** - after that, you're just adding features to a working foundation.

