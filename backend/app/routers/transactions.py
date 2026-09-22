from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_, and_
from datetime import datetime, timezone
from typing import Optional, List
import csv
import io
import random

from app.database import get_db
from app.models.transaction import Transaction
from app.models.user import User
from app.models.case import Case, CaseAuditLog, CaseStatus
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
    device_id = transaction_in.device_id or f"DEV-{random.randint(1000, 9999)}"
    ip_addr = transaction_in.ip_address or f"198.51.100.{random.randint(2, 250)}"
    loc = transaction_in.location or "Primary Jurisdiction"
    card4 = transaction_in.card_last4 or "4821"

    tx_dict = {
        "amount": transaction_in.amount,
        "category": transaction_in.category,
        "merchant": transaction_in.merchant,
        "description": transaction_in.description,
        "mcc_code": transaction_in.mcc_code or "5999",
        "is_merchant_verified": transaction_in.is_merchant_verified if transaction_in.is_merchant_verified is not None else True,
        "transaction_date": transaction_in.transaction_date,
        "device_id": device_id,
        "ip_address": ip_addr,
        "location": loc
    }
    
    # Run structured risk engine
    calc = fraud_detector.calculate_structured_risk(tx_dict, monthly_income_baseline=current_user.monthly_income)
    is_fraud = 1 if calc["is_flagged"] else 0
    score = calc["score"]

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
        fraud_score=score,
        device_id=device_id,
        ip_address=ip_addr,
        location=loc,
        card_last4=card4
    )
    db.add(db_transaction)
    await db.commit()
    await db.refresh(db_transaction)

    # Core Product Workflow (Section 3 & 4): Alert -> Case Conversion
    if is_fraud:
        case_num = f"CASE-{db_transaction.id + 1000}"
        db_case = Case(
            case_number=case_num,
            transaction_id=db_transaction.id,
            user_id=current_user.id,
            status=CaseStatus.NEW.value,
            risk_score=score,
            risk_level=calc["risk_level"],
            risk_factors=calc["risk_factors"]
        )
        db.add(db_case)
        await db.commit()
        await db.refresh(db_case)

        # Audit Trail: Initial Case Creation Event
        audit = CaseAuditLog(
            case_id=db_case.id,
            actor="RISK_ENGINE",
            actor_id="FinSight-RulesEngine-v2",
            action="CASE_CREATED",
            details=f"Suspicious transaction alert triggered (Risk Score: {score}/100, {calc['risk_level']}). New case {case_num} opened for investigation.",
            event_metadata={
                "risk_factors": calc["risk_factors"],
                "mcc_code": tx_dict["mcc_code"],
                "merchant": tx_dict["merchant"],
                "amount": tx_dict["amount"]
            }
        )
        db.add(audit)
        await db.commit()

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

    tx_dicts = []
    VERIFIED_KEYWORDS = ["mcdonald", "uber", "lyft", "amazon", "target", "walmart", "netflix", "spotify", "apple", "starbucks", "jio", "bigbasket", "dmart", "zomato", "apollo", "bookstore", "chipotle", "peet"]

    for row in csv_reader:
        amount = float(row.get("amount") or row.get("Amount") or 0.0)
        merchant = row.get("merchant") or row.get("Merchant") or row.get("description") or "Unknown Merchant"
        category = row.get("category") or row.get("Category") or "Other"
        date_str = row.get("date") or row.get("transaction_date") or row.get("Date") or datetime.now(timezone.utc).isoformat()

        try:
            tx_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception:
            tx_date = datetime.now(timezone.utc)

        merchant_lower = merchant.lower()
        is_verified = any(k in merchant_lower for k in VERIFIED_KEYWORDS) or row.get("is_verified", "").lower() in ["true", "1", "yes"]
        mcc = row.get("mcc_code") or row.get("mcc") or ("5814" if "food" in category.lower() else "5999")
        dev_id = row.get("device_id") or f"DEV-{random.randint(1000, 9999)}"
        ip_addr = row.get("ip_address") or f"198.51.100.{random.randint(2, 250)}"

        tx_dict = {
            "amount": abs(amount),
            "category": category,
            "merchant": merchant,
            "description": row.get("description", "Imported from Bank Statement"),
            "mcc_code": mcc,
            "is_merchant_verified": is_verified,
            "transaction_date": tx_date,
            "device_id": dev_id,
            "ip_address": ip_addr,
            "location": row.get("location", "Primary Jurisdiction")
        }
        tx_dicts.append(tx_dict)

    if not tx_dicts:
        raise HTTPException(status_code=400, detail="No valid transactions found in CSV statement.")

    db_items = []
    cases_to_create = []

    for tx_dict in tx_dicts:
        calc = fraud_detector.calculate_structured_risk(tx_dict, monthly_income_baseline=current_user.monthly_income)
        is_fraud = 1 if calc["is_flagged"] else 0
        score = calc["score"]

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
            fraud_score=score,
            device_id=tx_dict["device_id"],
            ip_address=tx_dict["ip_address"],
            location=tx_dict["location"]
        )
        db.add(db_tx)
        db_items.append((db_tx, calc))

    await db.commit()

    # Create cases for all flagged items
    for db_tx, calc in db_items:
        await db.refresh(db_tx)
        if db_tx.is_fraudulent:
            case_num = f"CASE-{db_tx.id + 1000}"
            db_case = Case(
                case_number=case_num,
                transaction_id=db_tx.id,
                user_id=current_user.id,
                status=CaseStatus.NEW.value,
                risk_score=calc["score"],
                risk_level=calc["risk_level"],
                risk_factors=calc["risk_factors"]
            )
            db.add(db_case)
            cases_to_create.append((db_case, case_num, calc))

    if cases_to_create:
        await db.commit()
        for db_case, case_num, calc in cases_to_create:
            await db.refresh(db_case)
            audit = CaseAuditLog(
                case_id=db_case.id,
                actor="RISK_ENGINE",
                actor_id="FinSight-RulesEngine-v2",
                action="CASE_CREATED",
                details=f"Statement ingestion alert triggered (Risk Score: {calc['score']}/100, {calc['risk_level']}). Case {case_num} opened.",
                event_metadata={"risk_factors": calc["risk_factors"]}
            )
            db.add(audit)
        await db.commit()

    return [item[0] for item in db_items]

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
    conditions = [Transaction.user_id == current_user.id]
    
    if category:
        conditions.append(Transaction.category == category)
    if start_date:
        conditions.append(Transaction.transaction_date >= start_date)
    if end_date:
        conditions.append(Transaction.transaction_date <= end_date)
    if min_amount is not None:
        conditions.append(Transaction.amount >= min_amount)
    if max_amount is not None:
        conditions.append(Transaction.amount <= max_amount)
        
    if search:
        search_filter = or_(
            Transaction.merchant.ilike(f"%{search}%"),
            Transaction.description.ilike(f"%{search}%")
        )
        conditions.append(search_filter)
        
    query_filter = and_(*conditions)
    
    count_stmt = select(func.count()).select_from(Transaction).where(query_filter)
    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0
    
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
