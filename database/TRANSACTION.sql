-- Start a transaction
START TRANSACTION;

SELECT * FROM PORTFOLIO_3NF;

-- COMMIT
START TRANSACTION;

UPDATE PORTFOLIO_3NF
SET portfolio_name = 'Growth Portfolio'
WHERE portfolio_id = 1;

COMMIT;

-- ROLLBACK
START TRANSACTION;

UPDATE PORTFOLIO_3NF
SET portfolio_name = 'Temporary Portfolio'
WHERE portfolio_id = 1;

ROLLBACK;

SELECT * FROM PORTFOLIO_3NF
WHERE portfolio_id = 1;

-- SAVEPOINT and ROLLBACK TO SAVEPOINT
START TRANSACTION;

UPDATE PORTFOLIO_3NF
SET portfolio_name = 'Updated Portfolio'
WHERE portfolio_id = 1;

SAVEPOINT sp1;

UPDATE PORTFOLIO_3NF
SET portfolio_name = 'Temporary Name'
WHERE portfolio_id = 1;

ROLLBACK TO SAVEPOINT sp1;

COMMIT;

-- RELEASE SAVEPOINT
START TRANSACTION;

SAVEPOINT sp1;

UPDATE PORTFOLIO_3NF
SET portfolio_name = 'Final Portfolio'
WHERE portfolio_id = 1;

RELEASE SAVEPOINT sp1;

ROLLBACK;