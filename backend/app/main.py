from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.future import select
from app.config import settings
from app.database import engine, Base, SessionLocal
from app.routers import auth, transactions, analytics, admin, cases, network, evaluation, policies, governance
from app.seed_data import seed_all
# Import all models to ensure metadata registration
from app.models import User, Transaction, Case, CaseAuditLog, AgentInvestigationRun
import asyncio


# ---------------------------------------------------------------------------
# Inline schema migrations
# Runs ADD COLUMN IF NOT EXISTS for every column added after the initial
# deploy. Safe to run on every startup — completely idempotent.
# ---------------------------------------------------------------------------
_MIGRATIONS = [
    # transactions table — redesign columns
    "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS device_id VARCHAR(64)",
    "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS ip_address VARCHAR(64)",
    "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS location VARCHAR(128)",
    "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS card_last4 VARCHAR(4) DEFAULT '4821'",
    # Create indexes only if they don't exist (PostgreSQL 9.5+)
    "CREATE INDEX IF NOT EXISTS idx_device_tx ON transactions (device_id, transaction_date)",
    "CREATE INDEX IF NOT EXISTS idx_ip_tx ON transactions (ip_address, transaction_date)",
    "CREATE INDEX IF NOT EXISTS idx_merchant_tx ON transactions (merchant, transaction_date)",
    "CREATE INDEX IF NOT EXISTS idx_user_date_category ON transactions (user_id, transaction_date, category)",
    "CREATE INDEX IF NOT EXISTS idx_user_amount ON transactions (user_id, amount)",
    # cases table — all AI/decision columns
    "ALTER TABLE cases ADD COLUMN IF NOT EXISTS risk_factors JSON DEFAULT '[]'",
    "ALTER TABLE cases ADD COLUMN IF NOT EXISTS ai_recommendation VARCHAR(64)",
    "ALTER TABLE cases ADD COLUMN IF NOT EXISTS ai_confidence FLOAT",
    "ALTER TABLE cases ADD COLUMN IF NOT EXISTS ai_reasoning_summary TEXT",
    "ALTER TABLE cases ADD COLUMN IF NOT EXISTS ai_investigated_at TIMESTAMPTZ",
    "ALTER TABLE cases ADD COLUMN IF NOT EXISTS human_decision VARCHAR(64)",
    "ALTER TABLE cases ADD COLUMN IF NOT EXISTS human_notes TEXT",
    "ALTER TABLE cases ADD COLUMN IF NOT EXISTS decided_by VARCHAR(128)",
    "ALTER TABLE cases ADD COLUMN IF NOT EXISTS decided_at TIMESTAMPTZ",
]

async def run_migrations(conn) -> None:
    """Apply all pending schema migrations idempotently."""
    for sql in _MIGRATIONS:
        try:
            await conn.execute(text(sql))
        except Exception as e:
            # Log but don't crash — index-already-exists errors are harmless
            print(f"[migration] skipped ({type(e).__name__}): {sql[:80]}")

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
                # 2. Apply incremental column migrations for existing tables
                print("Applying schema migrations...")
                await run_migrations(conn)
                
            # 3. Run seed process
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
