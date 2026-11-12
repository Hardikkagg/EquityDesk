# EquityDesk

EquityDesk is a responsive stock-market overview and investment-management application built on the existing Flask, MySQL, HTML, CSS, and vanilla JavaScript project.

## What it does

- **Market Discover:** default landing page with deterministic, clearly labeled synthetic demo fixtures for index, movers, volume, sector, ETF, US-market, and fictional news sections. Demo fixtures are presentation-only; the separate security catalogue uses stored prices only.
- **Investor context:** select an investor in the header before viewing investment pages. Portfolio, holdings, transaction, analytics, watchlist, portfolio-detail, and security-detail activity is scoped to the selected investor. This selector is not authentication or account-level security.
- **Portfolio overview:** after selecting an investor, see only their database-backed portfolio value, open invested amount, FIFO realized P&L, unrealized P&L, returns, and open-position counts. Empty portfolios offer a direct first-trade action; cards open their detail page.
- **Portfolios and holdings:** create, rename, safely delete, compare, search, sort, and inspect portfolios and positions. Holdings can be grouped by security across portfolios with a quantity-weighted cost basis. Portfolios with recorded transactions cannot be deleted.
- **Securities and screener:** filter and sort by symbol, company, sector, and stored price; view available company/security information; save securities and optional target-price alerts in the selected investor's MySQL watchlist.
- **Security details:** inspect stored security details, the portfolios holding a security, consolidated quantities, and related transactions. Historical closing-price charts use only genuine CSV-imported `PRICE_HISTORY` records.
- **Portfolio details:** inspect FIFO realized P&L, open-position unrealized P&L, active transaction cash flows, holdings, sector allocation, portfolio XIRR, and a historical valuation chart when comparable imported prices exist. Current positions come from `PORTFOLIO_POSITION`; FIFO cost basis is used when the active trade ledger quantity reconciles, otherwise the stored position average is used.
- **Transactions:** validated BUY/SELL entry with inline quantity/price/oversell errors, portfolio/security/investor/type/date/status filtering, and transaction CSV export. Voided records remain visible with their mandatory reason, actor, and timestamp.
- **Analytics and risk:** selected-investor invested-versus-current value, allocation, holdings returns, BUY/SELL volume, monthly transaction activity, and rule-based concentration indicators. Cross-investor comparisons are not shown.
- **Exports:** CSV for filtered transaction history and investor-specific holdings.

### Data-source limits

Security current values are read from `SECURITY.current_price` and are **database prices, not live quotes**. Market Discover's sample indices, price movements, trading volumes, sectors, ETFs, international listings, and headlines are fictional demonstration fixtures in the frontend and are labeled synthetic/demo. They are never sent to or used by the backend, database, investor holdings, transaction accounting, valuations, or analytics. Do not treat demo values as market data or investment information. The project has no external live market-data or news feed. Historical charts are empty until the PRICE_HISTORY migration is applied and genuine daily closes are imported.

### Historical-price migration and CSV import

The migration `database/07_price_history.sql` creates only the `PRICE_HISTORY` table, with a foreign key to `SECURITY`, a unique `(security_id, price_date)` key, and a date index. It does not update `SECURITY.current_price`, replay trades, or modify existing records. The migration is **not applied** to the configured database; historical charts and CSV imports require it. Apply it manually only when desired (re-running is safe):

```powershell
mysql -h localhost -P 3306 -u root -p stock_portfolio_management < database\07_price_history.sql
```

Use the database user configured for your environment. The migration is not automatically applied. The CSV import endpoint requires a CSV with the exact identifying fields below; `security_id` must exist in `SECURITY`, dates must use `YYYY-MM-DD`, and closing prices must be positive:

```csv
security_id,price_date,close_price
12,2025-01-02,123.45
12,2025-01-03,124.10
```

Import via `POST /api/price-history/import` as multipart form data with the file field named `file`. Duplicate `(security_id, price_date)` rows are skipped and never replace an existing close. Imports do not modify current stored prices. Only import historical market data obtained from a genuine source; EquityDesk does not provide or fabricate a price feed.

Portfolio XIRR uses non-voided BUY cash flows as negative, non-voided SELL flows as positive, and the remaining holdings' current value as a positive terminal flow on the valuation date. The terminal valuation uses `SECURITY.current_price` (database price, not live). XIRR is omitted when cash flows are insufficient or a unique valid rate cannot be found.

Risk indicators describe current concentration only; they are not investment advice or predictions.

## Database and migration

The existing database remains `stock_portfolio_management`. The five existing core tables and their records are preserved:

`INVESTOR`, `PORTFOLIO`, `SECURITY`, `PORTFOLIO_POSITION`, and `TRADE`.

The watchlist is stored in one new table, `WATCHLIST`, keyed by investor and security, with an optional target price and foreign keys to the existing investor/security tables. No existing table is altered.

The migration `database/05_add_watchlist.sql` has been applied to the configured MySQL database during this update. It uses `CREATE TABLE IF NOT EXISTS`, so it is safe to run again:

```cmd
mysql -u root -p stock_portfolio_management < database\05_add_watchlist.sql
```

Replace `root` with the MySQL user configured for your environment. If the `mysql` client is not available in PATH, execute the migration file in your MySQL client.

## Configure and run

Requirements: Python 3.9+, MySQL, and the dependencies in `backend/requirements.txt`.

1. From the project root, create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install backend requirements:

   ```powershell
   python -m pip install -r backend\requirements.txt
   ```

3. Configure the root `.env` file with your local database connection. Keep credentials private:

   ```text
   MYSQL_HOST=localhost
   MYSQL_PORT=3306
   MYSQL_USER=root
   MYSQL_PASSWORD=your-local-password
   MYSQL_DB=stock_portfolio_management
   ```

4. Start Flask from the project root and open `http://127.0.0.1:5000`:

   ```powershell
   python backend\app.py
   ```

Do not rerun the original table-creation scripts against an already initialized database.

## API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health`, `/api/test-db` | Flask/MySQL health |
| GET | `/api/market` | Public security catalogue and explicit unavailable market-data flags |
| GET | `/api/investors` | Investor selector-safe names and IDs |
| GET, POST | `/api/portfolios?investor_id=<id>` | List the selected investor's portfolios or create a portfolio |
| GET, PUT, DELETE | `/api/portfolios/<id>?investor_id=<id>` | Investor-scoped portfolio detail; mutations require investor_id in the JSON body |
| GET | `/api/securities`, `/api/securities/<id>?period=1W\|1M\|1Y\|ALL&investor_id=<id>` | Security catalogue/details; investor activity is omitted unless scoped |
| POST | `/api/price-history/import` | Validate and import a CSV of genuine historical closing prices |
| GET | `/api/holdings?investor_id=<id>` | Required investor-scoped holdings, filters, and calculated summary |
| GET | `/api/trades?investor_id=<id>` | Required investor/portfolio/security/type/date-filtered trade history |
| POST | `/api/trade` | Validated transactional BUY or SELL |
| POST | `/api/trades/<id>/void` | Void a trade within the supplied investor context; preserves audit history |
| GET, POST, PUT, DELETE | `/api/watchlist` | Persistent investor-specific watchlist and target prices |
| GET | `/api/analytics?investor_id=<id>` | Required investor-scoped allocation, performance, activity, and concentration data |

Database writes use parameterized SQL and transaction commit/rollback. App-created IDs remain safe on schemas with manually assigned IDs; the configured database's AUTO_INCREMENT columns are compatible with the existing explicit-ID inserts.

## Testing

Run the complete test suite:

```powershell
python -m unittest discover -s tests -v
```

The Phase 2 accounting and Phase 3 historical/XIRR integration tests create unique temporary MySQL databases using the configured connection credentials, exercise the APIs there, and drop only those test databases when complete. The configured MySQL account needs permission to create and drop databases for these tests. The API smoke tests use Flask's local test client and do not require a running server or write to the configured database.

For route-only validation, run `python -m unittest discover -s tests -p "test_routes.py" -v`.

## External integrations not connected

- Live or delayed market data, index values, open/previous-close prices, and historical price charts.
- Verified IPO calendar and market-news feed.
- Excel/XLSX export (CSV export is available).

No new Python package dependencies were added.
