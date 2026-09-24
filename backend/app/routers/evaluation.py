from fastapi import APIRouter, Depends
from typing import Dict, Any

from app.models.user import User
from app.services.auth_service import get_current_user
from app.services.evaluation_service import evaluation_service

router = APIRouter(prefix="/evaluation", tags=["Evaluation & Benchmark Suite"])

@router.get("/results")
async def get_latest_evaluation_results(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get latest empirical evaluation metrics measured on the standard benchmark dataset.
    """
    return evaluation_service.evaluate_benchmark()

@router.post("/run")
async def run_evaluation_benchmark(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Re-run the complete evaluation harness across all test cases.
    """
    return evaluation_service.evaluate_benchmark()
