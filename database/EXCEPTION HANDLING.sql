-- Exception Handling — Invalid Investor -This procedure attempts to find an investor. If something goes wrong, the handler catches the SQL exception.
DELIMITER $$

CREATE PROCEDURE check_investor(IN p_investor_id INT)
BEGIN

    DECLARE v_name VARCHAR(100);
    DECLARE error_message VARCHAR(100);

    DECLARE CONTINUE HANDLER FOR SQLEXCEPTION
    BEGIN
        SET error_message = 'An SQL error occurred while retrieving investor';
        SELECT error_message AS message;
    END;

    SELECT investor_name
    INTO v_name
    FROM INVESTOR
    WHERE investor_id = p_investor_id;

    SELECT
        p_investor_id AS investor_id,
        v_name AS investor_name;

END$$

DELIMITER ;

CALL check_investor(1);

-- Exception Handling with NOT FOUND This is particularly useful because SELECT ... INTO can return no row.
DELIMITER $$

CREATE PROCEDURE find_investor(IN p_investor_id INT)
BEGIN

    DECLARE v_name VARCHAR(100);

    DECLARE CONTINUE HANDLER FOR NOT FOUND
    BEGIN
        SELECT 'Investor not found' AS message;
    END;

    SELECT investor_name
    INTO v_name
    FROM INVESTOR
    WHERE investor_id = p_investor_id;

    SELECT v_name AS investor_name;

END$$

DELIMITER ;

CALL find_investor(1);
CALL find_investor(999);

