-- BCNF documentation
-- Faculty ko ye likh sakte ho:
-- - All determinants are candidate keys or superkeys.
-- - No non-superkey determinant exists.
-- - Therefore, all relations satisfy BCNF.
-- - No further decomposition is required.

-- BCNF ko properly demonstrate karne ke liye bas ye 3 cheezein karo:
-- 1. Functional dependencies likho — har table ki.
-- 2. Candidate keys / determinants identify karo.
-- 3. BCNF verification show karo ki har determinant superkey hai.

USE stock_portfolio_management;

DROP TABLE IF EXISTS TRADE_BCNF;

CREATE TABLE TRADE_BCNF (
    trade_id INT PRIMARY KEY,
    portfolio_id INT NOT NULL,
    security_id INT NOT NULL,
    trade_type VARCHAR(4) NOT NULL,
    quantity INT NOT NULL,
    trade_price DECIMAL(12,2) NOT NULL,
    trade_date DATE NOT NULL,

    FOREIGN KEY (portfolio_id)
        REFERENCES PORTFOLIO_3NF(portfolio_id),

    FOREIGN KEY (security_id)
        REFERENCES SECURITY_3NF(security_id)
);

INSERT INTO TRADE_BCNF
(trade_id, portfolio_id, security_id, trade_type,
 quantity, trade_price, trade_date)
SELECT
    trade_id, portfolio_id, security_id, trade_type,
    quantity, trade_price, trade_date
FROM TRADE_2NF;

SELECT * FROM TRADE_BCNF;

SELECT
    (SELECT COUNT(*) FROM TRADE_2NF) AS original_records,
    (SELECT COUNT(*) FROM TRADE_BCNF) AS bcnf_records;
    
SELECT
    t.trade_id,
    t.portfolio_id,
    p.investor_id,
    t.security_id,
    t.trade_type,
    t.quantity,
    t.trade_price,
    t.trade_date
FROM TRADE_BCNF t
JOIN PORTFOLIO_3NF p
    ON t.portfolio_id = p.portfolio_id;
    
SELECT
    COUNT(*) AS reconstructed_records,
    COUNT(DISTINCT t.trade_id) AS unique_trades
FROM TRADE_BCNF t
JOIN PORTFOLIO_3NF p
    ON t.portfolio_id = p.portfolio_id
JOIN SECURITY_3NF s
    ON t.security_id = s.security_id;