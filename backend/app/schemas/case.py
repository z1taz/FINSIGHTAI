from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class RiskFactorSchema(BaseModel):
    factor: str
    points: float
    category: str
    description: str

class CounterfactualSchema(BaseModel):
    scenario: str
    estimated_risk_score: float
    delta: float

class AuditLogResponse(BaseModel):
    id: int
    actor: str
    actor_id: Optional[str] = None
    action: str
    details: str
    event_metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime

    class Config:
        from_attributes = True

class InvestigationRunResponse(BaseModel):
    id: int
    run_id: str
    status: str
    recommendation: str
    abstained: bool
    reasoning_summary: str
    observed_evidence: List[Dict[str, Any]]
    retrieved_policies: List[Dict[str, Any]]
    similar_cases: List[Dict[str, Any]]
    tool_calls: List[Dict[str, Any]]
    total_latency_ms: float
    model_version: str
    created_at: datetime

    class Config:
        from_attributes = True

class CaseSummaryResponse(BaseModel):
    id: int
    case_number: str
    transaction_id: int
    user_id: int
    customer_name: Optional[str] = None
    amount: float
    merchant: str
    category: str
    status: str
    risk_score: float
    risk_level: str
    risk_factors: List[Dict[str, Any]]
    ai_recommendation: Optional[str] = None
    human_decision: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class CaseDetailResponse(BaseModel):
    id: int
    case_number: str
    transaction_id: int
    user_id: int
    customer_name: Optional[str] = None
    status: str
    risk_score: float
    risk_level: str
    risk_factors: List[Dict[str, Any]]
    counterfactuals: List[Dict[str, Any]] = []
    
    # Transaction snapshot
    transaction: Dict[str, Any]
    
    # AI state
    ai_recommendation: Optional[str] = None
    ai_confidence: Optional[float] = None
    ai_reasoning_summary: Optional[str] = None
    ai_investigated_at: Optional[datetime] = None
    
    # Human state
    human_decision: Optional[str] = None
    human_notes: Optional[str] = None
    decided_by: Optional[str] = None
    decided_at: Optional[datetime] = None
    
    # History & Investigation
    audit_logs: List[AuditLogResponse] = []
    latest_investigation: Optional[InvestigationRunResponse] = None
    
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class HumanDecisionRequest(BaseModel):
    decision: str = Field(..., description="CONFIRM_FRAUD | FALSE_POSITIVE | ESCALATE | REQUEST_MORE_INFO")
    notes: Optional[str] = ""

class PaginatedCases(BaseModel):
    items: List[CaseSummaryResponse]
    total: int
    page: int
    pages: int
    limit: int
