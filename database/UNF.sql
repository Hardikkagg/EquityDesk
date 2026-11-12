-- Create UNF table
CREATE TABLE normalization_unf_demo AS
SELECT
    i.investor_id,
    i.investor_name,
    i.email,
    i.phone,

    p.portfolio_id,
    p.portfolio_name,
    p.created_date,

    COALESCE(
        GROUP_CONCAT(
            CONCAT(
                s.symbol,
                ' (Qty: ', pp.quantity,
                ', Buy Price: ', pp.average_buy_price,
                ')'
            )
            ORDER BY s.symbol
            SEPARATOR ', '
        ),
        'NO HOLDINGS'
    ) AS holdings_list

FROM INVESTOR i

INNER JOIN PORTFOLIO p
    ON i.investor_id = p.investor_id

LEFT JOIN PORTFOLIO_POSITION pp
    ON p.portfolio_id = pp.portfolio_id

LEFT JOIN SECURITY s
    ON pp.security_id = s.security_id

GROUP BY
    i.investor_id,
    i.investor_name,
    i.email,
    i.phone,
    p.portfolio_id,
    p.portfolio_name,
    p.created_date;
    
-- UNF table
SELECT * FROM normalization_unf_demo;
SELECT COUNT(*) AS total_records
FROM normalization_unf_demo;


SELECT portfolio_id, portfolio_name, holdings_list
FROM normalization_unf_demo
WHERE holdings_list = 'NO HOLDINGS';