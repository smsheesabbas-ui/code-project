🏗️ CashFlow AI — Software Design Document
Version 1.0 | Full System Design: Schemas + API Spec + Architecture

MVP alignment note (Option A)
- The MVP implementation follows `plans/development-plan.md` (MongoDB + modular monolith + local file storage + Groq + local forecasting).
- The rest of this document is a longer-term blueprint and may differ from MVP architecture choices (e.g., Postgres/RLS, S3, microservices).

Table of Contents
System Architecture Overview
Database Schemas
API Specification (FastAPI)
Key Design Patterns
Project Folder Structure
Celery Tasks Reference
Implementation Sprints
1. System Architecture Overview
Layer Map
Layer	Responsibility	Technologies
Client	Web + Mobile UI	Next.js 14, React Native, Tailwind CSS, shadcn/ui
API Gateway	Auth, routing, rate limiting	FastAPI, JWT, NGINX
Services	Feature business logic	4 microservices
AI Intelligence	Classification, forecasting, NLU	GPT-4o, LangChain, Prophet, scikit-learn
Data	Persistence, caching, files	PostgreSQL + pgvector, Redis, AWS S3
Async	Background jobs	Celery + Redis Queue
Infra	Hosting, CI/CD	AWS ECS, Vercel, Docker, GitHub Actions
4 Core Microservices
Service	Owns	Feature
ingestion-service	CSV upload, parsing, dedup	F1
entity-service	Customer/supplier classification	F2
intelligence-service	Forecasts, anomalies, insights	F3
conversation-service	Chat, alerts, notifications	F4
Feature 5 (Dashboard) is an aggregation layer — it reads from all 4 services via the API gateway. No separate service needed.

Data Flow (Simple)
User uploads CSV
  → ingestion-service parses → stores raw transactions
  → entity-service runs AI → assigns customers/suppliers/categories
  → intelligence-service generates forecasts, anomalies, weekly insight
  → conversation-service handles chat + fires notifications
  → Dashboard reads aggregated data from all services
2. Database Schemas
PostgreSQL. All tables use UUID PKs. All user-owned tables have user_id + Row-Level Security. created_at / updated_at on all tables.

2.1 users
CopyCREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    full_name       VARCHAR(255),
    hashed_password VARCHAR(255),
    auth_provider   VARCHAR(50)  DEFAULT 'email',  -- 'email' | 'google'
    is_active       BOOLEAN      DEFAULT TRUE,
    timezone        VARCHAR(100) DEFAULT 'UTC',
    currency        VARCHAR(10)  DEFAULT 'USD',
    created_at      TIMESTAMPTZ  DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  DEFAULT NOW()
);
2.2 csv_imports
CopyCREATE TABLE csv_imports (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    file_name       VARCHAR(255) NOT NULL,
    s3_key          VARCHAR(500) NOT NULL,
    status          VARCHAR(50)  DEFAULT 'pending',
    -- 'pending' | 'processing' | 'preview_ready' | 'confirmed' | 'failed'
    row_count       INTEGER,
    imported_count  INTEGER     DEFAULT 0,
    duplicate_count INTEGER     DEFAULT 0,
    error_count     INTEGER     DEFAULT 0,
    column_mapping  JSONB,   -- detected column assignments
    error_log       JSONB,   -- row-level errors
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_csv_imports_user_id ON csv_imports(user_id);
column_mapping JSONB shape:

Copy{
  "date": "Transaction Date",
  "description": "Narration",
  "amount": null,
  "debit": "Debit Amount",
  "credit": "Credit Amount",
  "balance": "Running Balance",
  "confidence": 0.91
}
2.3 transactions (core table)
CopyCREATE TABLE transactions (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                 UUID         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    import_id               UUID         REFERENCES csv_imports(id),
    transaction_date        DATE         NOT NULL,
    description             TEXT         NOT NULL,
    description_cleaned     TEXT,
    amount                  NUMERIC(15,2) NOT NULL,
    -- POSITIVE = credit/revenue, NEGATIVE = debit/expense
    currency                VARCHAR(10)  DEFAULT 'USD',
    balance_after           NUMERIC(15,2),
    transaction_type        VARCHAR(20), -- 'credit' | 'debit'
    entity_id               UUID         REFERENCES entities(id),
    revenue_stream_id       UUID         REFERENCES revenue_streams(id),
    expense_category_id     UUID         REFERENCES expense_categories(id),
    is_recurring            BOOLEAN      DEFAULT FALSE,
    is_duplicate            BOOLEAN      DEFAULT FALSE,
    is_anomaly              BOOLEAN      DEFAULT FALSE,
    classification_confidence NUMERIC(4,3),
    is_manually_corrected   BOOLEAN      DEFAULT FALSE,
    embedding               VECTOR(1536), -- pgvector for similarity search
    created_at              TIMESTAMPTZ  DEFAULT NOW(),
    updated_at              TIMESTAMPTZ  DEFAULT NOW()
);

CREATE INDEX idx_transactions_user_id   ON transactions(user_id);
CREATE INDEX idx_transactions_date      ON transactions(transaction_date);
CREATE INDEX idx_transactions_entity    ON transactions(entity_id);
CREATE INDEX idx_transactions_user_date ON transactions(user_id, transaction_date DESC);
2.4 entities
CopyCREATE TABLE entities (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          UUID         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name             VARCHAR(255) NOT NULL,
    normalized_name  VARCHAR(255),   -- lowercased for matching
    entity_type      VARCHAR(50)  NOT NULL, -- 'customer' | 'supplier' | 'both'
    total_revenue    NUMERIC(15,2) DEFAULT 0,  -- denormalized counter
    total_expense    NUMERIC(15,2) DEFAULT 0,  -- denormalized counter
    transaction_count INTEGER     DEFAULT 0,
    embedding        VECTOR(1536),
    created_at       TIMESTAMPTZ  DEFAULT NOW(),
    updated_at       TIMESTAMPTZ  DEFAULT NOW(),
    UNIQUE(user_id, normalized_name)
);

CREATE INDEX idx_entities_user_id ON entities(user_id);
Why denormalized counters? Avoids expensive SUM() queries on every dashboard load. Celery updates them after each import/correction.

2.5 entity_corrections (AI feedback loop)
CopyCREATE TABLE entity_corrections (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id              UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    transaction_id       UUID NOT NULL REFERENCES transactions(id),
    original_entity_id   UUID REFERENCES entities(id),
    corrected_entity_id  UUID REFERENCES entities(id),
    original_description TEXT,
    correction_type      VARCHAR(50), -- 'entity' | 'category' | 'type'
    created_at           TIMESTAMPTZ DEFAULT NOW()
);
2.6 revenue_streams
CopyCREATE TABLE revenue_streams (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name        VARCHAR(255) NOT NULL,
    description TEXT,
    color       VARCHAR(7),   -- hex color for UI e.g. '#4CAF50'
    is_active   BOOLEAN      DEFAULT TRUE,
    created_at  TIMESTAMPTZ  DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  DEFAULT NOW(),
    UNIQUE(user_id, name)
);
2.7 expense_categories
CopyCREATE TABLE expense_categories (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name        VARCHAR(255) NOT NULL,
    description TEXT,
    color       VARCHAR(7),
    is_active   BOOLEAN      DEFAULT TRUE,
    created_at  TIMESTAMPTZ  DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  DEFAULT NOW(),
    UNIQUE(user_id, name)
);
Default categories seeded on user signup: Rent · Salaries · Marketing · Software & Subscriptions · Travel · Utilities · Professional Services · Equipment · Taxes · Other

2.8 tags + transaction_tags
CopyCREATE TABLE tags (
    id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name    VARCHAR(100) NOT NULL,
    color   VARCHAR(7),
    UNIQUE(user_id, name)
);

CREATE TABLE transaction_tags (
    transaction_id UUID REFERENCES transactions(id) ON DELETE CASCADE,
    tag_id         UUID REFERENCES tags(id)         ON DELETE CASCADE,
    PRIMARY KEY (transaction_id, tag_id)
);
2.9 ai_insights
CopyCREATE TABLE ai_insights (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    insight_type  VARCHAR(100) NOT NULL,
    -- 'weekly_summary' | 'recommendation' | 'pattern' | 'risk'
    title         VARCHAR(500),
    content       TEXT        NOT NULL,  -- Plain-language insight
    data_payload  JSONB,                 -- Supporting data for rendering
    period_start  DATE,
    period_end    DATE,
    is_read       BOOLEAN     DEFAULT FALSE,
    user_feedback VARCHAR(50),           -- 'helpful' | 'not_helpful' | NULL
    generated_by  VARCHAR(50) DEFAULT 'gpt-4o',
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_insights_user_id ON ai_insights(user_id);
CREATE INDEX idx_insights_type    ON ai_insights(user_id, insight_type);
2.10 alerts
CopyCREATE TABLE alerts (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    alert_type       VARCHAR(100) NOT NULL,
    -- 'cashflow_risk' | 'spending_spike' | 'revenue_drop' | 'concentration_risk' | 'anomaly'
    severity         VARCHAR(20) DEFAULT 'medium',  -- 'low' | 'medium' | 'high'
    title            VARCHAR(255) NOT NULL,
    message          TEXT        NOT NULL,
    data_payload     JSONB,
    is_acknowledged  BOOLEAN     DEFAULT FALSE,
    acknowledged_at  TIMESTAMPTZ,
    expires_at       TIMESTAMPTZ,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_alerts_user ON alerts(user_id, is_acknowledged);
2.11 cashflow_forecasts
CopyCREATE TABLE cashflow_forecasts (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id            UUID           NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    forecast_date      DATE           NOT NULL,
    projected_balance  NUMERIC(15,2),
    projected_revenue  NUMERIC(15,2),
    projected_expense  NUMERIC(15,2),
    confidence_lower   NUMERIC(15,2),
    confidence_upper   NUMERIC(15,2),
    model_version      VARCHAR(50),
    generated_at       TIMESTAMPTZ    DEFAULT NOW(),
    UNIQUE(user_id, forecast_date)
);
2.12 chat_sessions + chat_messages
CopyCREATE TABLE chat_sessions (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title            VARCHAR(255),       -- Auto-generated from first message
    context_summary  TEXT,               -- Compressed context for long sessions
    message_count    INTEGER     DEFAULT 0,
    last_message_at  TIMESTAMPTZ,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE chat_messages (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id    UUID        NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    user_id       UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role          VARCHAR(20) NOT NULL,  -- 'user' | 'assistant'
    content       TEXT        NOT NULL,
    intent        VARCHAR(100),
    -- 'revenue_query' | 'expense_query' | 'forecast' | 'entity_query' | 'general'
    data_payload  JSONB,                 -- Structured data returned with response
    tokens_used   INTEGER,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_chat_messages_session ON chat_messages(session_id, created_at);
2.13 notification_preferences
CopyCREATE TABLE notification_preferences (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                     UUID          NOT NULL UNIQUE REFERENCES users(id),
    email_weekly_summary        BOOLEAN       DEFAULT TRUE,
    email_alerts                BOOLEAN       DEFAULT TRUE,
    whatsapp_enabled            BOOLEAN       DEFAULT FALSE,
    whatsapp_number             VARCHAR(20),
    whatsapp_verified           BOOLEAN       DEFAULT FALSE,
    cashflow_risk_threshold     NUMERIC(15,2) DEFAULT 500,
    spending_spike_threshold    NUMERIC(5,2)  DEFAULT 30.0,  -- % increase
    concentration_risk_threshold NUMERIC(5,2) DEFAULT 50.0,  -- % of revenue
    weekly_summary_day          VARCHAR(10)   DEFAULT 'monday',
    updated_at                  TIMESTAMPTZ   DEFAULT NOW()
);
2.14 dashboard_layouts
CopyCREATE TABLE dashboard_layouts (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID        NOT NULL UNIQUE REFERENCES users(id),
    layout     JSONB       NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
layout JSONB shape:

Copy{
  "cards": [
    {"id": "cash_balance",    "visible": true, "position": 1},
    {"id": "revenue_summary", "visible": true, "position": 2},
    {"id": "expense_summary", "visible": true, "position": 3},
    {"id": "top_customers",   "visible": true, "position": 4},
    {"id": "cashflow_chart",  "visible": true, "position": 5},
    {"id": "alerts",          "visible": true, "position": 6}
  ],
  "default_period": "month"
}
Schema Relationship Map
users
  ├── csv_imports
  ├── transactions ──── entities
  │       ├──────────── revenue_streams
  │       ├──────────── expense_categories
  │       └──────────── tags (via transaction_tags)
  ├── entities
  ├── entity_corrections
  ├── revenue_streams
  ├── expense_categories
  ├── tags
  ├── ai_insights
  ├── alerts
  ├── cashflow_forecasts
  ├── chat_sessions ──── chat_messages
  ├── notification_preferences
  └── dashboard_layouts
3. API Specification (FastAPI)
Base URL: https://api.cashflow.ai/api/v1 Auth: All endpoints (except /auth/*) require Authorization: Bearer <JWT>

Standard response envelope:

Copy{ "success": true,  "data": {}, "message": "OK" }
{ "success": false, "error": "VALIDATION_ERROR", "message": "Human readable", "details": {} }
3.1 Auth
Method	Path	Description
POST	/auth/register	Register new user
POST	/auth/login	Login, returns tokens
POST	/auth/refresh	Refresh access token
POST	/auth/logout	Invalidate refresh token
POST /auth/register

Copy// Request
{ "email": "shees@example.com", "password": "SecurePass123!", "full_name": "Shees Khan", "currency": "GBP", "timezone": "Europe/London" }

// Response 201
{ "user_id": "uuid", "email": "shees@example.com", "access_token": "jwt...", "token_type": "bearer" }
POST /auth/login

Copy// Response 200
{ "access_token": "jwt...", "refresh_token": "rt...", "expires_in": 3600 }
3.2 Feature 1 — Ingestion
Method	Path	Description
POST	/imports/upload	Upload CSV (multipart)
GET	/imports/{id}/preview	Get parsed preview + column map
PUT	/imports/{id}/column-mapping	Correct column mapping
POST	/imports/{id}/confirm	Commit transactions to DB
GET	/imports	List all imports
GET	/transactions	List transactions (filterable)
PUT	/transactions/{id}	Edit a transaction
DELETE	/transactions/{id}	Soft delete transaction
POST /imports/upload

Copy@router.post("/imports/upload", status_code=202)
async def upload_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(400, "Only CSV files accepted")
    if file.size > 10 * 1024 * 1024:
        raise HTTPException(400, "File exceeds 10MB limit")

    s3_key = await upload_to_s3(file, current_user.id)
    csv_import = await create_import_record(current_user.id, file.filename, s3_key)
    background_tasks.add_task(process_csv_import, csv_import.id)

    return {"import_id": str(csv_import.id), "status": "processing"}
GET /imports/{id}/preview — Response:

Copy{
  "import_id": "uuid",
  "status": "preview_ready",
  "column_mapping": {
    "date": "Transaction Date", "description": "Narration",
    "debit": "Debit Amount", "credit": "Credit Amount",
    "balance": "Running Balance", "confidence": 0.91
  },
  "preview_rows": [
    { "row": 1, "transaction_date": "2024-01-15", "description": "TESCO STORES", "amount": -45.60, "transaction_type": "debit" }
  ],
  "total_rows": 342,
  "duplicate_estimate": 3
}
GET /transactions — Query Params: ?start_date=2024-01-01&end_date=2024-01-31&type=debit&entity_id=uuid&tag_id=uuid&page=1&limit=50

3.3 Feature 2 — Entity Structuring
Method	Path	Description
GET	/entities	List entities (?type=customer)
POST	/entities	Create entity
PUT	/entities/{id}	Update entity
DELETE	/entities/{id}	Delete entity
GET	/entities/top-customers	Top customers by revenue
GET	/entities/top-suppliers	Top suppliers by expense
POST	/entities/{id}/correct	Log AI correction (learning loop)
GET	/revenue-streams	List revenue streams
POST	/revenue-streams	Create revenue stream
GET	/expense-categories	List expense categories
POST	/expense-categories	Create category
GET	/tags	List tags
POST	/tags	Create tag
POST	/transactions/{id}/tags	Add tags to transaction
DELETE	/transactions/{id}/tags/{tag_id}	Remove tag
GET /entities/top-customers?period=month&limit=5

Copy{
  "period": "2024-01",
  "total_revenue": 28500.00,
  "customers": [
    { "entity_id": "uuid", "name": "Acme Corp", "revenue": 12000.00, "percentage": 42.1, "transaction_count": 4 }
  ]
}
POST /entities/{id}/correct

Copy{ "transaction_id": "uuid", "correct_entity_id": "uuid", "correction_type": "entity" }
3.4 Feature 3 — AI Intelligence
Method	Path	Description
GET	/insights	List insights (?type=recommendation&is_read=false)
GET	/insights/weekly-summary	Latest AI weekly summary
POST	/insights/{id}/feedback	Helpful / not helpful
GET	/forecasts/cashflow	30-day cashflow forecast
GET	/alerts	Active alerts (?acknowledged=false)
PUT	/alerts/{id}/acknowledge	Acknowledge alert
GET /insights/weekly-summary

Copy{
  "period": "2024-01-15 to 2024-01-21",
  "revenue": 8200.00, "expenses": 3100.00, "net": 5100.00,
  "revenue_change_pct": -12.0, "expense_change_pct": 5.0,
  "top_customer": "Acme Corp",
  "top_expense_category": "Software & Subscriptions",
  "narrative": "Revenue was $8,200 last week, down 12% from the prior week. Most of the drop came from fewer orders from Acme Corp.",
  "recommendations": [
    "Follow up with Acme Corp — no invoices raised this week.",
    "Software subscriptions grew — consider an audit."
  ]
}
GET /forecasts/cashflow

Copy{
  "current_balance": 14250.00,
  "forecast": [
    { "date": "2024-01-23", "projected_balance": 13800.00,
      "projected_revenue": 500.00, "projected_expense": 950.00,
      "confidence_lower": 13100.00, "confidence_upper": 14500.00 }
  ],
  "risk_alert": {
    "has_risk": true, "risk_date": "2024-02-08",
    "projected_low": 420.00,
    "message": "Cash may fall below $500 around Feb 8th based on current trends."
  }
}
3.5 Feature 4 — Conversational Assistant
Method	Path	Description
POST	/chat/sessions	Create new chat session
GET	/chat/sessions	List sessions
POST	/chat/sessions/{id}/messages	Send message, get AI reply
GET	/chat/sessions/{id}/messages	Message history
DELETE	/chat/sessions/{id}	Delete session
GET	/notifications/preferences	Get preferences
PUT	/notifications/preferences	Update preferences
POST /chat/sessions/{id}/messages

Copy@router.post("/chat/sessions/{session_id}/messages")
async def send_message(
    session_id: UUID,
    body: ChatMessageRequest,
    current_user: User = Depends(get_current_user)
):
    session = await get_session(session_id, current_user.id)
    context = await redis.get(f"chat_context:{session_id}")

    response = await financial_agent.run(
        query=body.content,
        user_id=current_user.id,
        context=context
    )

    await store_message(session_id, current_user.id, "user", body.content)
    msg = await store_message(session_id, current_user.id, "assistant",
                               response.text, response.intent, response.data)
    await redis.setex(f"chat_context:{session_id}", 3600, response.updated_context)

    return msg
Response example:

Copy{
  "role": "assistant",
  "content": "Your top customer last month was Acme Corp, contributing $12,000 — that's 42% of your total revenue.",
  "intent": "revenue_query",
  "data_payload": { "entity_name": "Acme Corp", "revenue": 12000.00, "percentage": 42.1, "period": "2024-01" }
}
3.6 Feature 5 — Dashboard
Method	Path	Description
GET	/dashboard/overview	Core KPIs (?period=month)
GET	/dashboard/trends	Chart data (?period=quarter&granularity=month)
GET	/dashboard/cashflow-timeline	Historical + projected cash
GET	/dashboard/anomalies	Recent anomalies
GET	/dashboard/layout	Saved card layout
PUT	/dashboard/layout	Save card layout
GET /dashboard/overview

Copy{
  "period": "2024-01",
  "cash_balance": 14250.00,   "net_income": 5100.00,
  "total_revenue": 28500.00,  "total_expenses": 23400.00,
  "revenue_change_pct": 8.2,  "expense_change_pct": -3.1,
  "active_alerts_count": 2,
  "top_customers": [...],     "top_suppliers": [...]
}
GET /dashboard/trends

Copy{
  "labels": ["Oct", "Nov", "Dec", "Jan"],
  "revenue":  [22000, 25000, 21000, 28500],
  "expenses": [18000, 20000, 19500, 23400],
  "net":      [4000,  5000,  1500,  5100]
}
Complete API Reference (42 Endpoints)
#	Method	Endpoint	Feature
1	POST	/auth/register	Auth
2	POST	/auth/login	Auth
3	POST	/auth/refresh	Auth
4	POST	/auth/logout	Auth
5	POST	/imports/upload	F1
6	GET	/imports/{id}/preview	F1
7	PUT	/imports/{id}/column-mapping	F1
8	POST	/imports/{id}/confirm	F1
9	GET	/imports	F1
10	GET	/transactions	F1
11	PUT	/transactions/{id}	F1
12	DELETE	/transactions/{id}	F1
13	GET	/entities	F2
14	POST	/entities	F2
15	PUT	/entities/{id}	F2
16	DELETE	/entities/{id}	F2
17	GET	/entities/top-customers	F2
18	GET	/entities/top-suppliers	F2
19	POST	/entities/{id}/correct	F2
20	GET	/revenue-streams	F2
21	POST	/revenue-streams	F2
22	GET	/expense-categories	F2
23	POST	/expense-categories	F2
24	GET	/tags	F2
25	POST	/tags	F2
26	POST	/transactions/{id}/tags	F2
27	DELETE	/transactions/{id}/tags/{tag_id}	F2
28	GET	/insights	F3
29	GET	/insights/weekly-summary	F3
30	POST	/insights/{id}/feedback	F3
31	GET	/forecasts/cashflow	F3
32	GET	/alerts	F3
33	PUT	/alerts/{id}/acknowledge	F3
34	POST	/chat/sessions	F4
35	GET	/chat/sessions	F4
36	POST	/chat/sessions/{id}/messages	F4
37	GET	/chat/sessions/{id}/messages	F4
38	DELETE	/chat/sessions/{id}	F4
39	GET	/notifications/preferences	F4
40	PUT	/notifications/preferences	F4
41	GET	/dashboard/overview	F5
42	GET	/dashboard/trends	F5
43	GET	/dashboard/cashflow-timeline	F5
44	GET	/dashboard/anomalies	F5
45	GET	/dashboard/layout	F5
46	PUT	/dashboard/layout	F5
4. Key Design Patterns
4.1 Background Job Flow (Celery)
POST /imports/upload
  ↓ Upload file to S3
  ↓ Create csv_import (status: pending)
  ↓ Queue: process_csv_import(import_id)
  ↓ Return 202 immediately ✓

Background: process_csv_import
  ↓ Download from S3
  ↓ Detect columns (scikit-learn heuristics)
  ↓ Parse rows (Pandas)
  ↓ Flag duplicates
  ↓ Update status: preview_ready

POST /imports/{id}/confirm
  ↓ Queue: commit_transactions(import_id)
  ↓ Queue: classify_transactions_batch(import_id)
  ↓ Queue: regenerate_forecast(user_id)
4.2 AI Classification Pipeline
New transaction description arrives
  → spaCy NER: extract entity name from text
  → pgvector similarity search: find existing entity (cosine similarity)
  → If score > 0.85 → auto-assign entity
  → If no match → GPT-4o: classify + create new entity
  → Store confidence score on transaction
  → User correction → entity_corrections table → future signal
4.3 LangChain Agent Tools (Feature 4)
Tool	Purpose
get_revenue_summary	Aggregate revenue by period
get_expense_summary	Aggregate expenses by category + period
get_entity_summary	Revenue/expense for specific customer or supplier
get_cashflow_forecast	Return 30-day projection data
get_recent_alerts	Active risk alerts for context
The agent parses intent → selects tool(s) → synthesizes plain-language response. No raw SQL exposed to the LLM.

4.4 Row-Level Security (PostgreSQL)
Copy-- Enable per table
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
CREATE POLICY transactions_user_isolation ON transactions
  USING (user_id = current_setting('app.current_user_id')::UUID);

-- FastAPI sets per request:
await db.execute(f"SET app.current_user_id = '{current_user.id}'")
Users physically cannot access each other's data at the DB layer — not just application layer.

5. Project Folder Structure
cashflow-ai/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Settings (Pydantic BaseSettings)
│   │   ├── database.py          # Async SQLAlchemy engine
│   │   ├── celery_app.py        # Celery config
│   │   ├── auth/
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   └── schemas.py
│   │   ├── ingestion/
│   │   │   ├── router.py        # /imports, /transactions
│   │   │   ├── service.py
│   │   │   ├── schemas.py
│   │   │   ├── parser.py        # Pandas CSV logic
│   │   │   ├── detector.py      # scikit-learn column detection
│   │   │   └── tasks.py         # Celery tasks
│   │   ├── entities/
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   ├── schemas.py
│   │   │   ├── classifier.py    # spaCy + GPT-4o entity AI
│   │   │   └── tasks.py
│   │   ├── intelligence/
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   ├── schemas.py
│   │   │   ├── forecaster.py    # Prophet integration
│   │   │   ├── anomaly.py       # Isolation Forest / Z-score
│   │   │   ├── summariser.py    # GPT-4o weekly summary
│   │   │   └── tasks.py
│   │   ├── conversation/
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   ├── schemas.py
│   │   │   ├── agent.py         # LangChain agent + tools
│   │   │   ├── notifier.py      # Resend + Twilio
│   │   │   └── tasks.py
│   │   ├── dashboard/
│   │   │   ├── router.py
│   │   │   └── service.py       # Aggregation queries
│   │   └── models/              # SQLAlchemy ORM models
│   │       ├── user.py
│   │       ├── transaction.py
│   │       ├── entity.py
│   │       └── ...
│   ├── alembic/                 # DB migrations
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                    # Next.js 14
├── mobile/                      # React Native / Expo
├── docker-compose.yml
└── .github/workflows/           # CI/CD
6. Celery Tasks Reference
Copy# ingestion-service
@celery_app.task
def process_csv_import(import_id: str): ...      # Parse + preview

@celery_app.task
def commit_transactions(import_id: str): ...     # Save to DB

# entity-service
@celery_app.task
def classify_transactions_batch(import_id: str): ...  # Run AI classification

# intelligence-service
@celery_app.task
def regenerate_forecast(user_id: str): ...       # Prophet 30-day forecast

@celery_app.task
def run_anomaly_detection(user_id: str): ...     # Isolation Forest

@celery_app.task
def generate_weekly_summary(user_id: str): ...   # GPT-4o summary

# Scheduled
@celery_app.task  # cron: every Monday 8am
def send_weekly_summaries_all_users(): ...

@celery_app.task  # cron: every hour
def check_cashflow_thresholds(): ...             # Fire alerts if needed
7. Implementation Sprint Plan
Sprint	Focus	Delivers
Sprint 1	Auth + DB setup	users, all migrations, JWT auth
Sprint 2	CSV Ingestion	Upload, preview, confirm, transactions list
Sprint 3	Entity Structuring	Entities CRUD, top customers/suppliers, categories, tags
Sprint 4	AI Intelligence	Insights, forecast, anomaly alerts
Sprint 5	Clarity Dashboard	Overview, trends, cashflow timeline, layout
Sprint 6	Chat Assistant	Sessions, messages, LangChain agent
Sprint 7	Notifications	Weekly email, alerts, WhatsApp opt-in
Sprint 8	Mobile + Polish	React Native, edge cases, performance
Quick Architecture Decisions Summary
Decision	Choice	Why
Backend language	Python / FastAPI	Native AI/ML ecosystem — Pandas, Prophet, LangChain
Vector search	pgvector (inside Postgres)	No separate vector DB needed — keeps it simple
Async jobs	Celery + Redis	CSV parsing + AI classification are too heavy for request-response
Chat context	Redis (TTL 1hr)	Fast read/write, auto-expires — no DB bloat
Frontend	Next.js 14 App Router	SSR for fast dashboard loads, one codebase for web + SSG
Forecasting	Prophet (Facebook)	Built for irregular business time-series — minimal tuning
Anomaly detection	Isolation Forest	Unsupervised, works well on small datasets
Security	RLS at DB layer	Users can't access each other's data even if app has a bug
Denormalized counters	On entities table	total_revenue, total_expense pre-computed — fast dashboard queries
Shees — this is your complete blueprint. 15 database tables, 46 API endpoints, 4 microservices, full Celery task map, folder structure, and sprint plan. Everything is intentionally simple but production-ready — no over-engineering.