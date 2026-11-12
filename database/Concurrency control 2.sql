USE stock_portfolio_management;

-- -- Shared Lock (S-Lock)
-- 2
START TRANSACTION;

SELECT *
FROM PORTFOLIO_3NF
WHERE portfolio_id = 1;

-- 3

UPDATE PORTFOLIO_3NF
SET portfolio_name = 'Test Portfolio'
WHERE portfolio_id = 1;
-- 5
ROLLBACK;


-- Exclusive Lock (X-Lock)
-- 2
START TRANSACTION;

UPDATE PORTFOLIO_3NF
SET portfolio_name = 'Exclusive Lock Test'
WHERE portfolio_id = 1;
-- 4 
ROLLBACK;


-- Row-Level Locking
-- 2
START TRANSACTION;

UPDATE TRADE_BCNF
SET quantity = quantity + 5
WHERE trade_id = 1;


-- 4
ROLLBACK;

-- Table-Level Locking
-- 2
SELECT * FROM PORTFOLIO_3NF;

-- Predicate Locking (SERIALIZABLE)
-- 2
INSERT INTO PORTFOLIO_3NF
(portfolio_id, investor_id, portfolio_name, created_date)
VALUES
(21, 1, 'Concurrency Test Portfolio', '2026-11-09');

 -- 4
 ROLLBACK;