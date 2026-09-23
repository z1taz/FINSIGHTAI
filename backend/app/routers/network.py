from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List

from app.database import get_db
from app.models.user import User
from app.services.auth_service import get_current_user
from app.services.network_intelligence import network_intelligence

router = APIRouter(prefix="/network", tags=["Relationship & Network Intelligence"])

@router.get("/graph")
async def get_network_graph(
    limit: int = Query(60, ge=10, le=150),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve force-directed graph data representing relationships between
    Customers, Devices, IP addresses, and Merchants.
    """
    return await network_intelligence.get_network_graph(db, limit_nodes=limit)

@router.get("/clusters")
async def get_emerging_clusters(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Surface detected emerging anomaly clusters, hardware collisions,
    and merchant concentration rings.
    """
    return await network_intelligence.detect_emerging_fraud_clusters(db)
