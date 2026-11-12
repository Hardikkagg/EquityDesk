-- Query 8 — Nested subquery - Find securities whose current price is greater than the average price of securities in the Banking sector.
SELECT symbol, security_name, current_price
FROM SECURITY
WHERE current_price > (
    SELECT AVG(current_price)
    FROM SECURITY
    WHERE sector = (
        SELECT sector
        FROM SECURITY
        WHERE symbol = 'HDFCBANK'
    )
);

-- Query 9 — Correlated query - Find securities whose current price is greater than the average price of their own sector.
SELECT s1.symbol,
       s1.security_name,
       s1.sector,
       s1.current_price
FROM SECURITY s1
WHERE s1.current_price > (
    SELECT AVG(s2.current_price)
    FROM SECURITY s2
    WHERE s2.sector = s1.sector
);

-- Query 10 — Correlated query using portfolio position - Find portfolio positions whose average buy price is greater than the average buy price of that security across all portfolios.
SELECT pp1.portfolio_id,
       pp1.security_id,
       pp1.quantity,
       pp1.average_buy_price
FROM PORTFOLIO_POSITION pp1
WHERE pp1.average_buy_price > (
    SELECT AVG(pp2.average_buy_price)
    FROM PORTFOLIO_POSITION pp2
    WHERE pp2.security_id = pp1.security_id
);

-- Query 11 — Correlated EXISTS - Find securities that are currently held in at least one portfolio.
SELECT s.security_id,
       s.symbol,
       s.security_name
FROM SECURITY s
WHERE EXISTS (
    SELECT 1
    FROM PORTFOLIO_POSITION pp
    WHERE pp.security_id = s.security_id
);

-- Query - Find investors who own portfolios containing TCS
SELECT investor_id, investor_name
FROM INVESTOR
WHERE investor_id IN (
    SELECT investor_id
    FROM PORTFOLIO
    WHERE portfolio_id IN (
        SELECT portfolio_id
        FROM PORTFOLIO_POSITION
        WHERE security_id = (
            SELECT security_id
            FROM SECURITY
            WHERE symbol = 'TCS'
        )
    )
);

-- Query - Find securities whose price is greater than the average price of IT-sector securities
SELECT symbol, security_name, current_price
FROM SECURITY
WHERE current_price > (
    SELECT AVG(current_price)
    FROM SECURITY
    WHERE sector = (
        SELECT sector
        FROM SECURITY
        WHERE symbol = 'TCS'
    )
);

-- Query - Find portfolios that contain a security priced above the overall average security price
SELECT portfolio_id, portfolio_name
FROM PORTFOLIO
WHERE portfolio_id IN (
    SELECT portfolio_id
    FROM PORTFOLIO_POSITION
    WHERE security_id IN (
        SELECT security_id
        FROM SECURITY
        WHERE current_price > (
            SELECT AVG(current_price)
            FROM SECURITY
        )
    )
);
