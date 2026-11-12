-- Cursor — Display all securities
DELIMITER $$

CREATE PROCEDURE show_all_securities()
BEGIN

    DECLARE done INT DEFAULT 0;
    DECLARE v_symbol VARCHAR(20);
    DECLARE v_price DECIMAL(12,2);

    DECLARE security_cursor CURSOR FOR
        SELECT symbol, current_price
        FROM SECURITY;

    DECLARE CONTINUE HANDLER FOR NOT FOUND
        SET done = 1;

    OPEN security_cursor;

    read_loop: LOOP

        FETCH security_cursor
        INTO v_symbol, v_price;

        IF done = 1 THEN
            LEAVE read_loop;
        END IF;

        SELECT v_symbol AS Symbol,
               v_price AS Current_Price;

    END LOOP;

    CLOSE security_cursor;

END$$

DELIMITER ;
CALL show_all_securities();

-- Cursor 2 - Display all portfolio names and their creation dates
DELIMITER $$

CREATE PROCEDURE show_portfolios()
BEGIN
    DECLARE done INT DEFAULT 0;
    DECLARE v_name VARCHAR(100);
    DECLARE v_date DATE;

    DECLARE portfolio_cursor CURSOR FOR
        SELECT portfolio_name, created_date
        FROM PORTFOLIO;

    DECLARE CONTINUE HANDLER FOR NOT FOUND
        SET done = 1;

    OPEN portfolio_cursor;

    read_loop: LOOP

        FETCH portfolio_cursor
        INTO v_name, v_date;

        IF done = 1 THEN
            LEAVE read_loop;
        END IF;

        SELECT v_name AS Portfolio_Name,
               v_date AS Created_Date;

    END LOOP;

    CLOSE portfolio_cursor;
END$$

DELIMITER ;

CALL show_portfolios();

-- cursor 3 - Display all securities and their current prices
DELIMITER $$

CREATE PROCEDURE show_security_prices()
BEGIN
    DECLARE done INT DEFAULT 0;
    DECLARE v_symbol VARCHAR(20);
    DECLARE v_price DECIMAL(12,2);

    DECLARE security_cursor CURSOR FOR
        SELECT symbol, current_price
        FROM SECURITY;

    DECLARE CONTINUE HANDLER FOR NOT FOUND
        SET done = 1;

    OPEN security_cursor;

    read_loop: LOOP

        FETCH security_cursor
        INTO v_symbol, v_price;

        IF done = 1 THEN
            LEAVE read_loop;
        END IF;

        SELECT v_symbol AS Symbol,
               v_price AS Current_Price;

    END LOOP;

    CLOSE security_cursor;
END$$

DELIMITER ;
CALL show_security_prices();