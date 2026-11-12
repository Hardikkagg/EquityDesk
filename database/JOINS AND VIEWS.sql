-- Query 12 — INNER JOIN - Display each investor along with their portfolio.
SELECT
    i.investor_name,
    p.portfolio_name,
    p.created_date
FROM INVESTOR i
INNER JOIN PORTFOLIO p
    ON i.investor_id = p.investor_id;
    
-- Query 13 — Multiple INNER JOIN
SELECT
    p.portfolio_name,
    s.symbol,
    s.security_name,
    pp.quantity,
    pp.average_buy_price,
    s.current_price
FROM PORTFOLIO p
INNER JOIN PORTFOLIO_POSITION pp
    ON p.portfolio_id = pp.portfolio_id
INNER JOIN SECURITY s
    ON pp.security_id = s.security_id;
    
-- Query 14 — LEFT JOIN - Display all investors and their portfolios, including investors who do not have a portfolio.
SELECT
    i.investor_id,
    i.investor_name,
    p.portfolio_name
FROM INVESTOR i
LEFT JOIN PORTFOLIO p
    ON i.investor_id = p.investor_id;

-- Query 15 — RIGHT JOIN - Display all portfolios along with their investors.
SELECT
    i.investor_name,
    p.portfolio_name
FROM INVESTOR i
RIGHT JOIN PORTFOLIO p
    ON i.investor_id = p.investor_id;
    
-- Query 16 — SELF JOIN - Find pairs of securities belonging to the same sector.
SELECT
    s1.symbol AS Security_1,
    s2.symbol AS Security_2,
    s1.sector
FROM SECURITY s1
JOIN SECURITY s2
    ON s1.sector = s2.sector
   AND s1.security_id < s2.security_id;
   
-- Query 17 — CROSS JOIN - Generate all possible investor-security combinations.
SELECT
    i.investor_name,
    s.symbol
FROM INVESTOR i
CROSS JOIN SECURITY s;

-- View 1 — Portfolio Holdings View
CREATE OR REPLACE VIEW portfolio_holdings_view AS
SELECT
    p.portfolio_id,
    p.portfolio_name,
    s.security_id,
    s.symbol,
    s.security_name,
    s.sector,
    pp.quantity,
    pp.average_buy_price,
    s.current_price,
    pp.quantity * pp.average_buy_price AS invested_value,
    pp.quantity * s.current_price AS current_value,
    (pp.quantity * s.current_price)
      - (pp.quantity * pp.average_buy_price) AS profit_loss
FROM PORTFOLIO p
JOIN PORTFOLIO_POSITION pp
    ON p.portfolio_id = pp.portfolio_id
JOIN SECURITY s
    ON pp.security_id = s.security_id;
    
SELECT *
FROM portfolio_holdings_view;

-- View 2 — Complete Trade View
CREATE OR REPLACE VIEW trade_details_view AS
SELECT
    t.trade_id,
    t.trade_date,
    i.investor_name,
    p.portfolio_name,
    s.symbol,
    s.security_name,
    t.trade_type,
    t.quantity,
    t.trade_price,
    t.quantity * t.trade_price AS total_amount
FROM TRADE t
JOIN INVESTOR i
    ON t.investor_id = i.investor_id
JOIN PORTFOLIO p
    ON t.portfolio_id = p.portfolio_id
JOIN SECURITY s
    ON t.security_id = s.security_id;
    
SELECT *
FROM trade_details_view;

