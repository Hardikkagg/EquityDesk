-- Function 1 — Calculate Portfolio Invested Value- This calculates: quantity × average_buy_price for all holdings in a portfolio.
USE stock_portfolio_management;

DELIMITER $$

CREATE FUNCTION get_portfolio_invested_value(p_portfolio_id INT)
RETURNS DECIMAL(15,2)
DETERMINISTIC
BEGIN
    DECLARE total_value DECIMAL(15,2);

    SELECT COALESCE(
        SUM(quantity * average_buy_price), 0
    )
    INTO total_value
    FROM PORTFOLIO_POSITION
    WHERE portfolio_id = p_portfolio_id;

    RETURN total_value;
END$$

DELIMITER ;

SELECT get_portfolio_invested_value(1) AS invested_value;

-- FUNCTION — Calculate Current Portfolio Value
DELIMITER $$

CREATE FUNCTION get_portfolio_current_value(p_portfolio_id INT)
RETURNS DECIMAL(15,2)
DETERMINISTIC
BEGIN
    DECLARE total_value DECIMAL(15,2);

    SELECT COALESCE(
        SUM(pp.quantity * s.current_price), 0
    )
    INTO total_value
    FROM PORTFOLIO_POSITION pp
    JOIN SECURITY s
        ON pp.security_id = s.security_id
    WHERE pp.portfolio_id = p_portfolio_id;

    RETURN total_value;
END$$

DELIMITER ;

SELECT get_portfolio_current_value(1) AS current_value;

-- FUNCTION — Calculate Portfolio P&L
DELIMITER $$

CREATE FUNCTION get_portfolio_pnl(p_portfolio_id INT)
RETURNS DECIMAL(15,2)
DETERMINISTIC
BEGIN
    DECLARE pnl DECIMAL(15,2);

    SELECT COALESCE(
        SUM(
            pp.quantity * s.current_price
            - pp.quantity * pp.average_buy_price
        ), 0
    )
    INTO pnl
    FROM PORTFOLIO_POSITION pp
    JOIN SECURITY s
        ON pp.security_id = s.security_id
    WHERE pp.portfolio_id = p_portfolio_id;

    RETURN pnl;
END$$

DELIMITER ;

SELECT get_portfolio_pnl(1) AS portfolio_profit_loss;

