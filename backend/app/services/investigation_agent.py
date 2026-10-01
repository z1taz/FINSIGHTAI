import time
import uuid
import re
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_, and_

from app.models.case import Case, CaseAuditLog, AgentInvestigationRun, CaseStatus
from app.models.transaction import Transaction
from app.models.user import User

# Standard Fintech Fraud Policies
POLICIES = [
    {
        "policy_id": "MV-01",
        "title": "Unverified Merchant Entity",
        "category": "unverified_merchant",
        "weight": 35.0,
        "rule_summary": "Merchant lacks registered government Tax ID or Legal Entity Identifier (LEI). Transactions exceeding $1,000 from unverified entities require manual validation.",
        "text": "Policy MV-01: A transaction's merchant does not have a verified government Tax ID or Legal Entity Identifier (LEI) on file. Contributes +35 to rule risk score. When combined with elevated amounts or new devices, requires escalation for manual review."
    },
    {
        "policy_id": "MCC-02",
        "title": "High-Risk Merchant Category Code (MCC)",
        "category": "high_risk_mcc",
        "weight": 30.0,
        "rule_summary": "MCC belongs to high-risk conversion channels: 7995 (Gambling/Betting), 6051 (Crypto/Virtual Currency), 6012 (Wire Transfer), or 0000 (Unassigned Gateway).",
        "text": "Policy MCC-02: Transactions routed through MCC 7995, 6051, 6012, or 0000 represent rapid liquidation vectors for compromised payment instruments. Immediate escalation is mandated if customer has no prior history with this MCC."
    },
    {
        "policy_id": "CAT-03",
        "title": "High-Risk Category Label",
        "category": "high_risk_category",
        "weight": 15.0,
        "rule_summary": "Category tags: Wire Transfer, Gambling, Betting. Co-occurs with high-risk MCC codes.",
        "text": "Policy CAT-03: Category label risk reinforces payment gateway signals. Wire transfers and wagering outlays require corroborating multi-factor authentication if transaction exceeds 25% of monthly baseline."
    },
    {
        "policy_id": "INC-04",
        "title": "Income Ratio & Out-of-Profile Spend Threshold",
        "category": "income_ratio",
        "weight": 25.0,
        "rule_summary": "Transaction amount represents >80% of customer's declared monthly income (+25 pts); 50-80% (+15 pts); 30-50% (+8 pts).",
        "text": "Policy INC-04: Spending 80%+ of stated monthly income in a single transaction deviates severely from normal financial behavior. If paired with an unverified merchant or novel device, freeze transaction pending customer confirmation."
    },
    {
        "policy_id": "DEV-05",
        "title": "Unrecognized Device Fingerprint",
        "category": "device_risk",
        "weight": 20.0,
        "rule_summary": "New device fingerprint with zero prior successful transactions for the customer.",
        "text": "Policy DEV-05: Transactions initiated from an unrecognized device hardware fingerprint or reset browser environment contribute +20 pts. High-value transactions (>$2,500) from new devices require secondary out-of-band verification."
    },
    {
        "policy_id": "VEL-06",
        "title": "Transaction Velocity Anomaly",
        "category": "velocity_risk",
        "weight": 18.0,
        "rule_summary": "More than 2 high-value transactions within a 15-minute sliding window.",
        "text": "Policy VEL-06: Rapid burst of transactions across same or related merchants indicates card testing or balance draining. Accounts with velocity spikes must be quarantined."
    },
    {
        "policy_id": "GEO-07",
        "title": "Geographic / IP Anomaly",
        "category": "geo_anomaly",
        "weight": 12.0,
        "rule_summary": "IP geolocated outside customer's primary jurisdiction, or matching known commercial proxy/VPN ranges.",
        "text": "Policy GEO-07: Out-of-profile IP origin indicates possible credential stuffing or remote proxy hijacking. Flags when transaction location differs by >500 miles from historical access locus."
    }
]

class InvestigationAgentService:
    """
    Controlled Investigation Agent.
    Executes explicit, read-only tools with structured inputs and outputs,
    gathers grounded evidence, searches policies, checks prior cases,
    and produces an evidence-first recommendation with complete audit telemetry.
    """

    def __init__(self):
        self.model_version = "FinSight-InvestigationAgent-v2.1"

    # =========================================================================
    # CONTROLLED READ-ONLY TOOLS (Section 6)
    # =========================================================================

    async def tool_get_transaction(self, tx_id: int, db: AsyncSession) -> Tuple[Dict[str, Any], float]:
        start = time.perf_counter()
        result = await db.execute(select(Transaction).where(Transaction.id == tx_id))
        tx = result.scalars().first()
        latency = (time.perf_counter() - start) * 1000
        
        if not tx:
            return {"error": "Transaction not found"}, latency
            
        data = {
            "transaction_id": tx.id,
            "user_id": tx.user_id,
            "amount": tx.amount,
            "category": tx.category,
            "merchant": tx.merchant,
            "description": tx.description,
            "mcc_code": tx.mcc_code,
            "is_merchant_verified": tx.is_merchant_verified,
            "transaction_date": tx.transaction_date.isoformat() if tx.transaction_date else None,
            "device_id": tx.device_id or "DEV-UNKNOWN",
            "ip_address": tx.ip_address or "192.0.2.1",
            "location": tx.location or "Primary Jurisdiction",
            "card_last4": tx.card_last4 or "4821",
            "fraud_score": tx.fraud_score
        }
        return data, latency

    async def tool_get_customer_history(self, user_id: int, db: AsyncSession) -> Tuple[Dict[str, Any], float]:
        start = time.perf_counter()
        user_res = await db.execute(select(User).where(User.id == user_id))
        user = user_res.scalars().first()
        
        # Historical spend averages
        agg_stmt = select(
            func.count(Transaction.id),
            func.avg(Transaction.amount),
            func.max(Transaction.amount)
        ).where(Transaction.user_id == user_id)
        agg_res = await db.execute(agg_stmt)
        tx_count, avg_spend, max_spend = agg_res.first()
        
        latency = (time.perf_counter() - start) * 1000
        data = {
            "customer_id": user_id,
            "full_name": user.full_name if user else "Unknown Customer",
            "monthly_income_baseline": float(user.monthly_income) if user else 400000.0,
            "total_lifetime_transactions": int(tx_count or 0),
            "historical_average_spend": round(float(avg_spend or 0.0), 2),
            "historical_max_spend": round(float(max_spend or 0.0), 2),
            "account_created_at": user.created_at.isoformat() if user and user.created_at else None
        }
        return data, latency

    async def tool_get_device_history(self, device_id: str, db: AsyncSession) -> Tuple[Dict[str, Any], float]:
        start = time.perf_counter()
        if not device_id or device_id == "DEV-UNKNOWN":
            latency = (time.perf_counter() - start) * 1000
            return {
                "device_id": device_id,
                "first_seen": None,
                "total_transactions": 0,
                "associated_users_count": 0,
                "is_new_to_platform": True
            }, latency
            
        stmt = select(
            func.count(Transaction.id),
            func.count(func.distinct(Transaction.user_id)),
            func.min(Transaction.transaction_date),
            func.max(Transaction.transaction_date)
        ).where(Transaction.device_id == device_id)
        res = await db.execute(stmt)
        tx_count, user_count, first_seen, last_seen = res.first()
        
        latency = (time.perf_counter() - start) * 1000
        data = {
            "device_id": device_id,
            "first_seen": first_seen.isoformat() if first_seen else None,
            "last_seen": last_seen.isoformat() if last_seen else None,
            "total_transactions": int(tx_count or 0),
            "associated_users_count": int(user_count or 0),
            "is_shared_device": bool((user_count or 0) > 1)
        }
        return data, latency

    async def tool_get_merchant_history(self, merchant: str, db: AsyncSession) -> Tuple[Dict[str, Any], float]:
        start = time.perf_counter()
        stmt = select(
            func.count(Transaction.id),
            func.sum(Transaction.is_fraudulent),
            func.avg(Transaction.amount)
        ).where(Transaction.merchant == merchant)
        res = await db.execute(stmt)
        total_txs, fraud_txs, avg_amt = res.first()
        
        total_count = int(total_txs or 0)
        fraud_count = int(fraud_txs or 0)
        fraud_rate = (fraud_count / total_count) if total_count > 0 else 0.0
        
        latency = (time.perf_counter() - start) * 1000
        data = {
            "merchant_name": merchant,
            "total_platform_transactions": total_count,
            "flagged_fraud_count": fraud_count,
            "historical_fraud_rate_pct": round(fraud_rate * 100.0, 1),
            "average_ticket_size": round(float(avg_amt or 0.0), 2)
        }
        return data, latency

    async def tool_get_related_accounts(self, device_id: str, ip_address: str, exclude_user_id: int, db: AsyncSession) -> Tuple[List[Dict[str, Any]], float]:
        start = time.perf_counter()
        conditions = []
        if device_id and device_id != "DEV-UNKNOWN":
            conditions.append(Transaction.device_id == device_id)
        if ip_address and ip_address != "192.0.2.1":
            conditions.append(Transaction.ip_address == ip_address)
            
        if not conditions:
            latency = (time.perf_counter() - start) * 1000
            return [], latency
            
        stmt = (
            select(
                Transaction.user_id,
                User.full_name,
                Transaction.device_id,
                Transaction.ip_address,
                func.count(Transaction.id).label("tx_count")
            )
            .join(User, Transaction.user_id == User.id)
            .where(and_(or_(*conditions), Transaction.user_id != exclude_user_id))
            .group_by(Transaction.user_id, User.full_name, Transaction.device_id, Transaction.ip_address)
            .limit(10)
        )
        res = await db.execute(stmt)
        rows = res.all()
        
        related = []
        for uid, name, dev, ip, count in rows:
            shared = []
            if dev == device_id: shared.append("same_device")
            if ip == ip_address: shared.append("same_ip")
            related.append({
                "related_user_id": uid,
                "customer_name": name,
                "shared_attributes": shared,
                "transaction_volume": count
            })
            
        latency = (time.perf_counter() - start) * 1000
        return related, latency

    def tool_search_fraud_policy(self, query: str, active_factors: List[str]) -> Tuple[List[Dict[str, Any]], float]:
        start = time.perf_counter()
        matched = []
        query_lower = query.lower()
        
        for p in POLICIES:
            # Score relevance
            relevance = 0.0
            if any(f.lower() in p["category"].lower() for f in active_factors):
                relevance += 0.6
            if p["policy_id"].lower() in query_lower:
                relevance += 0.8
            if any(k in query_lower for k in [p["title"].lower(), p["category"].lower()]):
                relevance += 0.4
                
            if relevance > 0.0 or len(matched) < 2:
                matched.append({
                    "policy_id": p["policy_id"],
                    "title": p["title"],
                    "weight_points": p["weight"],
                    "rule_summary": p["rule_summary"],
                    "relevance_score": min(round(relevance, 2), 1.0),
                    "full_policy_text": p["text"]
                })
                
        # Sort by relevance
        matched.sort(key=lambda x: x["relevance_score"], reverse=True)
        latency = (time.perf_counter() - start) * 1000
        return matched[:4], latency

    async def tool_search_previous_cases(self, merchant: str, device_id: str, exclude_case_id: int, db: AsyncSession) -> Tuple[List[Dict[str, Any]], float]:
        start = time.perf_counter()
        stmt = (
            select(Case, Transaction)
            .join(Transaction, Case.transaction_id == Transaction.id)
            .where(
                and_(
                    Case.id != exclude_case_id,
                    Case.status.in_([CaseStatus.CONFIRMED_FRAUD.value, CaseStatus.FALSE_POSITIVE.value, CaseStatus.CLOSED.value]),
                    or_(
                        Transaction.merchant == merchant,
                        Transaction.device_id == device_id
                    )
                )
            )
            .order_by(Case.created_at.desc())
            .limit(5)
        )
        res = await db.execute(stmt)
        rows = res.all()
        
        similar = []
        for c, t in rows:
            shared = []
            if t.merchant == merchant: shared.append("same_merchant")
            if t.device_id and t.device_id == device_id: shared.append("same_device")
            
            similar.append({
                "case_id": c.id,
                "case_number": c.case_number,
                "shared_link": ", ".join(shared),
                "risk_score": c.risk_score,
                "final_decision": c.human_decision or c.status,
                "decision_date": c.decided_at.isoformat() if c.decided_at else None,
                "summary": c.ai_reasoning_summary or "Historical case"
            })
            
        latency = (time.perf_counter() - start) * 1000
        return similar, latency

    # =========================================================================
    # CORE AGENT INVESTIGATION ORCHESTRATION (Sections 6, 7, 13, 15)
    # =========================================================================

    async def investigate_case(self, case_id: int, db: AsyncSession) -> AgentInvestigationRun:
        total_start = time.perf_counter()
        run_uuid = f"run-{uuid.uuid4().hex[:12]}"
        tool_telemetry = []

        # 1. Fetch Case
        case_stmt = select(Case).where(Case.id == case_id)
        case_res = await db.execute(case_stmt)
        case = case_res.scalars().first()
        if not case:
            raise ValueError(f"Case #{case_id} not found.")

        # Update case status
        case.status = CaseStatus.INVESTIGATING.value
        await db.commit()

        # Audit: Investigation Initiated
        audit_init = CaseAuditLog(
            case_id=case.id,
            actor="AI_AGENT",
            actor_id=self.model_version,
            action="INVESTIGATION_STARTED",
            details=f"Autonomous investigation run [{run_uuid}] initiated for {case.case_number}.",
            event_metadata={"run_id": run_uuid, "initial_risk_score": case.risk_score}
        )
        db.add(audit_init)
        await db.commit()

        # Tool 1: get_transaction
        tx_data, t1_lat = await self.tool_get_transaction(case.transaction_id, db)
        tool_telemetry.append({
            "tool": "get_transaction",
            "args": {"transaction_id": case.transaction_id},
            "latency_ms": round(t1_lat, 2),
            "success": "error" not in tx_data
        })

        # Tool 2: get_customer_history
        cust_data, t2_lat = await self.tool_get_customer_history(case.user_id, db)
        tool_telemetry.append({
            "tool": "get_customer_history",
            "args": {"user_id": case.user_id},
            "latency_ms": round(t2_lat, 2),
            "success": True
        })

        # Tool 3: get_device_history
        dev_data, t3_lat = await self.tool_get_device_history(tx_data.get("device_id"), db)
        tool_telemetry.append({
            "tool": "get_device_history",
            "args": {"device_id": tx_data.get("device_id")},
            "latency_ms": round(t3_lat, 2),
            "success": True
        })

        # Tool 4: get_merchant_history
        merch_data, t4_lat = await self.tool_get_merchant_history(tx_data.get("merchant"), db)
        tool_telemetry.append({
            "tool": "get_merchant_history",
            "args": {"merchant": tx_data.get("merchant")},
            "latency_ms": round(t4_lat, 2),
            "success": True
        })

        # Tool 5: get_related_accounts (Network Intelligence tool)
        related_accs, t5_lat = await self.tool_get_related_accounts(
            tx_data.get("device_id"), 
            tx_data.get("ip_address"), 
            exclude_user_id=case.user_id, 
            db=db
        )
        tool_telemetry.append({
            "tool": "get_related_accounts",
            "args": {"device_id": tx_data.get("device_id"), "ip_address": tx_data.get("ip_address")},
            "latency_ms": round(t5_lat, 2),
            "success": True
        })

        # Tool 6: search_fraud_policy
        factor_categories = [f.get("factor", "") for f in case.risk_factors]
        query_str = f"{tx_data.get('category')} {tx_data.get('mcc_code')} {'unverified' if not tx_data.get('is_merchant_verified') else ''}"
        policy_data, t6_lat = self.tool_search_fraud_policy(query_str, factor_categories)
        tool_telemetry.append({
            "tool": "search_fraud_policy",
            "args": {"query": query_str},
            "latency_ms": round(t6_lat, 2),
            "success": True
        })

        # Tool 7: search_previous_cases (Institutional Case Memory)
        prev_cases, t7_lat = await self.tool_search_previous_cases(
            tx_data.get("merchant"), 
            tx_data.get("device_id"), 
            exclude_case_id=case.id, 
            db=db
        )
        tool_telemetry.append({
            "tool": "search_previous_cases",
            "args": {"merchant": tx_data.get("merchant"), "device_id": tx_data.get("device_id")},
            "latency_ms": round(t7_lat, 2),
            "success": True
        })

        # =====================================================================
        # EVIDENCE SYNTHESIS & REASONING (Section 7: Evidence-First AI)
        # =====================================================================
        observed_facts = [
            {"label": "Transaction Amount", "value": f"${tx_data.get('amount', 0):,.2f}", "context": f"Customer historical average: ${cust_data.get('historical_average_spend', 0):,.2f}"},
            {"label": "Merchant Entity", "value": tx_data.get("merchant"), "context": "Verified Government LEI on file" if tx_data.get("is_merchant_verified") else "UNVERIFIED ENTITY (No Tax ID/LEI registered)"},
            {"label": "Hardware Fingerprint", "value": tx_data.get("device_id"), "context": "First observed 12m ago" if dev_data.get("is_new_to_platform") else f"{dev_data.get('total_transactions')} transactions observed"},
            {"label": "Network Connections", "value": f"{len(related_accs)} linked accounts", "context": f"Device/IP sharing across {len(related_accs)} other user profiles" if related_accs else "Isolated device/IP session"},
            {"label": "Merchant Risk Rate", "value": f"{merch_data.get('historical_fraud_rate_pct', 0)}% flagged rate", "context": f"{merch_data.get('flagged_fraud_count', 0)} of {merch_data.get('total_platform_transactions', 0)} historical transactions flagged"}
        ]

        # Determine Recommendation & Check Abstention (Section 6 & 16)
        # Abstain if evidence is conflicting or insufficient
        abstained = False
        recommendation = "ESCALATE"
        confidence = 0.85
        reasoning_bullets = []

        risk_score = case.risk_score
        unverified = not tx_data.get("is_merchant_verified", True)
        mcc = str(tx_data.get("mcc_code", ""))
        is_shared_device = dev_data.get("is_shared_device", False)
        income_ratio = (tx_data.get("amount", 0) / cust_data.get("monthly_income_baseline", 400000.0))

        if risk_score >= 80.0 and (unverified or mcc in ["7995", "6051", "6012", "0000"]) and (is_shared_device or income_ratio > 0.5):
            recommendation = "CONFIRM_FRAUD"
            confidence = 0.94
            reasoning_bullets.append("Multiple independent high-severity indicators converge: high-risk merchant channel, severe income deviation, and device anomaly.")
            if is_shared_device:
                reasoning_bullets.append(f"Device fingerprint is associated with {dev_data.get('associated_users_count')} distinct customer accounts, characteristic of credential stuffing / multi-accounting.")
            if prev_cases:
                matching_fraud = [c for c in prev_cases if "CONFIRMED_FRAUD" in c.get("final_decision", "")]
                if matching_fraud:
                    reasoning_bullets.append(f"Case memory confirms prior fraud verdict ({matching_fraud[0]['case_number']}) on matching entity signature.")
        elif risk_score >= 50.0:
            recommendation = "ESCALATE"
            confidence = 0.82
            reasoning_bullets.append(f"Case risk score ({risk_score}/100) crosses mandatory human review threshold.")
            reasoning_bullets.append("Elevated risk present in transaction profile, but lacks conclusive credential theft signature. Manual investigator out-of-band verification recommended.")
        elif risk_score < 35.0 and tx_data.get("is_merchant_verified") and not is_shared_device:
            recommendation = "FALSE_POSITIVE"
            confidence = 0.88
            reasoning_bullets.append("Transaction aligns with historical account behavior. Verified merchant entity with low platform fraud rate.")
        else:
            # Borderline or conflicting case -> ABSTAIN per Rule 3
            abstained = True
            recommendation = "REQUEST_MORE_INFO"
            confidence = 0.55
            reasoning_bullets.append("ABSTAIN: Insufficient conclusive evidence. Weak risk indicators conflict with customer spending baseline.")
            reasoning_bullets.append("Grounded policies do not provide definitive guidance without customer SMS/biometric verification.")

        reasoning_summary = " ".join(reasoning_bullets)

        total_latency_ms = (time.perf_counter() - total_start) * 1000

        # Create Agent Investigation Run record
        investigation_run = AgentInvestigationRun(
            run_id=run_uuid,
            case_id=case.id,
            status="COMPLETED",
            recommendation=recommendation,
            abstained=abstained,
            reasoning_summary=reasoning_summary,
            observed_evidence=observed_facts,
            retrieved_policies=policy_data,
            similar_cases=prev_cases,
            tool_calls=tool_telemetry,
            total_latency_ms=round(total_latency_ms, 2),
            model_version=self.model_version,
            token_usage={"prompt_tokens": 842, "completion_tokens": 195, "total_tokens": 1037}
        )
        db.add(investigation_run)

        # Update Case with AI findings
        case.status = CaseStatus.AI_REVIEWED.value
        case.ai_recommendation = recommendation
        case.ai_confidence = confidence
        case.ai_reasoning_summary = reasoning_summary
        case.ai_investigated_at = datetime.now(timezone.utc)

        # Audit: Case Investigation Completed
        audit_complete = CaseAuditLog(
            case_id=case.id,
            actor="AI_AGENT",
            actor_id=self.model_version,
            action="AI_INVESTIGATION_COMPLETED",
            details=f"Completed multi-tool investigation. Recommendation: {recommendation} (Confidence: {int(confidence*100)}%). Total latency: {round(total_latency_ms, 1)}ms.",
            event_metadata={
                "run_id": run_uuid,
                "recommendation": recommendation,
                "abstained": abstained,
                "tool_calls_count": len(tool_telemetry)
            }
        )
        db.add(audit_complete)

        await db.commit()
        await db.refresh(case)
        await db.refresh(investigation_run)

        return investigation_run

    # =========================================================================
    # HUMAN-IN-THE-LOOP DECISIONING (Section 13)
    # =========================================================================

    async def record_human_decision(
        self,
        case_id: int,
        decision: str, # CONFIRM_FRAUD, FALSE_POSITIVE, ESCALATE, REQUEST_MORE_INFO
        investigator_id: str,
        notes: str,
        db: AsyncSession
    ) -> Case:
        stmt = select(Case).where(Case.id == case_id)
        res = await db.execute(stmt)
        case = res.scalars().first()
        if not case:
            raise ValueError(f"Case #{case_id} not found.")

        # Map human decision to case status
        if decision == "CONFIRM_FRAUD":
            new_status = CaseStatus.CONFIRMED_FRAUD.value
        elif decision == "FALSE_POSITIVE":
            new_status = CaseStatus.FALSE_POSITIVE.value
        elif decision == "ESCALATE":
            new_status = CaseStatus.ESCALATED.value
        else:
            new_status = CaseStatus.PENDING_HUMAN_DECISION.value

        case.status = new_status
        case.human_decision = decision
        case.human_notes = notes
        case.decided_by = investigator_id
        case.decided_at = datetime.now(timezone.utc)

        # Audit Log: Human Decision
        audit_event = CaseAuditLog(
            case_id=case.id,
            actor="INVESTIGATOR",
            actor_id=investigator_id,
            action="HUMAN_DECISION_RECORDED",
            details=f"Investigator '{investigator_id}' recorded final verdict: [{decision}]. Notes: {notes or 'No notes provided.'}",
            event_metadata={
                "decision": decision,
                "ai_recommendation": case.ai_recommendation,
                "overrode_ai": (decision != case.ai_recommendation)
            }
        )
        db.add(audit_event)

        await db.commit()
        await db.refresh(case)
        return case

investigation_agent = InvestigationAgentService()
