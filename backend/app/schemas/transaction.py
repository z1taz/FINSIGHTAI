from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class TransactionBase(BaseModel):
    amount: float
    category: str
    merchant: str
    description: Optional[str] = None
    mcc_code: Optional[str] = "5999"
    is_merchant_verified: Optional[bool] = True
    transaction_date: datetime
    device_id: Optional[str] = "DEV-8201"
    ip_address: Optional[str] = "198.51.100.12"
    location: Optional[str] = "Primary Jurisdiction"
    card_last4: Optional[str] = "4821"

class TransactionCreate(TransactionBase):
    pass

class TransactionResponse(TransactionBase):
    id: int
    user_id: int
    mcc_code: str = "5999"
    is_merchant_verified: bool = True
    is_fraudulent: int
    fraud_score: float
    case_id: Optional[int] = None

    class Config:
        from_attributes = True

class PaginatedTransactions(BaseModel):
    items: List[TransactionResponse]
    total: int
    page: int
    pages: int
    limit: int
