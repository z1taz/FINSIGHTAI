from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "FinSight AI"
    API_V1_STR: str = "/api"
    
    # Security
    SECRET_KEY: str = "SUPER_SECRET_JWT_KEY_CHANGE_IN_PRODUCTION_123456789"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./finsight.db"
    
    def __init__(self, **values):
        super().__init__(**values)
        # Render provides postgres:// or postgresql:// URLs for PostgreSQL.
        # SQLAlchemy asyncio requires postgresql+asyncpg://
        if self.DATABASE_URL.startswith("postgres://"):
            self.DATABASE_URL = self.DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
        elif self.DATABASE_URL.startswith("postgresql://") and not self.DATABASE_URL.startswith("postgresql+asyncpg://"):
            self.DATABASE_URL = self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
