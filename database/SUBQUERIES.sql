-- Query 1 — Single-row subquery using > - Find all securities whose current price is greater than the average current price of all securities.
SELECT symbol, security_name, current_price
FROM SECURITY
WHERE current_price > (
    SELECT AVG(current_price)
    FROM SECURITY
);

-- Query 2 — IN Find all investors who have performed at least one trade.
SELECT investor_id, investor_name
FROM INVESTOR
WHERE investor_id IN (
    SELECT investor_id
    FROM TRADE
);

-- Query 3 — NOT IN Find investors who have never performed a trade.
SELECT investor_id, investor_name
FROM INVESTOR
WHERE investor_id NOT IN (
    SELECT investor_id
    FROM TRADE
);

-- Query 4 — ANY - Find securities whose current price is greater than the price of at least one Banking security.
SELECT symbol, security_name, current_price
FROM SECURITY
WHERE current_price > ANY (
    SELECT current_price
    FROM SECURITY
    WHERE sector = 'Banking'
);

-- Query 5 — ALL -Find securities whose current price is greater than every Banking security.
SELECT symbol, security_name, current_price
FROM SECURITY
WHERE current_price > ALL (
    SELECT current_price
    FROM SECURITY
    WHERE sector = 'Banking'
);

-- Query 6 — EXISTS - Find investors who have at least one portfolio.
SELECT i.investor_id, i.investor_name
FROM INVESTOR i
WHERE EXISTS (
    SELECT 1
    FROM PORTFOLIO p
    WHERE p.investor_id = i.investor_id
);

-- Query 7 — NOT EXISTS - Find investors who do not have any portfolio.
SELECT i.investor_id, i.investor_name
FROM INVESTOR i
WHERE NOT EXISTS (
    SELECT 1
    FROM PORTFOLIO p
    WHERE p.investor_id = i.investor_id
);