from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON, Index, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base

class CaseStatus(str, enum.Enum):
    NEW = "NEW"
    INVESTIGATING = "INVESTIGATING"
    AI_REVIEWED = "AI_REVIEWED"
    PENDING_HUMAN_DECISION = "PENDING_HUMAN_DECISION"
    ESCALATED = "ESCALATED"
    CONFIRMED_FRAUD = "CONFIRMED_FRAUD"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    CLOSED = "CLOSED"

class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    case_number = Column(String(32), unique=True, index=True, nullable=False) # e.g. CASE-1042
    transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    status = Column(String(32), default=CaseStatus.NEW.value, nullable=False, index=True)
    risk_score = Column(Float, default=0.0, nullable=False) # 0 to 100
    risk_level = Column(String(16), default=RiskLevel.MEDIUM.value, nullable=False)
    
    # Structured breakdown of calculated risk factors
    # e.g. [{"factor": "New Device", "points": 42, "category": "device", "description": "Device observed for first time"}]
    risk_factors = Column(JSON, default=list, nullable=False)
    
    # Investigation & Decision state
    ai_recommendation = Column(String(64), nullable=True) # CONFIRM_FRAUD, FALSE_POSITIVE, ESCALATE, REQUEST_MORE_INFO, ABSTAIN
    ai_confidence = Column(Float, nullable=True)
    ai_reasoning_summary = Column(Text, nullable=True)
    ai_investigated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Human decision
    human_decision = Column(String(64), nullable=True)
    human_notes = Column(Text, nullable=True)
    decided_by = Column(String(128), nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=True)
    
    # Audit & timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    transaction = relationship("Transaction", back_populates="case")
    user = relationship("User", backref="cases")
    audit_logs = relationship("CaseAuditLog", back_populates="case", cascade="all, delete-orphan", order_by="CaseAuditLog.timestamp.asc()")
    investigation_runs = relationship("AgentInvestigationRun", back_populates="case", cascade="all, delete-orphan", order_by="AgentInvestigationRun.created_at.desc()")


class CaseAuditLog(Base):
    __tablename__ = "case_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    actor = Column(String(64), nullable=False) # "RISK_ENGINE", "AI_AGENT", "INVESTIGATOR", "SYSTEM"
    actor_id = Column(String(128), nullable=True) # e.g. investigator email or model version
    action = Column(String(128), nullable=False) # e.g. "CASE_CREATED", "TOOL_EXECUTED", "RECOMMENDATION_GENERATED", "HUMAN_DECISION_RECORDED"
    details = Column(Text, nullable=False)
    event_metadata = Column(JSON, default=dict, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    case = relationship("Case", back_populates="audit_logs")


class AgentInvestigationRun(Base):
    __tablename__ = "agent_investigation_runs"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(40), unique=True, index=True, nullable=False) # UUID
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Investigation lifecycle & trace
    status = Column(String(32), default="COMPLETED", nullable=False)
    recommendation = Column(String(64), nullable=False)
    abstained = Column(Boolean, default=False, nullable=False)
    reasoning_summary = Column(Text, nullable=False)
    
    # Grounded evidence & policies
    observed_evidence = Column(JSON, default=list, nullable=False)
    retrieved_policies = Column(JSON, default=list, nullable=False)
    similar_cases = Column(JSON, default=list, nullable=False)
    
    # Observability & telemetry
    tool_calls = Column(JSON, default=list, nullable=False) # [{tool: str, args: dict, latency_ms: float, success: bool}]
    total_latency_ms = Column(Float, default=0.0, nullable=False)
    model_version = Column(String(64), default="FinSight-Agent-v1.0", nullable=False)
    token_usage = Column(JSON, default=dict, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    case = relationship("Case", back_populates="investigation_runs")
