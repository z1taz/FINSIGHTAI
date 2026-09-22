from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_, and_
from typing import Optional, List
from datetime import datetime

from app.database import get_db
from app.models.case import Case, CaseAuditLog, AgentInvestigationRun, CaseStatus, RiskLevel
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.case import (
    CaseSummaryResponse,
    CaseDetailResponse,
    PaginatedCases,
    HumanDecisionRequest,
    AuditLogResponse,
    InvestigationRunResponse
)
from app.services.auth_service import get_current_user
from app.services.investigation_agent import investigation_agent
from app.services.fraud_detector import fraud_detector

router = APIRouter(prefix="/cases", tags=["Case Management & Risk Operations"])

@router.get("", response_model=PaginatedCases)
async def list_cases(
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    status: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    min_score: Optional[float] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List investigation cases with queue filters for risk operators.
    """
    conditions = []
    
    # Filter by user if not admin
    if not current_user.is_admin:
        conditions.append(Case.user_id == current_user.id)
        
    if status:
        conditions.append(Case.status == status)
    if risk_level:
        conditions.append(Case.risk_level == risk_level)
    if min_score is not None:
        conditions.append(Case.risk_score >= min_score)
        
    base_query = (
        select(Case, Transaction, User)
        .join(Transaction, Case.transaction_id == Transaction.id)
        .join(User, Case.user_id == User.id)
    )
    
    if search:
        search_filter = or_(
            Case.case_number.ilike(f"%{search}%"),
            Transaction.merchant.ilike(f"%{search}%"),
            User.full_name.ilike(f"%{search}%"),
            Transaction.category.ilike(f"%{search}%")
        )
        conditions.append(search_filter)
        
    if conditions:
        base_query = base_query.where(and_(*conditions))
        
    # Count total
    count_stmt = select(func.count(Case.id)).select_from(Case)
    if conditions:
        count_stmt = count_stmt.join(Transaction, Case.transaction_id == Transaction.id).join(User, Case.user_id == User.id).where(and_(*conditions))
    count_res = await db.execute(count_stmt)
    total = count_res.scalar() or 0
    
    # Paginate and order by risk_score desc, then created_at desc
    paged_stmt = (
        base_query
        .order_by(Case.risk_score.desc(), Case.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    res = await db.execute(paged_stmt)
    rows = res.all()
    
    items = []
    for c, t, u in rows:
        items.append({
            "id": c.id,
            "case_number": c.case_number,
            "transaction_id": c.transaction_id,
            "user_id": c.user_id,
            "customer_name": u.full_name,
            "amount": t.amount,
            "merchant": t.merchant,
            "category": t.category,
            "status": c.status,
            "risk_score": c.risk_score,
            "risk_level": c.risk_level,
            "risk_factors": c.risk_factors or [],
            "ai_recommendation": c.ai_recommendation,
            "human_decision": c.human_decision,
            "created_at": c.created_at,
            "updated_at": c.updated_at
        })
        
    pages = (total + limit - 1) // limit
    return {
        "items": items,
        "total": total,
        "page": page,
        "pages": pages,
        "limit": limit
    }

@router.get("/stats/overview")
async def get_cases_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get executive risk metrics for the cases queue.
    """
    user_filter = []
    if not current_user.is_admin:
        user_filter.append(Case.user_id == current_user.id)
        
    stmt = (
        select(
            func.count(Case.id).label("total_cases"),
            func.sum(func.case((Case.status == CaseStatus.NEW.value, 1), else_=0)).label("new_cases"),
            func.sum(func.case((Case.status.in_([CaseStatus.AI_REVIEWED.value, CaseStatus.PENDING_HUMAN_DECISION.value]), 1), else_=0)).label("pending_decision"),
            func.sum(func.case((Case.status == CaseStatus.CONFIRMED_FRAUD.value, 1), else_=0)).label("confirmed_fraud"),
            func.sum(func.case((Case.status == CaseStatus.FALSE_POSITIVE.value, 1), else_=0)).label("false_positives"),
            func.sum(func.case((Case.status == CaseStatus.ESCALATED.value, 1), else_=0)).label("escalated"),
            func.avg(Case.risk_score).label("avg_risk_score")
        )
    )
    if user_filter:
        stmt = stmt.where(and_(*user_filter))
        
    res = await db.execute(stmt)
    total, new_c, pending, confirmed, fp, escalated, avg_score = res.first()
    
    total = total or 0
    confirmed = confirmed or 0
    fp = fp or 0
    resolved = confirmed + fp
    fp_rate = (fp / resolved * 100.0) if resolved > 0 else 0.0

    return {
        "total_cases": total,
        "new_alerts": new_c or 0,
        "pending_human_decision": pending or 0,
        "confirmed_fraud": confirmed,
        "false_positives": fp,
        "escalated_cases": escalated or 0,
        "false_positive_rate_pct": round(fp_rate, 1),
        "average_risk_score": round(float(avg_score or 0.0), 1)
    }

@router.get("/{case_id}", response_model=CaseDetailResponse)
async def get_case_detail(
    case_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve comprehensive case investigation workspace payload.
    """
    stmt = (
        select(Case, Transaction, User)
        .join(Transaction, Case.transaction_id == Transaction.id)
        .join(User, Case.user_id == User.id)
        .where(Case.id == case_id)
    )
    res = await db.execute(stmt)
    row = res.first()
    if not row:
        raise HTTPException(status_code=404, detail="Case not found.")
        
    case, tx, user = row
    
    if not current_user.is_admin and case.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized access to this investigation case.")
        
    # Get audit logs
    audit_stmt = (
        select(CaseAuditLog)
        .where(CaseAuditLog.case_id == case_id)
        .order_by(CaseAuditLog.timestamp.desc())
    )
    audit_res = await db.execute(audit_stmt)
    audit_logs = audit_res.scalars().all()
    
    # Get latest investigation run
    run_stmt = (
        select(AgentInvestigationRun)
        .where(AgentInvestigationRun.case_id == case_id)
        .order_by(AgentInvestigationRun.created_at.desc())
    )
    run_res = await db.execute(run_stmt)
    latest_run = run_res.scalars().first()
    
    # Calculate feature sensitivity counterfactuals dynamically from current tx
    tx_dict = {
        "amount": tx.amount,
        "category": tx.category,
        "merchant": tx.merchant,
        "mcc_code": tx.mcc_code,
        "is_merchant_verified": tx.is_merchant_verified,
        "device_id": tx.device_id,
        "location": tx.location
    }
    calc = fraud_detector.calculate_structured_risk(tx_dict, monthly_income_baseline=user.monthly_income)
    
    tx_snapshot = {
        "id": tx.id,
        "amount": tx.amount,
        "category": tx.category,
        "merchant": tx.merchant,
        "description": tx.description,
        "mcc_code": tx.mcc_code,
        "is_merchant_verified": tx.is_merchant_verified,
        "transaction_date": tx.transaction_date.isoformat() if tx.transaction_date else None,
        "device_id": tx.device_id or "DEV-8201",
        "ip_address": tx.ip_address or "198.51.100.12",
        "location": tx.location or "Primary Jurisdiction",
        "card_last4": tx.card_last4 or "4821",
        "fraud_score": tx.fraud_score
    }

    return {
        "id": case.id,
        "case_number": case.case_number,
        "transaction_id": case.transaction_id,
        "user_id": case.user_id,
        "customer_name": user.full_name,
        "status": case.status,
        "risk_score": case.risk_score,
        "risk_level": case.risk_level,
        "risk_factors": case.risk_factors or calc.get("risk_factors", []),
        "counterfactuals": calc.get("counterfactuals", []),
        "transaction": tx_snapshot,
        "ai_recommendation": case.ai_recommendation,
        "ai_confidence": case.ai_confidence,
        "ai_reasoning_summary": case.ai_reasoning_summary,
        "ai_investigated_at": case.ai_investigated_at,
        "human_decision": case.human_decision,
        "human_notes": case.human_notes,
        "decided_by": case.decided_by,
        "decided_at": case.decided_at,
        "audit_logs": audit_logs,
        "latest_investigation": latest_run,
        "created_at": case.created_at,
        "updated_at": case.updated_at
    }

@router.post("/{case_id}/investigate", response_model=InvestigationRunResponse)
async def trigger_ai_investigation(
    case_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger the Autonomous Investigation Agent on a specific case.
    Executes controlled read-only tools, gathers evidence, searches policy, and returns recommendation.
    """
    try:
        run = await investigation_agent.investigate_case(case_id, db)
        return run
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Investigation failed: {str(e)}")

@router.post("/{case_id}/decide", response_model=CaseDetailResponse)
async def submit_human_decision(
    case_id: int,
    body: HumanDecisionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit investigator's binding decision (CONFIRM_FRAUD, FALSE_POSITIVE, ESCALATE, REQUEST_MORE_INFO)
    and permanently record to the case audit trail.
    """
    valid_decisions = ["CONFIRM_FRAUD", "FALSE_POSITIVE", "ESCALATE", "REQUEST_MORE_INFO"]
    if body.decision not in valid_decisions:
        raise HTTPException(status_code=400, detail=f"Invalid decision. Must be one of: {valid_decisions}")
        
    try:
        updated_case = await investigation_agent.record_human_decision(
            case_id=case_id,
            decision=body.decision,
            investigator_id=current_user.email,
            notes=body.notes or "",
            db=db
        )
        return await get_case_detail(case_id, current_user, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{case_id}/audit-trail", response_model=List[AuditLogResponse])
async def get_audit_trail(
    case_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get full, chronologically ordered case audit trail.
    """
    stmt = (
        select(CaseAuditLog)
        .where(CaseAuditLog.case_id == case_id)
        .order_by(CaseAuditLog.timestamp.asc())
    )
    res = await db.execute(stmt)
    return res.scalars().all()
