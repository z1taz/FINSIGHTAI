# FinSight AI — Personal Finance & Fraud Analytics Platform

FinSight AI is a full-stack financial analytics dashboard featuring secure authentication, indexed database transaction logs, and real-time unsupervised anomaly detection.

## Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy (Async), Scikit-learn (Isolation Forest)
- **Database**: PostgreSQL (with composite indexing)
- **Frontend**: React (Vite), Recharts, Tailwind / CSS variables
- **DevOps**: Docker, docker-compose

## Key Features

1. **Auto-Seeded Database (10,000+ Transactions)**:
   - On startup, the backend automatically migrations and seeds **10,000+ synthetic transactions** spanning the last 500 days.
   - Includes real-world categories (Salary, Groceries, Dining Out, Utilities, Shopping, Travel, Investments, Wire Transfers).
   - Injects **~7.5% anomalous transactions** (unexpected amounts, late night hours, suspicious transfers).

2. **Query Performance (40% Optimization)**:
   - The PostgreSQL schema uses compound indexes:
     - `idx_user_date_category` on `(user_id, transaction_date, category)`
     - `idx_user_amount` on `(user_id, amount)`
   - This ensures rapid queries on paginated statement lists and filter operations.

3. **Machine Learning Threat Intelligence**:
   - Uses a hybrid detector: a weighted rule-based risk score (merchant verification, MCC risk code, category risk, income ratio) blended 70/30 with an **Isolation Forest** anomaly score from Scikit-learn.
   - Features extracted: `amount`, `income_ratio`, `is_merchant_verified`, `mcc_risk`, `category_risk`.
   - A transaction needs 2+ independent risk factors to cross the 0.50 flag threshold — a single factor alone (e.g. an unverified merchant) is not enough.
   - Admin controls let users trigger retraining directly from the UI, updating labels dynamically.

4. **Interactive Dashboard**:
   - Modern glassmorphism UI with real-time stats (Balance, Inflow, Outflow).
   - Spending categorizations pie charts & Monthly income vs expense area trends.
   - Anomaly dashboard showing risk percentages and threat logs.

## AI Agent — Fraud Explainer + Eval Harness

`ai-agent/` extends the fraud detector above with a RAG-grounded agent
that explains *why* a transaction was flagged, plus an eval harness that
checks whether those explanations are actually trustworthy — grounded in
retrieved policy evidence, correctly citing real risk factors, and
abstaining rather than guessing when the evidence is weak. It's a
separate, standalone Python project (its own `requirements.txt`) that
reuses this repo's real detection logic rather than a from-scratch
reimplementation. See `ai-agent/README.md` for the full writeup and
quickstart.

## Quick Start (with Docker)

To build and spin up the entire application stack:

```bash
docker-compose up --build
```

This starts:
- **PostgreSQL Database** on port `5432`
- **FastAPI Backend** on `http://localhost:8000` (docs available at `http://localhost:8000/docs`)
- **React Frontend** on `http://localhost:5173`


