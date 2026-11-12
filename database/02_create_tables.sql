-- Create the INVESTOR table
CREATE TABLE INVESTOR (
    investor_id INT PRIMARY KEY,
    investor_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(15),
    date_joined DATE NOT NULL
);

-- describe the table 
DESCRIBE INVESTOR;

-- Create PORTFOLIO table
CREATE TABLE PORTFOLIO (
    portfolio_id INT PRIMARY KEY ,
    investor_id INT NOT NULL,
    portfolio_name VARCHAR(100) NOT NULL,
    created_date DATE NOT NULL,

    CONSTRAINT fk_portfolio_investor
        FOREIGN KEY (investor_id)
        REFERENCES INVESTOR(investor_id)
);
DESCRIBE PORTFOLIO;
SHOW CREATE TABLE PORTFOLIO;

-- Create SECURITY table
CREATE TABLE SECURITY (
    security_id INT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL UNIQUE,
    security_name VARCHAR(100) NOT NULL,
    sector VARCHAR(50),
    current_price DECIMAL(12,2) NOT NULL
);

DESCRIBE SECURITY;

-- Create PORTFOLIO_POSITION table
CREATE TABLE PORTFOLIO_POSITION (
    position_id INT PRIMARY KEY,
    portfolio_id INT NOT NULL,
    security_id INT NOT NULL,
    quantity INT NOT NULL,
    average_buy_price DECIMAL(12,2) NOT NULL,

    CONSTRAINT fk_position_portfolio
        FOREIGN KEY (portfolio_id)
        REFERENCES PORTFOLIO(portfolio_id),

    CONSTRAINT fk_position_security
        FOREIGN KEY (security_id)
        REFERENCES SECURITY(security_id)
);

DESCRIBE PORTFOLIO_POSITION;

-- Create TRADE table
CREATE TABLE TRADE (
    trade_id INT PRIMARY KEY ,
    investor_id INT NOT NULL,
    security_id INT NOT NULL,
    portfolio_id INT NOT NULL,
    trade_type VARCHAR(10) NOT NULL,
    quantity INT NOT NULL,
    trade_price DECIMAL(12,2) NOT NULL,
    trade_date DATE NOT NULL,

    CONSTRAINT fk_trade_investor
        FOREIGN KEY (investor_id)
        REFERENCES INVESTOR(investor_id),

    CONSTRAINT fk_trade_security
        FOREIGN KEY (security_id)
        REFERENCES SECURITY(security_id),

    CONSTRAINT fk_trade_portfolio
        FOREIGN KEY (portfolio_id)
        REFERENCES PORTFOLIO(portfolio_id),

    CONSTRAINT chk_trade_type
        CHECK (trade_type IN ('BUY', 'SELL'))
);

DESCRIBE TRADE;
