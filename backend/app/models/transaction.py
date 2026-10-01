from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    category = Column(String, nullable=False, index=True)
    merchant = Column(String, nullable=False)
    description = Column(String, nullable=True)
    mcc_code = Column(String, default="5999", nullable=False)
    is_merchant_verified = Column(Boolean, default=True, nullable=False)
    transaction_date = Column(DateTime(timezone=True), nullable=False, index=True)
    is_fraudulent = Column(Integer, default=0, nullable=False) # 0 = normal, 1 = flagged anomaly
    fraud_score = Column(Float, default=0.0, nullable=False)

    # Enriched entity & network intelligence signals
    device_id = Column(String(64), nullable=True, index=True)
    ip_address = Column(String(64), nullable=True, index=True)
    location = Column(String(128), nullable=True)
    card_last4 = Column(String(4), default="4821", nullable=True)

    # Relationships
    user = relationship("User", backref="transactions")
    case = relationship("Case", back_populates="transaction", uselist=False, cascade="all, delete-orphan")

# Compound indexes to optimize filtered searches and graph aggregations
Index("idx_user_date_category", Transaction.user_id, Transaction.transaction_date, Transaction.category)
Index("idx_user_amount", Transaction.user_id, Transaction.amount)
Index("idx_device_tx", Transaction.device_id, Transaction.transaction_date)
Index("idx_ip_tx", Transaction.ip_address, Transaction.transaction_date)
Index("idx_merchant_tx", Transaction.merchant, Transaction.transaction_date)
