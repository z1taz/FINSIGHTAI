from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.config import settings

# Build engine kwargs conditionally — SQLite doesn't support pool_size/max_overflow
engine_kwargs = {
    "echo": False,
    "future": True,
}

# Only add pool settings for PostgreSQL (not SQLite)
if "postgresql" in settings.DATABASE_URL:
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

# Create database engine
engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)

# Async session maker
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Base class for SQLAlchemy ORM models
Base = declarative_base()

# Dependency to get db session
async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
