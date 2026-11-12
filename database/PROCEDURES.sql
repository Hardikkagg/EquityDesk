-- Procedure 1 — Show investor portfolio - Create a procedure that displays all portfolios belonging to a given investor.
DELIMITER $$

CREATE PROCEDURE get_investor_portfolios(IN p_investor_id INT)
BEGIN

    SELECT
        p.portfolio_id,
        p.portfolio_name,
        p.created_date
    FROM PORTFOLIO p
    WHERE p.investor_id = p_investor_id;

END$$

DELIMITER ;
CALL get_investor_portfolios(1);

-- Procedure 2 — Show portfolio holdings
DELIMITER $$

CREATE PROCEDURE get_portfolio_holdings(IN p_portfolio_id INT)
BEGIN

    SELECT
        s.symbol,
        s.security_name,
        pp.quantity,
        pp.average_buy_price,
        s.current_price,
        pp.quantity * pp.average_buy_price AS invested_value,
        pp.quantity * s.current_price AS current_value
    FROM PORTFOLIO_POSITION pp
    JOIN SECURITY s
        ON pp.security_id = s.security_id
    WHERE pp.portfolio_id = p_portfolio_id;

END$$

DELIMITER ;
CALL get_portfolio_holdings(1);

-- Procedure 3 - Procedure to display an investor's trade history
DELIMITER $$

CREATE PROCEDURE get_investor_trades(IN p_investor_id INT)
BEGIN
    SELECT
        t.trade_id,
        s.symbol,
        s.security_name,
        t.trade_type,
        t.quantity,
        t.trade_price,
        t.trade_date
    FROM TRADE t
    JOIN SECURITY s
        ON t.security_id = s.security_id
    WHERE t.investor_id = p_investor_id
    ORDER BY t.trade_date DESC;
END$$

DELIMITER ;

CALL get_investor_trades(1);

-- procedure 4 - Procedure to display all securities in a particular sector
DELIMITER $$

CREATE PROCEDURE get_securities_by_sector(IN p_sector VARCHAR(50))
BEGIN
    SELECT
        security_id,
        symbol,
        security_name,
        current_price
    FROM SECURITY
    WHERE sector = p_sector
    ORDER BY current_price DESC;
END$$

DELIMITER ;
CALL get_securities_by_sector('Banking');

-- Procedure 5 - Procedure to display portfolio trade summary
DELIMITER $$

CREATE PROCEDURE get_portfolio_trade_summary(IN p_portfolio_id INT)
BEGIN
    SELECT
        p.portfolio_name,
        COUNT(t.trade_id) AS total_trades,
        SUM(t.quantity * t.trade_price) AS total_trade_value
    FROM PORTFOLIO p
    LEFT JOIN TRADE t
        ON p.portfolio_id = t.portfolio_id
    WHERE p.portfolio_id = p_portfolio_id
    GROUP BY p.portfolio_id, p.portfolio_name;
END$$

DELIMITER ;

CALL get_portfolio_trade_summary(1);