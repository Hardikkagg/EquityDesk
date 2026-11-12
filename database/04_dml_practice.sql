-- created database stock_portfolio_management for project
CREATE DATABASE stock_portfolio_management;

-- show list of databases in the system
SHOW DATABASES;

-- use the database stock_portfolio_management for work
USE stock_portfolio_management;


-- Create the INVESTOR table
CREATE TABLE INVESTOR (
    investor_id INT PRIMARY KEY,
    investor_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(15),
    date_joined DATE NOT NULL
);

-- describe the table 
DESCRIBE INVESTOR;

-- Create PORTFOLIO table
CREATE TABLE PORTFOLIO (
    portfolio_id INT PRIMARY KEY ,
    investor_id INT NOT NULL,
    portfolio_name VARCHAR(100) NOT NULL,
    created_date DATE NOT NULL,

    CONSTRAINT fk_portfolio_investor
        FOREIGN KEY (investor_id)
        REFERENCES INVESTOR(investor_id)
);
DESCRIBE PORTFOLIO;
SHOW CREATE TABLE PORTFOLIO;

-- Create SECURITY table
CREATE TABLE SECURITY (
    security_id INT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL UNIQUE,
    security_name VARCHAR(100) NOT NULL,
    sector VARCHAR(50),
    current_price DECIMAL(12,2) NOT NULL
);

DESCRIBE SECURITY;

-- Create PORTFOLIO_POSITION table
CREATE TABLE PORTFOLIO_POSITION (
    position_id INT PRIMARY KEY,
    portfolio_id INT NOT NULL,
    security_id INT NOT NULL,
    quantity INT NOT NULL,
    average_buy_price DECIMAL(12,2) NOT NULL,

    CONSTRAINT fk_position_portfolio
        FOREIGN KEY (portfolio_id)
        REFERENCES PORTFOLIO(portfolio_id),

    CONSTRAINT fk_position_security
        FOREIGN KEY (security_id)
        REFERENCES SECURITY(security_id)
);

DESCRIBE PORTFOLIO_POSITION;

-- Create TRADE table
CREATE TABLE TRADE (
    trade_id INT PRIMARY KEY ,
    investor_id INT NOT NULL,
    security_id INT NOT NULL,
    portfolio_id INT NOT NULL,
    trade_type VARCHAR(10) NOT NULL,
    quantity INT NOT NULL,
    trade_price DECIMAL(12,2) NOT NULL,
    trade_date DATE NOT NULL,

    CONSTRAINT fk_trade_investor
        FOREIGN KEY (investor_id)
        REFERENCES INVESTOR(investor_id),

    CONSTRAINT fk_trade_security
        FOREIGN KEY (security_id)
        REFERENCES SECURITY(security_id),

    CONSTRAINT fk_trade_portfolio
        FOREIGN KEY (portfolio_id)
        REFERENCES PORTFOLIO(portfolio_id),

    CONSTRAINT chk_trade_type
        CHECK (trade_type IN ('BUY', 'SELL'))
);

DESCRIBE TRADE;

INSERT INTO INVESTOR
    (investor_name, email, phone, date_joined)
VALUES
    ('Rahul Sharma', 'rahul.sharma@example.com', '9876543210', '2026-01-15'),
    ('Priya Menon', 'priya.menon@example.com', '9876543211', '2026-01-20'),
    ('Arjun Mehta', 'arjun.mehta@example.com', '9876543212', '2026-02-05'),
    ('Sneha Iyer', 'sneha.iyer@example.com', '9876543213', '2026-02-12'),
    ('Karan Kapoor', 'karan.kapoor@example.com', '9876543214', '2026-02-18'),
    ('Ananya Rao', 'ananya.rao@example.com', '9876543215', '2026-02-25'),
    ('Vikram Singh', 'vikram.singh@example.com', '9876543216', '2026-03-01'),
    ('Neha Verma', 'neha.verma@example.com', '9876543217', '2026-03-08'),
    ('Aditya Nair', 'aditya.nair@example.com', '9876543218', '2026-03-15'),
    ('Meera Krishnan', 'meera.krishnan@example.com', '9876543219', '2026-03-22'),
    ('Rohan Malhotra', 'rohan.malhotra@example.com', '9876543220', '2026-03-29'),
    ('Ishita Das', 'ishita.das@example.com', '9876543221', '2026-04-03'),
    ('Nikhil Joshi', 'nikhil.joshi@example.com', '9876543222', '2026-04-10'),
    ('Pooja Agarwal', 'pooja.agarwal@example.com', '9876543223', '2026-04-17'),
    ('Siddharth Jain', 'siddharth.jain@example.com', '9876543224', '2026-04-24'),
    ('Aditi Shah', 'aditi.shah@example.com', '9876543225', '2026-05-01'),
    ('Manish Gupta', 'manish.gupta@example.com', '9876543226', '2026-05-08'),
    ('Divya Pillai', 'divya.pillai@example.com', '9876543227', '2026-05-15'),
    ('Yash Bansal', 'yash.bansal@example.com', '9876543228', '2026-05-22'),
    ('Simran Kaur', 'simran.kaur@example.com', '9876543229', '2026-05-29');
    
INSERT INTO PORTFOLIO
    (investor_id, portfolio_name, created_date)
VALUES
    (1, 'Long Term Wealth', '2026-01-16'),
    (2, 'Growth Portfolio', '2026-01-21'),
    (3, 'Blue Chip Portfolio', '2026-02-06'),
    (4, 'Balanced Portfolio', '2026-02-13'),
    (5, 'Technology Portfolio', '2026-02-19'),
    (6, 'Dividend Portfolio', '2026-02-26'),
    (7, 'High Growth Portfolio', '2026-03-02'),
    (8, 'Core Investments', '2026-03-09'),
    (9, 'Future Wealth', '2026-03-16'),
    (10, 'Diversified Portfolio', '2026-03-23'),
    (11, 'Equity Growth', '2026-03-30'),
    (12, 'Large Cap Portfolio', '2026-04-04'),
    (13, 'Market Leaders', '2026-04-11'),
    (14, 'Income Portfolio', '2026-04-18'),
    (15, 'Aggressive Growth', '2026-04-25'),
    (16, 'Long Term Equity', '2026-05-02'),
    (17, 'Value Portfolio', '2026-05-09'),
    (18, 'Core and Satellite', '2026-05-16'),
    (19, 'Multi Sector Portfolio', '2026-05-23'),
    (20, 'Strategic Portfolio', '2026-05-30');

INSERT INTO SECURITY
    (symbol, security_name, sector, current_price)
VALUES
    ('TCS', 'Tata Consultancy Services', 'Information Technology', 3125.50),
    ('INFY', 'Infosys', 'Information Technology', 1482.75),
    ('RELIANCE', 'Reliance Industries', 'Energy', 2910.40),
    ('HDFCBANK', 'HDFC Bank', 'Banking', 1725.20),
    ('ICICIBANK', 'ICICI Bank', 'Banking', 1398.60),
    ('ITC', 'ITC Limited', 'FMCG', 512.35),
    ('SBIN', 'State Bank of India', 'Banking', 845.70),
    ('BHARTIARTL', 'Bharti Airtel', 'Telecommunications', 1865.30),
    ('LT', 'Larsen and Toubro', 'Infrastructure', 3680.25),
    ('HINDUNILVR', 'Hindustan Unilever', 'FMCG', 2548.90),
    ('MARUTI', 'Maruti Suzuki India', 'Automobile', 14250.00),
    ('M&M', 'Mahindra and Mahindra', 'Automobile', 3185.45),
    ('SUNPHARMA', 'Sun Pharmaceutical Industries', 'Pharmaceuticals', 1762.80),
    ('AXISBANK', 'Axis Bank', 'Banking', 1248.50),
    ('KOTAKBANK', 'Kotak Mahindra Bank', 'Banking', 2015.75),
    ('WIPRO', 'Wipro', 'Information Technology', 548.30),
    ('HCLTECH', 'HCL Technologies', 'Information Technology', 1698.65),
    ('ASIANPAINT', 'Asian Paints', 'Consumer Goods', 2385.40),
    ('TITAN', 'Titan Company', 'Consumer Goods', 3642.15),
    ('ADANIPORTS', 'Adani Ports and SEZ', 'Infrastructure', 1485.90),
    ('NTPC', 'NTPC Limited', 'Power', 412.25),
    ('POWERGRID', 'Power Grid Corporation of India', 'Power', 348.70),
    ('COALINDIA', 'Coal India', 'Mining', 468.55),
    ('TATASTEEL', 'Tata Steel', 'Metals', 184.20),
    ('HINDALCO', 'Hindalco Industries', 'Metals', 756.80);
    
INSERT INTO PORTFOLIO_POSITION
    (portfolio_id, security_id, quantity, average_buy_price)
VALUES
    (1, 1, 25, 2850.00),
    (1, 4, 30, 1640.50),
    (2, 2, 40, 1325.75),
    (2, 3, 15, 2680.00),
    (3, 5, 35, 1180.25),
    (3, 6, 100, 465.80),
    (4, 7, 50, 720.40),
    (4, 8, 20, 1620.00),
    (5, 1, 15, 2945.50),
    (5, 17, 25, 1510.25),
    (6, 6, 150, 438.60),
    (6, 23, 80, 425.30),
    (7, 3, 30, 2795.00),
    (7, 9, 18, 3320.75),
    (8, 10, 45, 2380.00),
    (8, 18, 20, 2210.50),
    (9, 11, 12, 12950.00),
    (9, 12, 25, 2740.80),
    (10, 13, 40, 1585.25),
    (10, 14, 35, 1120.00),
    (11, 15, 22, 1850.60),
    (12, 16, 100, 510.75),
    (13, 19, 15, 3250.00),
    (14, 20, 30, 1325.50),
    (15, 25, 60, 690.25);
    
INSERT INTO TRADE
    (investor_id, security_id, portfolio_id, trade_type, quantity, trade_price, trade_date)
VALUES
    (1, 1, 1, 'BUY', 25, 2850.00, '2026-01-17'),
    (1, 4, 1, 'BUY', 30, 1640.50, '2026-01-18'),

    (2, 2, 2, 'BUY', 40, 1325.75, '2026-01-22'),
    (2, 3, 2, 'BUY', 15, 2680.00, '2026-01-23'),

    (3, 5, 3, 'BUY', 35, 1180.25, '2026-02-07'),
    (3, 6, 3, 'BUY', 100, 465.80, '2026-02-08'),

    (4, 7, 4, 'BUY', 50, 720.40, '2026-02-14'),
    (4, 8, 4, 'BUY', 20, 1620.00, '2026-02-15'),

    (5, 1, 5, 'BUY', 15, 2945.50, '2026-02-20'),
    (5, 17, 5, 'BUY', 25, 1510.25, '2026-02-21'),

    (6, 6, 6, 'BUY', 150, 438.60, '2026-02-27'),
    (6, 23, 6, 'BUY', 80, 425.30, '2026-02-28'),

    (7, 3, 7, 'BUY', 30, 2795.00, '2026-03-03'),
    (7, 9, 7, 'BUY', 18, 3320.75, '2026-03-04'),

    (8, 10, 8, 'BUY', 45, 2380.00, '2026-03-10'),
    (8, 18, 8, 'BUY', 20, 2210.50, '2026-03-11'),

    (9, 11, 9, 'BUY', 12, 12950.00, '2026-03-17'),
    (9, 12, 9, 'BUY', 25, 2740.80, '2026-03-18'),

    (10, 13, 10, 'BUY', 40, 1585.25, '2026-03-24'),
    (10, 14, 10, 'BUY', 35, 1120.00, '2026-03-25'),

    (11, 15, 11, 'BUY', 22, 1850.60, '2026-03-31'),
    (12, 16, 12, 'BUY', 100, 510.75, '2026-04-05'),

    (13, 19, 13, 'BUY', 15, 3250.00, '2026-04-12'),
    (14, 20, 14, 'BUY', 30, 1325.50, '2026-04-19'),

    (15, 25, 15, 'BUY', 60, 690.25, '2026-04-26');
    
SELECT 'INVESTOR' AS table_name, COUNT(*) AS record_count
FROM INVESTOR

UNION ALL

SELECT 'PORTFOLIO', COUNT(*)
FROM PORTFOLIO

UNION ALL

SELECT 'SECURITY', COUNT(*)
FROM SECURITY

UNION ALL

SELECT 'PORTFOLIO_POSITION', COUNT(*)
FROM PORTFOLIO_POSITION

UNION ALL

SELECT 'TRADE', COUNT(*)
FROM TRADE;


-- DML COMMANDS

SELECT * FROM INVESTOR;
SELECT * FROM SECURITY;

-- 1. INSERT — Add a new record
INSERT INTO INVESTOR
    (investor_name, email, phone, date_joined)
VALUES
    ('Demo Investor', 'demo.investor@example.com', '9000000000', '2026-09-06');
SELECT * FROM INVESTOR
WHERE email = 'demo.investor@example.com';
-- 2. INSERT — Insert selected columns
INSERT INTO INVESTOR
    (investor_name, email, date_joined)
VALUES
    ('Test Investor', 'test.investor@example.com', '2026-09-06');

SELECT * FROM INVESTOR
WHERE email = 'test.investor@example.com';


DELETE FROM INVESTOR
WHERE email IN (
    'demo.investor@example.com',
    'test.investor@example.com'
);

SELECT *
FROM INVESTOR
WHERE email IN (
    'demo.investor@example.com',
    'test.investor@example.com'
);

-- 3. UPDATE — Modify existing records

SELECT investor_id, investor_name, phone
FROM INVESTOR
WHERE investor_id = 2;

UPDATE INVESTOR
SET phone = '8888888888'
WHERE investor_id = 2;

SELECT investor_id, investor_name, phone
FROM INVESTOR
WHERE investor_id = 2;

UPDATE INVESTOR
SET phone = '9876543211'
WHERE investor_id = 2;

-- 4. DELETE — Remove records
INSERT INTO INVESTOR
    (investor_name, email, phone, date_joined)
VALUES
    ('Delete Demo', 'delete.demo@example.com', '9000000001', '2026-09-06');
    
DELETE FROM INVESTOR
WHERE email = 'delete.demo@example.com';

SELECT *
FROM INVESTOR
WHERE email = 'delete.demo@example.com';

-- 5. SELECT — Display all columns
SELECT *
FROM INVESTOR;

-- 6. SELECT — Display selected columns
SELECT investor_name, email, date_joined
FROM INVESTOR;

-- 7. SELECT with WHERE — Filter records
SELECT *
FROM SECURITY
WHERE current_price > 2000;

-- 8. LIKE — Search using a pattern
SELECT *
FROM INVESTOR
WHERE investor_name LIKE 'A%';

SELECT *
FROM SECURITY
WHERE security_name LIKE '%Bank%';

-- 9. ORDER BY — Sort results
SELECT symbol, security_name, current_price
FROM SECURITY
ORDER BY current_price DESC;

SELECT symbol, security_name, current_price
FROM SECURITY
ORDER BY current_price ASC;

-- 10. DISTINCT — Remove duplicate values
SELECT DISTINCT sector
FROM SECURITY;

-- 11. LIMIT — Restrict number of rows
SELECT *
FROM SECURITY
LIMIT 5;

SELECT symbol, security_name, current_price
FROM SECURITY
ORDER BY current_price DESC
LIMIT 5;

-- 12. GROUP BY — Group records
SELECT sector, COUNT(*) AS security_count
FROM SECURITY
GROUP BY sector;

-- 13. HAVING — Filter grouped data
SELECT sector, COUNT(*) AS security_count
FROM SECURITY
GROUP BY sector
HAVING COUNT(*) > 2;

-- 14. Addition
SELECT
    symbol,
    current_price,
    current_price + 100 AS price_after_increase
FROM SECURITY;

-- 15. Subtraction
SELECT
    symbol,
    current_price,
    current_price - 100 AS reduced_price
FROM SECURITY;

-- 16. Multiplication
SELECT
    portfolio_id,
    security_id,
    quantity,
    average_buy_price,
    quantity * average_buy_price AS investment_value
FROM PORTFOLIO_POSITION;

-- 17. Division
SELECT
    position_id,
    quantity,
    average_buy_price,
    (quantity * average_buy_price) / quantity AS calculated_average_price
FROM PORTFOLIO_POSITION;

-- 18. AND
SELECT *
FROM SECURITY
WHERE sector = 'Banking'
AND current_price > 1000;

-- 19. OR
SELECT *
FROM SECURITY
WHERE sector = 'Banking'
OR sector = 'Information Technology';

-- 20. NOT
SELECT *
FROM SECURITY
WHERE NOT sector = 'Banking';

-- 21. Equal
SELECT *
FROM SECURITY
WHERE sector = 'Banking';

-- 22. Not equal
SELECT *
FROM SECURITY
WHERE sector != 'Banking';

-- 23. Greater than
SELECT symbol, security_name, current_price
FROM SECURITY
WHERE current_price > 2000;

-- 24. Less than
SELECT symbol, security_name, current_price
FROM SECURITY
WHERE current_price < 1000;

-- 25. Greater than or equal
SELECT symbol, security_name, current_price
FROM SECURITY
WHERE current_price >= 2000;

-- 26. Less than or equal
SELECT symbol, security_name, current_price
FROM SECURITY
WHERE current_price <= 1000;

-- Portfolio investment value
SELECT
    p.portfolio_id,
    p.portfolio_name,
    pp.security_id,
    s.symbol,
    pp.quantity,
    pp.average_buy_price,
    pp.quantity * pp.average_buy_price AS invested_value
FROM PORTFOLIO p
JOIN PORTFOLIO_POSITION pp
    ON p.portfolio_id = pp.portfolio_id
JOIN SECURITY s
    ON pp.security_id = s.security_id;
    
-- Portfolio with investor name
SELECT
    i.investor_name,
    p.portfolio_name,
    p.created_date
FROM INVESTOR i
JOIN PORTFOLIO p
    ON i.investor_id = p.investor_id;
    
-- Complete trade information
SELECT
    t.trade_id,
    i.investor_name,
    p.portfolio_name,
    s.symbol,
    t.trade_type,
    t.quantity,
    t.trade_price,
    t.trade_date
FROM TRADE t
JOIN INVESTOR i
    ON t.investor_id = i.investor_id
JOIN PORTFOLIO p
    ON t.portfolio_id = p.portfolio_id
JOIN SECURITY s
    ON t.security_id = s.security_id;
    
select * from portfolio;
