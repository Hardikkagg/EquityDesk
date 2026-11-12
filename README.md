# EquityDesk – Stock Portfolio Management System

**EquityDesk** is a database-driven stock portfolio management application developed using Python, Flask, MySQL, HTML, CSS, and JavaScript.

The application helps investors manage portfolios, track securities, record stock transactions, and monitor portfolio performance through a simple web interface.

The project demonstrates the practical implementation of relational database concepts, SQL queries, database relationships, and CRUD operations.

## Project Objectives

- Design and implement a relational database for stock portfolio management.
- Maintain investor, portfolio, security, and transaction records.
- Perform database operations using SQL.
- Connect a Flask application to a MySQL database.
- Present portfolio and investment information through a web interface.

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python, Flask |
| Database | MySQL |
| Database Connectivity | MySQL Connector |
| Version Control | Git and GitHub |

## Application Features

- **Investor Management:** View and manage investor records.
- **Portfolio Management:** Organize portfolios associated with investors.
- **Security Management:** Maintain stock and security information.
- **Portfolio Positions:** Track securities held in portfolios.
- **Trade Management:** Record and manage BUY and SELL transactions.
- **Watchlist:** Maintain a list of securities users want to monitor.
- **Portfolio Analytics:** View investment performance and related portfolio metrics.
- **Transaction History:** Review recorded transactions and their details.

## Database Design

The application uses a relational MySQL database named `stock_portfolio_management`.

### Main Tables

| Table | Purpose |
|---|---|
| `INVESTOR` | Stores investor information. |
| `PORTFOLIO` | Stores portfolio records associated with investors. |
| `SECURITY` | Stores information about available securities. |
| `PORTFOLIO_POSITION` | Maintains securities held in portfolios. |
| `TRADE` | Stores BUY and SELL transaction records. |
| `WATCHLIST` | Maintains securities added to a watchlist. |

The database uses relationships between entities to maintain consistency and reduce unnecessary data duplication.

## SQL Implementation

The project demonstrates SQL operations used in a practical stock portfolio management system.

### 1. Create and Select Database

```sql
CREATE DATABASE stock_portfolio_management;

USE stock_portfolio_management;
```

### 2. Retrieve Records

```sql
-- View all investors
SELECT * FROM INVESTOR;

-- View all portfolios
SELECT * FROM PORTFOLIO;

-- View available securities
SELECT * FROM SECURITY;

-- View recorded trades
SELECT * FROM TRADE;
```

### 3. Filter Records

```sql
-- Retrieve a specific investor
SELECT *
FROM INVESTOR
WHERE investor_id = 1;

-- Retrieve transactions for a portfolio
SELECT *
FROM TRADE
WHERE portfolio_id = 1;
```

*Note: These examples assume the corresponding columns exist in the database schema.*

### 4. Aggregate Functions

```sql
-- Count total investors
SELECT COUNT(*) AS total_investors
FROM INVESTOR;

-- Count total portfolios
SELECT COUNT(*) AS total_portfolios
FROM PORTFOLIO;

-- Count total securities
SELECT COUNT(*) AS total_securities
FROM SECURITY;

-- Count total trades
SELECT COUNT(*) AS total_trades
FROM TRADE;
```

### 5. Sorting and Grouping

```sql
-- Display portfolios in descending order
SELECT *
FROM PORTFOLIO
ORDER BY portfolio_id DESC;

-- Count trades for each portfolio
SELECT portfolio_id, COUNT(*) AS total_trades
FROM TRADE
GROUP BY portfolio_id;
```

### 6. JOIN Operations

JOIN operations can combine related information stored across multiple tables.

```sql
-- Retrieve portfolios along with investor information
SELECT *
FROM INVESTOR i
INNER JOIN PORTFOLIO p
ON i.investor_id = p.investor_id;
```

*The JOIN examples should be checked against the actual column names and foreign-key relationships in the database scripts.*

## Project Structure

```text
EquityDesk/
│
├── backend/
│   ├── app.py
│   ├── config.py
│   └── requirements.txt
│
├── database/
│   ├── SQL schema and migration files
│   └── Supporting database files
│
├── frontend/
│   ├── index.html
│   ├── css/
│   └── js/
│
├── tests/
│
├── .gitignore
├── README.md
└── PROJECT_STATE.md
```

## Installation and Setup

### Prerequisites

- Python 3.9 or above
- MySQL Server
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/Hardikkagg/EquityDesk.git
cd EquityDesk
```

### 2. Install Dependencies

```bash
pip install -r backend/requirements.txt
```

### 3. Configure Database

Create the database and execute the required SQL schema and migration scripts from the `database/` directory.

Create a local `.env` file in the project root using the following placeholders:

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=your_mysql_username
MYSQL_PASSWORD=your_local_password
MYSQL_DB=stock_portfolio_management
```

**Do not upload `.env` or actual database credentials to GitHub.**

### 4. Run the Application

```bash
python backend/app.py
```

Open the application in your browser:

```text
http://127.0.0.1:5000
```

## Testing

Run the project's tests using:

```bash
python -m unittest discover -s tests -v
```

Database integration tests may require a configured MySQL server and appropriate database permissions.

## Learning Outcomes

This project provides practical exposure to:

- Relational Database Management Systems (RDBMS)
- Entity Relationship modelling
- Relational schema design
- Primary and Foreign Keys
