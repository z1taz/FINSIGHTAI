from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List

from app.database import get_db
from app.models.user import User
from app.services.auth_service import get_current_user
from app.services.governance_service import governance_service

router = APIRouter(prefix="/governance", tags=["Model Governance & Product Metrics"])

@router.get("/models")
async def get_model_registry(
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Get registered fraud detection and investigation models with governance compliance terms.
    """
    return governance_service.get_model_registry()

@router.get("/versions")
async def get_agent_version_history(
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Get evolution of agent versions with benchmark evaluation scores.
    """
    return governance_service.get_agent_versions()

@router.get("/product-metrics")
async def get_product_metrics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get actual measured product-level operational metrics (Section 19).
    """
    return await governance_service.get_product_metrics(db)
