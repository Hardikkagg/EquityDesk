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

