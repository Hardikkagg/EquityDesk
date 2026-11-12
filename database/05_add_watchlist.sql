USE stock_portfolio_management;

CREATE TABLE IF NOT EXISTS WATCHLIST (
    investor_id INT NOT NULL,
    security_id INT NOT NULL,
    target_price DECIMAL(12,2),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (investor_id, security_id),
    CONSTRAINT fk_watchlist_investor
        FOREIGN KEY (investor_id)
        REFERENCES INVESTOR(investor_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_watchlist_security
        FOREIGN KEY (security_id)
        REFERENCES SECURITY(security_id)
        ON DELETE CASCADE,
    CONSTRAINT chk_watchlist_target_price
        CHECK (target_price IS NULL OR target_price > 0)
);
