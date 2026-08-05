from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.transaction import Transaction
from app.schemas.user import AdminUserDetail, AdminPlatformStats
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/admin", tags=["Creator Admin"])

async def verify_admin(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin privileges required."
        )
    return current_user

@router.get("/users", response_model=List[AdminUserDetail])
async def get_all_users(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(verify_admin)
):
    # Fetch all users
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    
    user_details = []
    for user in users:
        # Count transactions for each user
        tx_count_res = await db.execute(
            select(func.count(Transaction.id)).filter(Transaction.user_id == user.id)
        )
        tx_count = tx_count_res.scalar() or 0
        
        user_details.append(
            AdminUserDetail(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                monthly_income=user.monthly_income,
                is_admin=user.is_admin,
                total_transactions=tx_count,
                last_login_at=user.last_login_at,
                created_at=user.created_at
            )
        )
        
    return user_details

@router.get("/stats", response_model=AdminPlatformStats)
async def get_platform_stats(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(verify_admin)
):
    # Total Users
    total_users_res = await db.execute(select(func.count(User.id)))
    total_users = total_users_res.scalar() or 0
    
    # Total Transactions
    total_tx_res = await db.execute(select(func.count(Transaction.id)))
    total_tx = total_tx_res.scalar() or 0
    
    # Total Flagged Anomalies
    total_anomalies_res = await db.execute(
        select(func.count(Transaction.id)).filter(Transaction.is_fraudulent == 1)
    )
    total_anomalies = total_anomalies_res.scalar() or 0
    
    # Total System Volume (sum of amounts)
    total_vol_res = await db.execute(select(func.sum(Transaction.amount)))
    total_vol = total_vol_res.scalar() or 0.0
    
    return AdminPlatformStats(
        total_users=total_users,
        total_transactions=total_tx,
        total_flagged_anomalies=total_anomalies,
        total_system_volume=round(total_vol, 2)
    )
