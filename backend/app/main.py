from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import init_db
from .auth.router import router as auth_router
from .ingestion.router import router as ingestion_router
from .dashboard.router import router as dashboard_router
from .dashboard.advanced_router import router as advanced_dashboard_router
from .entities.router import router as entities_router
from .forecasting.router import router as forecasting_router
from .insights.router import router as insights_router
from .alerts.router import router as alerts_router
from .chat.router import router as chat_router
from .notifications.router import router as notifications_router
from .config import settings

app = FastAPI(
    title="CashFlow AI API",
    description="AI-powered cashflow management system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(ingestion_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(advanced_dashboard_router, prefix="/api/v1")
app.include_router(entities_router, prefix="/api/v1")
app.include_router(forecasting_router, prefix="/api/v1")
app.include_router(insights_router, prefix="/api/v1")
app.include_router(alerts_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.get("/")
async def root():
    return {"message": "CashFlow AI API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
