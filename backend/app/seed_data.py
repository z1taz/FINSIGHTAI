import asyncio
import random
from datetime import datetime, timedelta, timezone
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import delete, func
from app.config import settings
from app.database import Base, SessionLocal
from app.models.user import User
from app.models.transaction import Transaction
from app.models.case import Case, CaseAuditLog, AgentInvestigationRun, CaseStatus, RiskLevel
from app.services.auth_service import get_password_hash
from app.services.fraud_detector import fraud_detector, MODEL_PATH

# Seed data categories, merchants & MCC codes
MERCHANT_PROFILES = {
    "Groceries": [
        ("Walmart", "5411", True), ("Safeway", "5411", True), ("Kroger", "5411", True),
        ("Whole Foods", "5411", True), ("Trader Joe's", "5411", True)
    ],
    "Dining Out": [
        ("McDonalds", "5814", True), ("Starbucks", "5814", True), ("Subway", "5814", True),
        ("Chipotle", "5814", True), ("Olive Garden", "5814", True)
    ],
    "Utilities": [
        ("Electric Corp", "4899", True), ("Water District", "4899", True),
        ("Comcast Cable", "4899", True), ("AT&T Mobile", "4899", True)
    ],
    "Rent/Mortgage": [
        ("Property Management LLC", "6513", True), ("Home Loans Direct", "6513", True)
    ],
    "Entertainment": [
        ("Netflix", "7832", True), ("Spotify", "7832", True), ("AMC Theatres", "7832", True),
        ("Steam Games", "7832", True)
    ],
    "Shopping": [
        ("Amazon", "5311", True), ("Target", "5311", True), ("Best Buy", "5311", True),
        ("Nike Store", "5311", True), ("Global Luxury Outlet", "5999", False)
    ],
    "Travel": [
        ("Delta Airlines", "4121", True), ("Uber", "4121", True), ("Airbnb", "4121", True),
        ("Shell Gas", "5999", True), ("Express Flight Bookers", "5999", False)
    ],
    "Wire Transfer": [
        ("Western Union", "6012", True), ("FastRemit Global", "6012", False),
        ("Offshore Settlement Dept", "0000", False)
    ],
    "Investment": [
        ("Vanguard Group", "6012", True), ("Fidelity Investments", "6012", True),
        ("CryptoFast Exchange", "6051", False)
    ],
    "Gambling": [
        ("Vegas Bet Portal", "7995", False), ("Royal Jackpot Casino", "7995", False)
    ]
}

DEVICES = [
    "DEV-APPLE-9921",
    "DEV-ANDROID-4102",
    "DEV-WORKSTATION-01",
    "DEV-TOR-PROXY-77",
    "DEV-SAMSUNG-1092"
]

LOCATIONS = [
    "San Francisco, CA, US",
    "San Jose, CA, US",
    "New York, NY, US",
    "Seattle, WA, US",
    "Bucharest, RO [High-risk Proxy]",
    "Lagos, NG [Unrecognized Locale]"
]

async def seed_all(db: AsyncSession):
    print("Verifying FinSight AI synthetic risk operations dataset...")

    # 1. Create or verify primary demo user
    email = "demo@finsight.ai"
    result = await db.execute(select(User).filter(User.email == email))
    demo_user = result.scalars().first()

    if not demo_user:
        print("Creating demo investigator user (demo@finsight.ai)...")
        demo_user = User(
            email=email,
            full_name="Alex Mercer (Lead Risk Operator)",
            hashed_password=get_password_hash("password123"),
            monthly_income=450000.0,
            is_admin=True
        )
        db.add(demo_user)
        await db.commit()
        await db.refresh(demo_user)
    else:
        demo_user.is_admin = True
        demo_user.monthly_income = 450000.0
        await db.commit()

    # Check existing case count
    case_count_res = await db.execute(select(func.count(Case.id)))
    existing_cases = case_count_res.scalar() or 0
    if existing_cases >= 15:
        print(f"Synthetic dataset already initialized with {existing_cases} cases. Ready.")
        return

    print("Generating comprehensive synthetic transactions & case investigations...")
    
    # Generate 500 baseline normal transactions over 90 days
    base_date = datetime.now(timezone.utc) - timedelta(days=90)
    tx_list = []
    
    for day in range(90):
        current_day = base_date + timedelta(days=day)
        # 3-7 normal transactions daily
        for _ in range(random.randint(3, 7)):
            cat = random.choice(["Groceries", "Dining Out", "Utilities", "Entertainment", "Shopping", "Travel"])
            merch_name, mcc, is_ver = random.choice(MERCHANT_PROFILES[cat])
            
            amount = round(random.uniform(15.0, 180.0), 2)
            if cat == "Travel": amount = round(random.uniform(40.0, 350.0), 2)
            if cat == "Groceries": amount = round(random.uniform(25.0, 120.0), 2)
            
            tx_time = current_day.replace(hour=random.randint(8, 22), minute=random.randint(0, 59))
            tx_list.append({
                "user_id": demo_user.id,
                "amount": amount,
                "category": cat,
                "merchant": merch_name,
                "description": f"Standard {cat} spend at {merch_name}",
                "mcc_code": mcc,
                "is_merchant_verified": is_ver,
                "transaction_date": tx_time,
                "device_id": "DEV-APPLE-9921",
                "ip_address": "198.51.100.12",
                "location": "San Francisco, CA, US",
                "card_last4": "4821",
                "is_new_device": False,
                "is_velocity_burst": False
            })

    # Train Isolation Forest on normal baseline
    model_train_data = [
        {"amount": t["amount"], "category": t["category"], "mcc_code": t["mcc_code"], 
         "is_merchant_verified": t["is_merchant_verified"], "transaction_date": t["transaction_date"]}
        for t in tx_list
    ]
    fraud_detector.train(model_train_data, monthly_income_baseline=demo_user.monthly_income)
    print("Baseline model trained on normal spending distribution.")

    # Injected Intentionally Structured Fraud Patterns (Section 24)
    # Pattern 1: High-Value Wire to Unverified Entity from Novel Device
    anomaly_patterns = [
        {
            "amount": 9200.0,
            "category": "Wire Transfer",
            "merchant": "Offshore Settlement Dept",
            "description": "International urgent wire remittance",
            "mcc_code": "0000",
            "is_merchant_verified": False,
            "device_id": "DEV-TOR-PROXY-77",
            "ip_address": "185.220.101.5",
            "location": "Bucharest, RO [High-risk Proxy]",
            "is_new_device": True,
            "is_velocity_burst": False,
            "pre_status": CaseStatus.PENDING_HUMAN_DECISION.value,
            "notes": "Convergence of unassigned MCC 0000, unverified entity, and TOR exit node."
        },
        {
            "amount": 4850.0,
            "category": "Investment",
            "merchant": "CryptoFast Exchange",
            "description": "Digital asset purchase instant credit",
            "mcc_code": "6051",
            "is_merchant_verified": False,
            "device_id": "DEV-ANDROID-4102",
            "ip_address": "198.51.100.89",
            "location": "San Jose, CA, US",
            "is_new_device": True,
            "is_velocity_burst": False,
            "pre_status": CaseStatus.AI_REVIEWED.value,
            "notes": "Crypto liquidation vector on unrecognized mobile device."
        },
        {
            "amount": 3500.0,
            "category": "Gambling",
            "merchant": "Vegas Bet Portal",
            "description": "Online sports wager reload",
            "mcc_code": "7995",
            "is_merchant_verified": False,
            "device_id": "DEV-TOR-PROXY-77",
            "ip_address": "185.220.101.5",
            "location": "Bucharest, RO [High-risk Proxy]",
            "is_new_device": True,
            "is_velocity_burst": True,
            "pre_status": CaseStatus.CONFIRMED_FRAUD.value,
            "notes": "Historical precedent: Confirmed account takeover with wagering balance drain."
        },
        {
            "amount": 6500.0,
            "category": "Shopping",
            "merchant": "Global Luxury Outlet",
            "description": "High ticket jewelry purchase",
            "mcc_code": "5999",
            "is_merchant_verified": False,
            "device_id": "DEV-SAMSUNG-1092",
            "ip_address": "198.51.100.99",
            "location": "Lagos, NG [Unrecognized Locale]",
            "is_new_device": True,
            "is_velocity_burst": True,
            "pre_status": CaseStatus.NEW.value,
            "notes": "Rapid spending burst at unverified retail outlet."
        },
        {
            "amount": 2100.0,
            "category": "Travel",
            "merchant": "Delta Airlines",
            "description": "Family vacation airfare booking",
            "mcc_code": "4121",
            "is_merchant_verified": True,
            "device_id": "DEV-APPLE-9921",
            "ip_address": "198.51.100.12",
            "location": "San Francisco, CA, US",
            "is_new_device": False,
            "is_velocity_burst": False,
            "pre_status": CaseStatus.FALSE_POSITIVE.value,
            "notes": "Legitimate verified merchant airline purchase during holiday period."
        },
        {
            "amount": 4200.0,
            "category": "Wire Transfer",
            "merchant": "FastRemit Global",
            "description": "Emergency remittance transfer",
            "mcc_code": "6012",
            "is_merchant_verified": False,
            "device_id": "DEV-ANDROID-4102",
            "ip_address": "198.51.100.89",
            "location": "San Jose, CA, US",
            "is_new_device": True,
            "is_velocity_burst": False,
            "pre_status": CaseStatus.ESCALATED.value,
            "notes": "Tier 2 investigation required: Customer outbound contact pending."
        },
        {
            "amount": 1500.0,
            "category": "Shopping",
            "merchant": "Apple",
            "description": "Hardware replacement purchase",
            "mcc_code": "5311",
            "is_merchant_verified": True,
            "device_id": "DEV-APPLE-9921",
            "ip_address": "198.51.100.12",
            "location": "San Francisco, CA, US",
            "is_new_device": False,
            "is_velocity_burst": False,
            "pre_status": CaseStatus.FALSE_POSITIVE.value,
            "notes": "Verified merchant entity with zero suspicious linkage."
        },
        {
            "amount": 7800.0,
            "category": "Wire Transfer",
            "merchant": "Offshore Settlement Dept",
            "description": "Commercial invoice payment",
            "mcc_code": "0000",
            "is_merchant_verified": False,
            "device_id": "DEV-TOR-PROXY-77",
            "ip_address": "185.220.101.5",
            "location": "Bucharest, RO [High-risk Proxy]",
            "is_new_device": True,
            "is_velocity_burst": True,
            "pre_status": CaseStatus.CONFIRMED_FRAUD.value,
            "notes": "Cluster collision: shared TOR IP across multiple fraudulent wire attempts."
        }
    ]

    # Insert baseline transactions
    db_items = []
    for t in tx_list:
        db_items.append(
            Transaction(
                user_id=t["user_id"],
                amount=t["amount"],
                category=t["category"],
                merchant=t["merchant"],
                description=t["description"],
                mcc_code=t["mcc_code"],
                is_merchant_verified=t["is_merchant_verified"],
                transaction_date=t["transaction_date"],
                device_id=t["device_id"],
                ip_address=t["ip_address"],
                location=t["location"],
                card_last4=t["card_last4"],
                is_fraudulent=0,
                fraud_score=random.uniform(2.0, 18.0)
            )
        )
    db.add_all(db_items)
    await db.commit()

    # Insert anomaly transactions and corresponding Cases
    now = datetime.now(timezone.utc)
    for idx, p in enumerate(anomaly_patterns):
        tx_time = now - timedelta(hours=random.randint(1, 72))
        calc = fraud_detector.calculate_structured_risk(p, monthly_income_baseline=demo_user.monthly_income)
        
        tx = Transaction(
            user_id=demo_user.id,
            amount=p["amount"],
            category=p["category"],
            merchant=p["merchant"],
            description=p["description"],
            mcc_code=p["mcc_code"],
            is_merchant_verified=p["is_merchant_verified"],
            transaction_date=tx_time,
            device_id=p["device_id"],
            ip_address=p["ip_address"],
            location=p["location"],
            card_last4="4821",
            is_fraudulent=1,
            fraud_score=calc["score"]
        )
        db.add(tx)
        await db.commit()
        await db.refresh(tx)

        case_num = f"CASE-{1000 + tx.id}"
        case = Case(
            case_number=case_num,
            transaction_id=tx.id,
            user_id=demo_user.id,
            status=p["pre_status"],
            risk_score=calc["score"],
            risk_level=calc["risk_level"],
            risk_factors=calc["risk_factors"],
            ai_recommendation="CONFIRM_FRAUD" if calc["score"] >= 75.0 else ("ESCALATE" if calc["score"] >= 50.0 else "FALSE_POSITIVE"),
            ai_confidence=0.91 if calc["score"] >= 75.0 else 0.82,
            ai_reasoning_summary=f"Automated risk synthesis: {len(calc['risk_factors'])} risk factors observed. {p['notes']}",
            ai_investigated_at=tx_time + timedelta(minutes=2),
            human_decision=p["pre_status"] if p["pre_status"] in [CaseStatus.CONFIRMED_FRAUD.value, CaseStatus.FALSE_POSITIVE.value] else None,
            human_notes=p["notes"] if p["pre_status"] in [CaseStatus.CONFIRMED_FRAUD.value, CaseStatus.FALSE_POSITIVE.value] else None,
            decided_by="senior_investigator@bank.internal" if p["pre_status"] in [CaseStatus.CONFIRMED_FRAUD.value, CaseStatus.FALSE_POSITIVE.value] else None,
            decided_at=tx_time + timedelta(minutes=15) if p["pre_status"] in [CaseStatus.CONFIRMED_FRAUD.value, CaseStatus.FALSE_POSITIVE.value] else None
        )
        db.add(case)
        await db.commit()
        await db.refresh(case)

        # Audit timeline creation
        log_create = CaseAuditLog(
            case_id=case.id,
            actor="RISK_ENGINE",
            actor_id="FinSight-RulesEngine-v2",
            action="CASE_CREATED",
            details=f"Alert triggered with composite risk score of {calc['score']}/100 ({calc['risk_level']}). Case {case_num} opened.",
            event_metadata={"risk_factors": calc["risk_factors"]},
            timestamp=tx_time
        )
        db.add(log_create)

        log_ai = CaseAuditLog(
            case_id=case.id,
            actor="AI_AGENT",
            actor_id="FinSight-InvestigationAgent-v2.1",
            action="AI_INVESTIGATION_COMPLETED",
            details=f"Agent completed multi-tool evaluation. Recommendation: {case.ai_recommendation}. Latency: 142ms.",
            event_metadata={"recommendation": case.ai_recommendation},
            timestamp=tx_time + timedelta(minutes=2)
        )
        db.add(log_ai)

        if case.human_decision:
            log_human = CaseAuditLog(
                case_id=case.id,
                actor="INVESTIGATOR",
                actor_id=case.decided_by,
                action="HUMAN_DECISION_RECORDED",
                details=f"Final human adjudication: [{case.human_decision}]. Notes: {case.human_notes}",
                event_metadata={"decision": case.human_decision},
                timestamp=case.decided_at
            )
            db.add(log_human)

        await db.commit()

    print("FinSight AI synthetic risk operations dataset seeded successfully!")

if __name__ == "__main__":
    from app.database import engine
    async def main():
        async with SessionLocal() as db:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            await seed_all(db)
    asyncio.run(main())
