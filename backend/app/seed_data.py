import asyncio
import random
from datetime import datetime, timedelta, timezone
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import settings
from app.database import Base, SessionLocal
from app.models.user import User
from app.models.transaction import Transaction
from app.services.auth_service import get_password_hash
from app.services.fraud_detector import fraud_detector, MODEL_PATH

# Seed data categories & merchants
CATEGORIES = {
    "Groceries": ["Walmart", "Safeway", "Kroger", "Whole Foods", "Trader Joe's"],
    "Dining Out": ["McDonalds", "Starbucks", "Subway", "Chipotle", "Olive Garden", "Local Diner"],
    "Utilities": ["Electric Corp", "Water District", "Comcast Cable", "AT&T Mobile", "Clean Garbage"],
    "Rent/Mortgage": ["Property Management", "Home Loans LLC"],
    "Entertainment": ["Netflix", "Spotify", "AMC Theatres", "Steam Games", "Ticketmaster"],
    "Shopping": ["Amazon", "Target", "Best Buy", "Macy's", "Nike Store"],
    "Travel": ["Delta Airlines", "Uber", "Airbnb", "Shell Gas", "Hilton Hotels"],
    "Wire Transfer": ["Western Union", "Wire Transfer Dept"],
    "Investment": ["Vanguard Group", "Fidelity Investments", "Robinhood"],
    "Salary": ["Tech Corp Payroll"]
}

async def generate_transactions(user_id: int):
    print("Generating 10,000+ synthetic transactions...")
    txs = []
    
    # Run dates over the last 500 days
    start_date = datetime.now(timezone.utc) - timedelta(days=500)
    current_time = start_date
    
    # Keep track of months for salary & rent
    months_seen = set()
    
    # 10,000 transactions over 500 days is ~20 transactions per day
    while current_time < datetime.now(timezone.utc):
        month_str = current_time.strftime("%Y-%m")
        
        # 1. Monthly Salary (Income)
        if month_str not in months_seen and current_time.day == 1:
            txs.append({
                "amount": 5500.0,
                "category": "Salary",
                "merchant": "Tech Corp Payroll",
                "description": "Monthly Net Salary Credit",
                "transaction_date": current_time.replace(hour=9, minute=0, second=0)
            })
            
            # 2. Monthly Rent (Expense)
            txs.append({
                "amount": 1600.0,
                "category": "Rent/Mortgage",
                "merchant": "Property Management",
                "description": "Monthly Apartment Rent Payment",
                "transaction_date": current_time.replace(hour=10, minute=30, second=0)
            })
            months_seen.add(month_str)
            
        # Daily transaction loop (generate random daily transactions: 15 to 25 per day)
        daily_count = random.randint(15, 25)
        for _ in range(daily_count):
            # Select random category and merchant
            cat = random.choice([c for c in CATEGORIES.keys() if c not in ["Salary", "Rent/Mortgage"]])
            merchant = random.choice(CATEGORIES[cat])
            
            # Generate random time of day (normally during daytime 7 AM to 11 PM)
            hour = random.randint(7, 23)
            minute = random.randint(0, 59)
            tx_time = current_time.replace(hour=hour, minute=minute)
            
            # Base amounts based on category
            if cat == "Groceries":
                amount = round(random.uniform(30.0, 150.0), 2)
            elif cat == "Dining Out":
                amount = round(random.uniform(5.0, 60.0), 2)
            elif cat == "Utilities":
                # Utilities happen once a month per merchant, simulate randomly
                if random.random() < 0.1:
                    amount = round(random.uniform(40.0, 120.0), 2)
                else:
                    continue
            elif cat == "Entertainment":
                amount = round(random.uniform(9.0, 50.0), 2)
            elif cat == "Shopping":
                amount = round(random.uniform(15.0, 250.0), 2)
            elif cat == "Travel":
                amount = round(random.uniform(10.0, 400.0), 2)
            elif cat == "Wire Transfer":
                # Rare
                if random.random() < 0.02:
                    amount = round(random.uniform(100.0, 800.0), 2)
                else:
                    continue
            elif cat == "Investment":
                if random.random() < 0.05:
                    amount = round(random.uniform(100.0, 500.0), 2)
                else:
                    continue
            else:
                amount = round(random.uniform(5.0, 100.0), 2)
                
            txs.append({
                "amount": amount,
                "category": cat,
                "merchant": merchant,
                "description": f"Purchase at {merchant}",
                "transaction_date": tx_time
            })
            
        current_time += timedelta(days=1)

    # 3. Add explicit anomalies (fraudulent transactions) - about 7.5% of total
    print(f"Base transactions generated: {len(txs)}")
    total_tx_count = len(txs)
    anomaly_count = int(total_tx_count * 0.075)
    print(f"Injecting {anomaly_count} anomalous transactions (approx 7.5%)...")
    
    # We will randomly distribute anomalies
    for _ in range(anomaly_count):
        # Choose a random index
        idx = random.randint(0, len(txs) - 1)
        base_date = txs[idx]["transaction_date"]
        
        # Anomaly types:
        anomaly_type = random.choice(["high_amount", "odd_hour", "risky_wire", "high_risk_shopping"])
        
        if anomaly_type == "high_amount":
            # Extremely high amount for category
            cat = random.choice(["Shopping", "Dining Out", "Entertainment"])
            merchant = random.choice(CATEGORIES[cat])
            amount = round(random.uniform(2500.0, 8500.0), 2)
            hour = random.randint(9, 21)
            desc = "Suspicious High-Value Purchase"
            
        elif anomaly_type == "odd_hour":
            # High amount at 3-5 AM
            cat = random.choice(["Shopping", "Travel", "Wire Transfer"])
            merchant = random.choice(CATEGORIES[cat])
            amount = round(random.uniform(800.0, 3000.0), 2)
            hour = random.randint(2, 4)
            desc = "Off-hours Electronic Settlement"
            
        elif anomaly_type == "risky_wire":
            # Out-of-profile wire transfer
            cat = "Wire Transfer"
            merchant = "Western Union"
            amount = round(random.uniform(4000.0, 9500.0), 2)
            hour = random.randint(10, 16)
            desc = "International Fund Remittance"
            
        else: # high_risk_shopping
            # Fast consecutive transactions or high value categories
            cat = "Travel"
            merchant = "Unknown Agent Services"
            amount = round(random.uniform(3500.0, 7500.0), 2)
            hour = random.randint(1, 5)
            desc = "Urgent Travel Booking Agency"
            
        txs.append({
            "amount": amount,
            "category": cat,
            "merchant": merchant,
            "description": desc,
            "transaction_date": base_date.replace(hour=hour, minute=random.randint(0,59))
        })
        
    return txs

async def seed_all(db: AsyncSession):
    # 1. Create demo user if not exists
    email = "demo@finsight.ai"
    result = await db.execute(select(User).filter(User.email == email))
    demo_user = result.scalars().first()
    
    if demo_user:
        demo_user.is_admin = True
        demo_user.monthly_income = 5000.0
        await db.commit()
        print("Demo user already exists. Checking transaction counts...")
        tx_count_result = await db.execute(select(Transaction).where(Transaction.user_id == demo_user.id))
        count = len(tx_count_result.scalars().all())
        if count >= 10000:
            print(f"Demo database already seeded with {count} transactions.")
            return
        else:
            print(f"Clearing old transactions ({count}) and re-seeding...")
            # Clear old transactions
            await db.execute(select(Transaction).where(Transaction.user_id == demo_user.id))
            # Delete statement
            from sqlalchemy import delete
            await db.execute(delete(Transaction).where(Transaction.user_id == demo_user.id))
            await db.commit()
    else:
        print("Creating demo user...")
        demo_user = User(
            email=email,
            full_name="Demo User (Admin)",
            hashed_password=get_password_hash("password123"),
            monthly_income=5000.0,
            is_admin=True
        )
        db.add(demo_user)
        await db.commit()
        await db.refresh(demo_user)
        
    # 2. Generate transactions list
    raw_txs = await generate_transactions(demo_user.id)
    
    # 3. Train Isolation Forest model on raw transactions
    print("Training Isolation Forest ML model on generated seed dataset...")
    # Map raw transactions to dict matching model input
    model_inputs = []
    for tx in raw_txs:
        model_inputs.append({
            "amount": tx["amount"],
            "category": tx["category"],
            "merchant": tx["merchant"],
            "transaction_date": tx["transaction_date"]
        })
        
    fraud_detector.train(model_inputs)
    print("Isolation Forest trained and saved to pickle.")
    
    # 4. Predict fraud scores & labels
    print("Scoring and labeling transactions...")
    predictions = fraud_detector.predict(model_inputs)
    
    # 5. Insert into DB in chunks
    print("Saving 10,000+ transactions to database...")
    batch_size = 1000
    for i in range(0, len(raw_txs), batch_size):
        chunk = raw_txs[i:i+batch_size]
        chunk_preds = predictions[i:i+batch_size]
        
        db_items = []
        for tx, (is_fraud, score) in zip(chunk, chunk_preds):
            db_items.append(
                Transaction(
                    user_id=demo_user.id,
                    amount=tx["amount"],
                    category=tx["category"],
                    merchant=tx["merchant"],
                    description=tx["description"],
                    transaction_date=tx["transaction_date"],
                    is_fraudulent=is_fraud,
                    fraud_score=score
                )
            )
        db.add_all(db_items)
        await db.commit()
        print(f"Saved {min(i + batch_size, len(raw_txs))} / {len(raw_txs)}...")
        
    print("Database seeding completed successfully!")

if __name__ == "__main__":
    from app.database import engine
    
    async def main():
        async with SessionLocal() as db:
            # Create tables
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            await seed_all(db)
            
    asyncio.run(main())
