
-- Remove the previous temporary table, if it exists
DROP TEMPORARY TABLE IF EXISTS normalization_1nf_demo;

-- Create the corrected 1NF table
USE stock_portfolio_management;

DROP TEMPORARY TABLE IF EXISTS normalization_1nf_demo;

CREATE TEMPORARY TABLE normalization_1nf_demo AS
SELECT
    i.investor_id,
    i.investor_name,
    i.email,
    i.phone,
    p.portfolio_id,
    p.portfolio_name,
    p.created_date,
    s.security_id,
    s.symbol,
    s.security_name,
    s.sector,
    s.current_price,
    pp.quantity,
    pp.average_buy_price
FROM INVESTOR i
JOIN PORTFOLIO p
    ON i.investor_id = p.investor_id
LEFT JOIN PORTFOLIO_POSITION pp
    ON p.portfolio_id = pp.portfolio_id
LEFT JOIN SECURITY s
    ON pp.security_id = s.security_id;

-- Display all 1NF records
SELECT *
FROM normalization_1nf_demo;

-- Total records
SELECT COUNT(*) AS total_records
FROM normalization_1nf_demo;

-- Count distinct investors
SELECT COUNT(DISTINCT investor_id) AS total_investors
FROM normalization_1nf_demo;

-- Count distinct portfolios
SELECT COUNT(DISTINCT portfolio_id) AS total_portfolios	
FROM normalization_1nf_demo;

-- Portfolios without holdings
SELECT DISTINCT portfolio_id, portfolio_name
FROM normalization_1nf_demo
WHERE security_id IS NULL;