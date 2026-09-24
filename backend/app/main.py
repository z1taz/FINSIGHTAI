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

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(transactions.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup_event():
    print("Starting up FastAPI application...")
    
    # Retry database connection with exponential backoff
    max_retries = 5
    for attempt in range(1, max_retries + 1):
        try:
            # 1. Ensure database tables exist
            print(f"Verifying database tables... (attempt {attempt}/{max_retries})")
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                
            # 2. Run seed process to insert 10,000+ records and pre-train model
            print("Checking database seed status...")
            async with SessionLocal() as db:
                await seed_all(db)
            
            print("Database startup completed successfully!")
            break
        except Exception as e:
            print(f"Database connection attempt {attempt}/{max_retries} failed: {e}")
            if attempt == max_retries:
                print("ERROR: All database connection attempts failed.")
                print("Hint: Check that DATABASE_URL is set correctly and the database is reachable.")
                raise
            wait_time = 2 ** attempt  # 2, 4, 8, 16, 32 seconds
            print(f"Retrying in {wait_time} seconds...")
            await asyncio.sleep(wait_time)

@app.get("/")
async def root():
    return {
        "message": "Welcome to FinSight AI API",
        "docs": "/docs",
        "status": "Running"
    }
