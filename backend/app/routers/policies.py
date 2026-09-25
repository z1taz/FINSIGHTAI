from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Dict, Any, List

from app.database import get_db
from app.models.user import User
from app.services.auth_service import get_current_user
from app.services.policy_simulator import policy_simulator
from app.services.investigation_agent import POLICIES

router = APIRouter(prefix="/policies", tags=["Policies & Policy Simulation"])

class PolicySimulationRequest(BaseModel):
    amount_threshold: float = 3000.0
    income_ratio_threshold: float = 0.50
    flag_unverified_merchants: bool = True

@router.get("")
async def get_all_policies(
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Retrieve institutional fraud policy knowledge base.
    """
    return POLICIES

@router.post("/simulate")
async def simulate_policy(
    body: PolicySimulationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Simulate adjusting risk policy thresholds against the dataset to measure
    actual trade-offs in alerts generated vs. investigator workload.
    """
    return await policy_simulator.simulate_policy_change(
        amount_threshold=body.amount_threshold,
        income_ratio_threshold=body.income_ratio_threshold,
        flag_unverified_merchants=body.flag_unverified_merchants,
        db=db
    )
