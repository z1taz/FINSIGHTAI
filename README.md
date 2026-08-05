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
   - Uses an **Isolation Forest** model from Scikit-learn to calculate transaction anomaly probability.
   - Features extracted: `amount`, `hour_of_day`, `day_of_week`, `category_risk_index`.
   - Admin controls let users trigger retraining directly from the UI, updating labels dynamically.

4. **Interactive Dashboard**:
   - Modern glassmorphism UI with real-time stats (Balance, Inflow, Outflow).
   - Spending categorizations pie charts & Monthly income vs expense area trends.
   - Anomaly dashboard showing risk percentages and threat logs.

## Quick Start (with Docker)

To build and spin up the entire application stack:

```bash
docker-compose up --build
```

This starts:
- **PostgreSQL Database** on port `5432`
- **FastAPI Backend** on `http://localhost:8000` (docs available at `http://localhost:8000/docs`)
- **React Frontend** on `http://localhost:5173`


