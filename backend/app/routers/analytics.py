from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_, extract
from datetime import datetime, timedelta
from typing import List, Dict

from app.database import get_db
from app.models.transaction import Transaction
from app.models.user import User
from app.services.auth_service import get_current_user
from app.services.fraud_detector import fraud_detector
from app.schemas.transaction import TransactionResponse

router = APIRouter(prefix="/analytics", tags=["Analytics & Fraud Detection"])

@router.get("/spending-summary")
async def get_spending_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get category-wise total spending for current user.
    """
    # Exclude Income (e.g. Salary, Refund) from spending summary
    stmt = (
        select(Transaction.category, func.sum(Transaction.amount).label("total"))
        .where(
            and_(
                Transaction.user_id == current_user.id,
                Transaction.category != "Salary"
            )
        )
        .group_by(Transaction.category)
        .order_by(func.sum(Transaction.amount).desc())
    )
    result = await db.execute(stmt)
    rows = result.all()
    
    return [{"category": row[0], "total": float(row[1] or 0.0)} for row in rows]

@router.get("/monthly-trend")
async def get_monthly_trend(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get monthly income vs expense trend for current user.
    """
    # SQLite / Postgres date formatting. 
    # For cross-database compatibility in SQL, we can fetch transaction records and aggregate in Python
    # since we want to be robust across SQLite (development) and PostgreSQL (production).
    # Since we use Postgres in docker, let's fetch raw dates and amounts and group in Python.
    stmt = (
        select(
            Transaction.amount,
            Transaction.category,
            Transaction.transaction_date
        )
        .where(Transaction.user_id == current_user.id)
        .order_by(Transaction.transaction_date.asc())
    )
    result = await db.execute(stmt)
    transactions = result.all()
    
    monthly_data = {}
    for amount, category, date in transactions:
        month_key = date.strftime("%Y-%m")
        if month_key not in monthly_data:
            monthly_data[month_key] = {"month": month_key, "income": 0.0, "expense": 0.0}
            
        if category == "Salary":
            monthly_data[month_key]["income"] += amount
        else:
            monthly_data[month_key]["expense"] += amount
            
    # Round values
    trend_data = []
    for month_key in sorted(monthly_data.keys()):
        item = monthly_data[month_key]
        item["income"] = round(item["income"], 2)
        item["expense"] = round(item["expense"], 2)
        trend_data.append(item)
        
    return trend_data

@router.get("/anomalies", response_model=List[TransactionResponse])
async def get_anomalies(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get flagged fraudulent/anomalous transactions for current user.
    """
    stmt = (
        select(Transaction)
        .where(
            and_(
                Transaction.user_id == current_user.id,
                Transaction.is_fraudulent == 1
            )
        )
        .order_by(Transaction.transaction_date.desc())
    )
    result = await db.execute(stmt)
    anomalies = result.scalars().all()
    return anomalies

@router.post("/train", status_code=status.HTTP_200_OK)
async def train_ml_model(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger training/retraining of the Isolation Forest ML model.
    """
    # Fetch all transactions for this user
    stmt = select(Transaction).where(Transaction.user_id == current_user.id)
    result = await db.execute(stmt)
    txs = result.scalars().all()
    
    if len(txs) < 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Need at least 20 transactions to train the anomaly detection model."
        )
        
    # Serialize to dictionary for the model
    tx_dicts = []
    for tx in txs:
        tx_dicts.append({
            "amount": tx.amount,
            "category": tx.category,
            "merchant": tx.merchant,
            "transaction_date": tx.transaction_date
        })
        
    contamination = fraud_detector.train(tx_dicts)
    
    # After training, score and update existing transactions
    predictions = fraud_detector.predict(tx_dicts)
    for tx, (is_fraud, score) in zip(txs, predictions):
        tx.is_fraudulent = is_fraud
        tx.fraud_score = score
        
    await db.commit()
    
    return {
        "status": "Success",
        "message": "Model trained successfully and transactions updated.",
        "contamination_rate": contamination
    }
