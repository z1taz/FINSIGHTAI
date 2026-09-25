from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.future import select
from app.config import settings
from app.database import engine, Base, SessionLocal
from app.routers import auth, transactions, analytics, admin, cases, network, evaluation, policies, governance
from app.seed_data import seed_all
# Import all models to ensure metadata registration
from app.models import User, Transaction, Case, CaseAuditLog, AgentInvestigationRun
import asyncio

app = FastAPI(
    title="FinSight AI Risk Operations API",
    description="AI-assisted fraud investigation and risk-operations platform",
    version="2.0.0"
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
app.include_router(cases.router, prefix=settings.API_V1_STR)
app.include_router(network.router, prefix=settings.API_V1_STR)
app.include_router(evaluation.router, prefix=settings.API_V1_STR)
app.include_router(policies.router, prefix=settings.API_V1_STR)
app.include_router(governance.router, prefix=settings.API_V1_STR)
app.include_router(transactions.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup_event():
    print("Starting up FinSight AI application...")
    
    # Retry database connection with exponential backoff
    max_retries = 5
    for attempt in range(1, max_retries + 1):
        try:
            # 1. Ensure database tables exist
            print(f"Verifying database tables... (attempt {attempt}/{max_retries})")
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                
            # 2. Run seed process
            print("Checking database seed status...")
            async with SessionLocal() as db:
                await seed_all(db)
            
            print("FinSight AI startup completed successfully!")
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
        "platform": "FinSight AI Risk Operations",
        "version": "2.0.0",
        "docs": "/docs",
        "status": "Operational"
    }
