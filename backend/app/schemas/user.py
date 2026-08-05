from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    full_name: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    monthly_income: float = 5000.0
    is_admin: bool = False
    last_login_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class UserUpdateProfile(BaseModel):
    monthly_income: Optional[float] = None
    full_name: Optional[str] = None

class AdminUserDetail(BaseModel):
    id: int
    email: str
    full_name: str
    monthly_income: float
    is_admin: bool
    total_transactions: int
    last_login_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class AdminPlatformStats(BaseModel):
    total_users: int
    total_transactions: int
    total_flagged_anomalies: int
    total_system_volume: float

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None

