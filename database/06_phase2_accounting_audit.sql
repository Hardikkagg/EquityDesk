USE stock_portfolio_management;

-- MySQL does not support IF NOT EXISTS in ALTER TABLE on this server.
-- Check the live schema first and only add missing columns so the migration is
-- safe to re-run without touching historical data.

SET @is_voided_exists := (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'trade'
      AND column_name = 'is_voided'
);
SET @sql := IF(@is_voided_exists = 0,
    'ALTER TABLE trade ADD COLUMN is_voided TINYINT(1) NOT NULL DEFAULT 0 AFTER trade_date',
    'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @void_reason_exists := (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'trade'
      AND column_name = 'void_reason'
);
SET @sql := IF(@void_reason_exists = 0,
    'ALTER TABLE trade ADD COLUMN void_reason VARCHAR(255) NULL AFTER is_voided',
    'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @voided_by_exists := (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'trade'
      AND column_name = 'voided_by'
);
SET @sql := IF(@voided_by_exists = 0,
    'ALTER TABLE trade ADD COLUMN voided_by VARCHAR(100) NULL AFTER void_reason',
    'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @voided_at_exists := (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'trade'
      AND column_name = 'voided_at'
);
SET @sql := IF(@voided_at_exists = 0,
    'ALTER TABLE trade ADD COLUMN voided_at DATETIME NULL AFTER voided_by',
    'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

CREATE TABLE IF NOT EXISTS audit_log (
    audit_id BIGINT NOT NULL AUTO_INCREMENT,
    transaction_id INT NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    old_values JSON NULL,
    new_values JSON NULL,
    reason VARCHAR(255) NULL,
    performed_by VARCHAR(100) NOT NULL DEFAULT 'system',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (audit_id),
    KEY idx_audit_transaction (transaction_id),
    KEY idx_audit_action (action_type, created_at),
    CONSTRAINT fk_audit_trade
        FOREIGN KEY (transaction_id)
        REFERENCES trade(trade_id)
        ON DELETE RESTRICT
);
