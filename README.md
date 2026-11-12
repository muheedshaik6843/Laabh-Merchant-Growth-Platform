# Laabh-Merchant-Growth-Platform

## Laabh — Merchant Growth Platform

A hackathon demo for profit-first growth decisions. The app includes three simulated merchants (kirana, café, pharmacy), seeded transaction history, dashboard analytics, recommendations, customer segments, inventory alerts, campaign simulation, holdout analytics, forecasts, a typed multilingual assistant, and a deterministic Profit Guard.

## Run locally

1. Create and activate a Python virtual environment.
2. Install `backend/requirements.txt`.
3. Copy `.env.example` to `.env` and optionally set `DATABASE_URL` / `SECRET_KEY`.
4. Run `python backend/app.py` from this directory.
5. Open http://127.0.0.1:5000. Demo login: `demo@laabh.in` / `laabh123`.

The default database is persistent SQLite (`backend/laabh.db`); set `DATABASE_URL` to a SQLAlchemy MySQL URL for a MySQL deployment. All included merchant, customer, sales, and campaign data are simulated and are not Paytm data. Campaign delivery is simulated and does not contact customers.

## Financial logic

Profit Guard calculates discounted unit profit, baseline purchases that would happen without an offer, incremental sales, cannibalization, campaign cost, break-even sales, and final incremental profit. An offer is approved only when projected incremental profit is strictly positive. Calculations are deterministic and happen server-side.

## Structure

- `backend/app.py` — API, SQLite persistence, authentication, seed data, analytics and profit engine
- `frontend/` — responsive dashboard and application UI
- `.env.example`, `backend/requirements.txt`

## Production notes

The demo supports password hashing, session authentication, merchant-scoped APIs, validation, and environment configuration. For production, use HTTPS, secure session settings, managed MySQL, migrations, rate limiting, and a configured messaging provider with explicit merchant authorization. LLM and speech services are intentionally not required for this functioning offline demo.
