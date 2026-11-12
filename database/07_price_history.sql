-- Run against the intended stock_portfolio_management database.
-- This migration adds only imported historical closes; it never changes
-- SECURITY.current_price or replays historical transactions.

CREATE TABLE IF NOT EXISTS PRICE_HISTORY (
    security_id INT NOT NULL,
    price_date DATE NOT NULL,
    close_price DECIMAL(12,2) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_price_history PRIMARY KEY (security_id, price_date),
    CONSTRAINT fk_price_history_security
        FOREIGN KEY (security_id)
        REFERENCES SECURITY(security_id)
        ON DELETE RESTRICT,
    CONSTRAINT chk_price_history_close_price CHECK (close_price > 0),
    KEY idx_price_history_price_date (price_date)
) ENGINE=InnoDB;
