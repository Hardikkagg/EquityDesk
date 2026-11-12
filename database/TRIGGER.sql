-- First create audit table
CREATE TABLE TRADE_AUDIT_LOG (
    audit_id INT AUTO_INCREMENT PRIMARY KEY,
    trade_id INT,
    action_type VARCHAR(20),
    action_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Trigger - Create a trigger that automatically records every new trade in the audit table.
DELIMITER $$

CREATE TRIGGER after_trade_insert
AFTER INSERT ON TRADE
FOR EACH ROW
BEGIN

    INSERT INTO TRADE_AUDIT_LOG
    (trade_id, action_type)
    VALUES
    (NEW.trade_id, 'TRADE INSERTED');

END$$

DELIMITER ;

-- testing a trigger

INSERT INTO TRADE
(investor_id, security_id, portfolio_id,
 trade_type, quantity, trade_price, trade_date)
VALUES
(1, 1, 1, 'BUY', 2, 3100.00, '2026-10-06');

SELECT *
FROM TRADE_AUDIT_LOG;

-- TRIGGERS 3- Audit trade updates
DELIMITER $$

CREATE TRIGGER after_trade_update
AFTER UPDATE ON TRADE
FOR EACH ROW
BEGIN
    INSERT INTO TRADE_AUDIT_LOG
    (trade_id, action_type)
    VALUES
    (NEW.trade_id, 'TRADE UPDATED');
END$$

DELIMITER ;

-- Trigger 4 -Audit trade deletion
DELIMITER $$

CREATE TRIGGER after_trade_delete
AFTER DELETE ON TRADE
FOR EACH ROW
BEGIN
    INSERT INTO TRADE_AUDIT_LOG
    (trade_id, action_type)
    VALUES
    (OLD.trade_id, 'TRADE DELETED');
END$$

DELIMITER ;

-- Trigger 5 - Prevent invalid trade quantity
DELIMITER $$

CREATE TRIGGER before_trade_insert
BEFORE INSERT ON TRADE
FOR EACH ROW
BEGIN
    IF NEW.quantity <= 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Trade quantity must be greater than zero';
    END IF;
END$$

DELIMITER ;