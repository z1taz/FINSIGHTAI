from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.future import select
from app.config import settings
from app.database import engine, Base, SessionLocal
from app.routers import auth, transactions, analytics, admin
from app.seed_data import seed_all
from app.models.user import User
import asyncio

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Personal Finance & Fraud Analytics API",
    version="1.0.0"
)

# Set up CORS middleware to allow connection from the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(transactions.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix=settings.API_V1_STR)


@app.on_event("startup")
async def startup_event():
    print("Starting up FastAPI application...")
    
    # 1. Ensure database tables exist
    print("Verifying database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    # 2. Run seed process to insert 10,000+ records and pre-train model
    print("Checking database seed status...")
    async with SessionLocal() as db:
        await seed_all(db)

@app.get("/")
async def root():
    return {
        "message": "Welcome to FinSight AI API",
        "docs": "/docs",
        "status": "Running"
    }
