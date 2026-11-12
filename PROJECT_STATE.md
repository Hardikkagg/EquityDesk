# PROJECT STATE

## Project
Stock Portfolio Management System

## Project Vision

This project is being developed in two stages:

1. College DBMS mini-project
2. Later expansion into a real personal/resume-ready Portfolio Intelligence & Stock Analysis Platform

The long-term system may eventually integrate brokerage data such as Groww, portfolio analytics, market data, stock analysis, ML-based predictions, alerts, and other intelligent features.

The current college implementation remains simple, clean, and stable while being designed so it can be extended later.

---

# FINAL DEVELOPMENT ROADMAP

## Phase 1 — Database Foundation
STATUS: COMPLETE

Completed:

- MySQL database created (`stock_portfolio_management`)
- `INVESTOR` table created (20 records)
- `PORTFOLIO` table created (20 records)
- `SECURITY` table created (25 records)
- `PORTFOLIO_POSITION` table created (25 records)
- `TRADE` table created (25+ records)
- Primary keys, Foreign keys, and Check constraints implemented
- Sample project data inserted & DML operations verified

---

## Phase 2 — Basic Application & Portfolio Dashboard
STATUS: COMPLETE

Completed:

- Flask backend connected cleanly to MySQL `stock_portfolio_management`.
- REST API Endpoints built:
  - `GET /api/health`
  - `GET /api/test-db`
  - `GET /api/investors`
  - `GET /api/portfolios`
  - `GET /api/securities`
  - `GET /api/holdings` (supports multi-table SQL JOINs with `PORTFOLIO_POSITION`, `PORTFOLIO`, `INVESTOR`, and `SECURITY`, calculating Invested Value, Current Market Value, and P&L dynamically)
  - `GET /api/trades` (supports multi-table SQL JOINs with `TRADE`, `INVESTOR`, `PORTFOLIO`, and `SECURITY`)
- Modern, responsive Dark Theme Financial Dashboard:
  - Summary metric cards (Total Invested, Current Value, P&L with % return, Number of Holdings)
  - Investor/Portfolio demo filter dropdowns
  - Full Holdings Table with profit/loss color highlights
  - Recent Transactions ledger

---

## Phase 3 — Complete Core Workflow (BUY/SELL)
STATUS: COMPLETE

Completed:

- Interactive BUY/SELL form with dynamic stock price auto-population and estimated total calculator.
- ACID Transaction support via `POST /api/trade` using MySQL database transactions (`autocommit=False`, `commit()`, `rollback()` on error).
- BUY Workflow:
  - Validates investor, portfolio ownership, security, positive quantity, and positive price.
  - Inserts `TRADE` record.
  - Updates `PORTFOLIO_POSITION` or inserts a new position if not previously held.
  - Recalculates weighted average buy price: `(old_qty * old_avg + new_qty * new_price) / (old_qty + new_qty)`.
- SELL Workflow:
  - Verifies position existence and prevents over-selling (rejects transactions exceeding available quantity with HTTP 400).
  - Inserts `TRADE` record.
  - Decrements `PORTFOLIO_POSITION.quantity` while maintaining `average_buy_price`.
- Instant asynchronous UI refresh upon successful execution.

---

# DATABASE FOUNDATION — PRESERVED & LOCKED

The core schema remains unmodified:

INVESTOR
- investor_id PK
- investor_name
- email
- phone
- date_joined

PORTFOLIO
- portfolio_id PK
- investor_id FK
- portfolio_name
- created_date

SECURITY
- security_id PK
- symbol
- security_name
- sector
- current_price

PORTFOLIO_POSITION
- position_id PK
- portfolio_id FK
- security_id FK
- quantity
- average_buy_price

TRADE
- trade_id PK
- investor_id FK
- security_id FK
- portfolio_id FK
- trade_type
- quantity
- trade_price
- trade_date

---

# KNOWN LIMITATIONS (College Demo Scope)

1. Single-user session demo selector (no user login/auth token system, as per college project specifications).
2. Prices are derived from the existing `SECURITY` table rather than live market ticker WebSocket streams.
3. Quantities are whole integer shares (fractional shares not supported in original schema).
4. No external third-party frontend frameworks (pure Vanilla JS and CSS used).

---

# LONG-TERM VISION (Future Expansion)

Portfolio Intelligence & Stock Analysis Platform:
- Multi-user accounts & JWT Authentication
- Live Brokerage API integration (e.g., Groww API)
- Historical price charting & Candlesticks
- XIRR, Sharpe Ratio, Risk analytics & Sector distribution charts
- ML-based price and volatility indicators
