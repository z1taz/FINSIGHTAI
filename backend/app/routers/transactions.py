from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_, and_
from datetime import datetime, timezone
from typing import Optional, List
import csv
import io

from app.database import get_db
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.transaction import TransactionCreate, TransactionResponse, PaginatedTransactions
from app.services.auth_service import get_current_user
from app.services.fraud_detector import fraud_detector

router = APIRouter(prefix="/transactions", tags=["Transactions"])

@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction_in: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    tx_dict = {
        "amount": transaction_in.amount,
        "category": transaction_in.category,
        "merchant": transaction_in.merchant,
        "description": transaction_in.description,
        "mcc_code": transaction_in.mcc_code or "5999",
        "is_merchant_verified": transaction_in.is_merchant_verified if transaction_in.is_merchant_verified is not None else True,
        "transaction_date": transaction_in.transaction_date
    }
    
    # Run immediate cybersecurity assessment using user's monthly income
    predictions = fraud_detector.predict([tx_dict], monthly_income_baseline=current_user.monthly_income)
    is_fraud, score = predictions[0]

    db_transaction = Transaction(
        user_id=current_user.id,
        amount=transaction_in.amount,
        category=transaction_in.category,
        merchant=transaction_in.merchant,
        description=transaction_in.description,
        mcc_code=transaction_in.mcc_code or "5999",
        is_merchant_verified=transaction_in.is_merchant_verified if transaction_in.is_merchant_verified is not None else True,
        transaction_date=transaction_in.transaction_date,
        is_fraudulent=is_fraud,
        fraud_score=score
    )
    db.add(db_transaction)
    await db.commit()
    await db.refresh(db_transaction)
    return db_transaction

@router.post("/upload-statement", response_model=List[TransactionResponse])
async def upload_bank_statement(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV bank statements are supported.")

    content = await file.read()
    text = content.decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(text))

    new_txs = []
    tx_dicts = []

    # Known corporate verified merchants list for automatic verification lookup
    VERIFIED_KEYWORDS = ["mcdonald", "uber", "lyft", "amazon", "target", "walmart", "netflix", "spotify", "apple", "starbucks", "jio", "bigbasket", "dmart", "zomato", "apollo", "bookstore", "chipotle", "peet"]

    for row in csv_reader:
        # Standard column names: amount, merchant, category, date/transaction_date
        amount = float(row.get("amount") or row.get("Amount") or 0.0)
        merchant = row.get("merchant") or row.get("Merchant") or row.get("description") or "Unknown Merchant"
        category = row.get("category") or row.get("Category") or "Other"
        date_str = row.get("date") or row.get("transaction_date") or row.get("Date") or datetime.now(timezone.utc).isoformat()

        try:
            tx_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception:
            tx_date = datetime.now(timezone.utc)

        # Auto-detect merchant entity verification
        merchant_lower = merchant.lower()
        is_verified = any(k in merchant_lower for k in VERIFIED_KEYWORDS) or row.get("is_verified", "").lower() in ["true", "1", "yes"]

        mcc = row.get("mcc_code") or row.get("mcc") or ("5814" if "food" in category.lower() else "5999")

        tx_dict = {
            "amount": abs(amount),
            "category": category,
            "merchant": merchant,
            "description": row.get("description", "Imported from Bank Statement"),
            "mcc_code": mcc,
            "is_merchant_verified": is_verified,
            "transaction_date": tx_date
        }
        tx_dicts.append(tx_dict)

    if not tx_dicts:
        raise HTTPException(status_code=400, detail="No valid transactions found in CSV statement.")

    # Run automated batch cybersecurity scanning
    predictions = fraud_detector.predict(tx_dicts, monthly_income_baseline=current_user.monthly_income)

    db_items = []
    for tx_dict, (is_fraud, score) in zip(tx_dicts, predictions):
        db_tx = Transaction(
            user_id=current_user.id,
            amount=tx_dict["amount"],
            category=tx_dict["category"],
            merchant=tx_dict["merchant"],
            description=tx_dict["description"],
            mcc_code=tx_dict["mcc_code"],
            is_merchant_verified=tx_dict["is_merchant_verified"],
            transaction_date=tx_dict["transaction_date"],
            is_fraudulent=is_fraud,
            fraud_score=score
        )
        db.add(db_tx)
        db_items.append(db_tx)

    await db.commit()
    for db_tx in db_items:
        await db.refresh(db_tx)

    return db_items


@router.get("", response_model=PaginatedTransactions)
async def get_transactions(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    category: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    min_amount: Optional[float] = Query(None),
    max_amount: Optional[float] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Base filter for current user
    conditions = [Transaction.user_id == current_user.id]
    
    # Category filter (uses idx_user_date_category via compound index or direct idx_category)
    if category:
        conditions.append(Transaction.category == category)
        
    # Date filters (hits composite index idx_user_date_category)
    if start_date:
        conditions.append(Transaction.transaction_date >= start_date)
    if end_date:
        conditions.append(Transaction.transaction_date <= end_date)
        
    # Amount filters (hits composite index idx_user_amount)
    if min_amount is not None:
        conditions.append(Transaction.amount >= min_amount)
    if max_amount is not None:
        conditions.append(Transaction.amount <= max_amount)
        
    # Full-text style query filter for description or merchant
    if search:
        search_filter = or_(
            Transaction.merchant.ilike(f"%{search}%"),
            Transaction.description.ilike(f"%{search}%")
        )
        conditions.append(search_filter)
        
    query_filter = and_(*conditions)
    
    # Count total matching transactions
    count_stmt = select(func.count()).select_from(Transaction).where(query_filter)
    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0
    
    # Retrieve paginated items
    select_stmt = (
        select(Transaction)
        .where(query_filter)
        .order_by(Transaction.transaction_date.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    result = await db.execute(select_stmt)
    items = result.scalars().all()
    
    pages = (total + limit - 1) // limit
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "pages": pages,
        "limit": limit
    }

@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id, 
            Transaction.user_id == current_user.id
        )
    )
    transaction = result.scalars().first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    return transaction

@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id, 
            Transaction.user_id == current_user.id
        )
    )
    transaction = result.scalars().first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    await db.delete(transaction)
    await db.commit()
    return None
