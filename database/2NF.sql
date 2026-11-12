
-- Check the 1NF table
DESCRIBE normalization_1nf_demo;

-- Remove previous 2NF tables if they exist
DROP TABLE IF EXISTS TRADE_2NF;
DROP TABLE IF EXISTS PORTFOLIO_POSITION_2NF;
DROP TABLE IF EXISTS PORTFOLIO_2NF;
DROP TABLE IF EXISTS SECURITY_2NF;
DROP TABLE IF EXISTS INVESTOR_2NF;


-- 1. INVESTOR_2NF
CREATE TABLE INVESTOR_2NF (
    investor_id INT PRIMARY KEY,
    investor_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    phone VARCHAR(15)
);


-- 2. PORTFOLIO_2NF
CREATE TABLE PORTFOLIO_2NF (
    portfolio_id INT PRIMARY KEY,
    investor_id INT NOT NULL,
    portfolio_name VARCHAR(100) NOT NULL,
    created_date DATE NOT NULL,
    FOREIGN KEY (investor_id)
        REFERENCES INVESTOR_2NF(investor_id)
);


-- 3. SECURITY_2NF
CREATE TABLE SECURITY_2NF (
    security_id INT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    security_name VARCHAR(100) NOT NULL,
    sector VARCHAR(50),
    current_price DECIMAL(12,2) NOT NULL
);


-- 4. PORTFOLIO_POSITION_2NF
CREATE TABLE PORTFOLIO_POSITION_2NF (
    portfolio_id INT,
    security_id INT,
    quantity INT NOT NULL,
    average_buy_price DECIMAL(12,2) NOT NULL,
    PRIMARY KEY (portfolio_id, security_id),
    FOREIGN KEY (portfolio_id)
        REFERENCES PORTFOLIO_2NF(portfolio_id),
    FOREIGN KEY (security_id)
        REFERENCES SECURITY_2NF(security_id)
);


-- 5. TRADE_2NF
CREATE TABLE TRADE_2NF (
    trade_id INT PRIMARY KEY,
    investor_id INT NOT NULL,
    security_id INT NOT NULL,
    portfolio_id INT NOT NULL,
    trade_type VARCHAR(4) NOT NULL,
    quantity INT NOT NULL,
    trade_price DECIMAL(12,2) NOT NULL,
    trade_date DATE NOT NULL,
    FOREIGN KEY (investor_id)
        REFERENCES INVESTOR_2NF(investor_id),
    FOREIGN KEY (security_id)
        REFERENCES SECURITY_2NF(security_id),
    FOREIGN KEY (portfolio_id)
        REFERENCES PORTFOLIO_2NF(portfolio_id)
);


-- TRANSFER DATA FROM 1NF TO 2NF

-- 1. Investor data
INSERT INTO INVESTOR_2NF
SELECT DISTINCT
    investor_id,
    investor_name,
    email,
    phone
FROM normalization_1nf_demo;


-- 2. Portfolio data
INSERT INTO PORTFOLIO_2NF
SELECT DISTINCT
    portfolio_id,
    investor_id,
    portfolio_name,
    created_date
FROM normalization_1nf_demo;


-- 3. Security data
-- Exclude NULL security records from empty portfolios
-- INSERT INTO SECURITY_2NF
-- SELECT DISTINCT
--     security_id,
--     symbol,
--     security_name,
--     sector,
--     current_price
-- FROM normalization_1nf_demo
-- WHERE security_id IS NOT NULL;

-- Remove existing 2NF security records
-- DELETE FROM SECURITY_2NF;

-- -- Transfer all securities from original table
-- INSERT INTO SECURITY_2NF
-- SELECT
--     security_id,
--     symbol,
--     security_name,
--     sector,
--     current_price
-- FROM SECURITY;

-- -- Verify
-- SELECT * FROM SECURITY_2NF;

-- SELECT COUNT(*) AS total_securities
-- FROM SECURITY_2NF;


-- 4. Portfolio position data
-- Exclude portfolios without holdings
INSERT INTO PORTFOLIO_POSITION_2NF
SELECT
    portfolio_id,
    security_id,
    quantity,
    average_buy_price
FROM normalization_1nf_demo
WHERE security_id IS NOT NULL;


-- 5. Trade data
-- TRADE was not included in the flattened 1NF table,
-- so transfer it separately from the original TRADE table.
INSERT INTO TRADE_2NF
SELECT
    trade_id,
    investor_id,
    security_id,
    portfolio_id,
    trade_type,
    quantity,
    trade_price,
    trade_date
FROM TRADE;


INSERT INTO SECURITY_2NF (
    security_id,
    symbol,
    security_name,
    sector,
    current_price
)
SELECT
    security_id,
    symbol,
    security_name,
    sector,
    current_price
FROM SECURITY
ON DUPLICATE KEY UPDATE
    symbol = VALUES(symbol),
    security_name = VALUES(security_name),
    sector = VALUES(sector),
    current_price = VALUES(current_price);

-- Verify all records
SELECT * FROM SECURITY_2NF;

SELECT COUNT(*) AS total_securities
FROM SECURITY_2NF;


SELECT * FROM INVESTOR_2NF;

SELECT * FROM PORTFOLIO_2NF;

SELECT * FROM SECURITY_2NF;

SELECT * FROM PORTFOLIO_POSITION_2NF;

SELECT * FROM TRADE_2NF;


-- Count records in all five tables
SELECT 'INVESTOR_2NF' AS table_name, COUNT(*) AS total
FROM INVESTOR_2NF

UNION ALL

SELECT 'PORTFOLIO_2NF', COUNT(*)
FROM PORTFOLIO_2NF

UNION ALL

SELECT 'SECURITY_2NF', COUNT(*)
FROM SECURITY_2NF

UNION ALL

SELECT 'PORTFOLIO_POSITION_2NF', COUNT(*)
FROM PORTFOLIO_POSITION_2NF

UNION ALL

SELECT 'TRADE_2NF', COUNT(*)
FROM TRADE_2NF;



