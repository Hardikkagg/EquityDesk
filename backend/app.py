import csv
import io
import json
import math
import os
from calendar import monthrange
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from flask import Flask, jsonify, request, send_from_directory
import mysql.connector
from mysql.connector import Error

from config import Config


frontend_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
app = Flask(__name__, static_folder=frontend_folder, static_url_path='')
app.config.from_object(Config)

WRITE_LOCK_NAME = 'stock_portfolio_management_write_ids'
HOLDINGS_QUERY = """
    SELECT
        pp.position_id,
        pp.portfolio_id,
        p.portfolio_name,
        i.investor_id,
        i.investor_name,
        pp.security_id,
        s.symbol,
        s.security_name,
        COALESCE(s.sector, 'Unclassified') AS sector,
        pp.quantity,
        CAST(pp.average_buy_price AS FLOAT) AS average_buy_price,
        CAST(s.current_price AS FLOAT) AS current_price,
        CAST(pp.quantity * pp.average_buy_price AS FLOAT) AS invested_value,
        CAST(pp.quantity * s.current_price AS FLOAT) AS current_value,
        CAST(pp.quantity * (s.current_price - pp.average_buy_price) AS FLOAT) AS pnl,
        CASE
            WHEN pp.quantity * pp.average_buy_price > 0
            THEN CAST(((s.current_price - pp.average_buy_price) / pp.average_buy_price) * 100 AS FLOAT)
            ELSE 0.0
        END AS pnl_percentage
    FROM PORTFOLIO_POSITION pp
    JOIN PORTFOLIO p ON pp.portfolio_id = p.portfolio_id
    JOIN INVESTOR i ON p.investor_id = i.investor_id
    JOIN SECURITY s ON pp.security_id = s.security_id
"""


def get_db_connection():
    return mysql.connector.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DB'],
        port=app.config['MYSQL_PORT'],
    )


def parse_positive_id(value, field_name):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise ValueError(f'{field_name} must be a positive integer.')
    if isinstance(value, bool) or parsed <= 0 or str(value).strip() != str(parsed):
        raise ValueError(f'{field_name} must be a positive integer.')
    return parsed


def parse_date(value, field_name):
    try:
        return datetime.strptime(str(value), '%Y-%m-%d').date()
    except (TypeError, ValueError):
        raise ValueError(f'{field_name} must be a valid date in YYYY-MM-DD format.')


def get_json_object():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None
    return data


def database_error(error, operation):
    app.logger.exception('%s failed: %s', operation, error)
    return jsonify({
        'status': 'error',
        'message': 'The database operation could not be completed. Check the server log and database connection.',
    }), 500


def close_database(cursor, connection):
    if cursor:
        cursor.close()
    if connection and connection.is_connected():
        connection.close()


def release_write_lock(cursor):
    try:
        cursor.execute('SELECT RELEASE_LOCK(%s)', (WRITE_LOCK_NAME,))
        cursor.fetchone()
    except Error as error:
        app.logger.exception('Releasing database write lock failed: %s', error)


def filtered_holdings(cursor, portfolio_id=None, investor_id=None, sector=None, search=None, sort='symbol', order='asc'):
    conditions = ['pp.quantity > 0']
    params = []
    if portfolio_id is not None:
        conditions.append('pp.portfolio_id = %s')
        params.append(portfolio_id)
    elif investor_id is not None:
        conditions.append('i.investor_id = %s')
        params.append(investor_id)
    if sector:
        conditions.append('COALESCE(s.sector, \'Unclassified\') = %s')
        params.append(sector)
    if search:
        conditions.append('(s.symbol LIKE %s OR s.security_name LIKE %s)')
        params.extend((f'%{search}%', f'%{search}%'))
    sort_columns = {
        'symbol': 's.symbol',
        'company': 's.security_name',
        'quantity': 'pp.quantity',
        'average_buy_price': 'pp.average_buy_price',
        'current_price': 's.current_price',
        'invested_value': 'pp.quantity * pp.average_buy_price',
        'current_value': 'pp.quantity * s.current_price',
        'pnl': 'pp.quantity * (s.current_price - pp.average_buy_price)',
        'sector': 's.sector',
    }
    sort_column = sort_columns.get(sort, sort_columns['symbol'])
    direction = 'DESC' if order.lower() == 'desc' else 'ASC'
    cursor.execute(
        f'{HOLDINGS_QUERY} WHERE {" AND ".join(conditions)} ORDER BY {sort_column} {direction}, s.symbol ASC',
        tuple(params),
    )
    return cursor.fetchall()


def collect_fifo_lots(cursor, portfolio_id, security_id):
    cursor.execute("""
        SELECT trade_id, trade_type, quantity, trade_price, trade_date
        FROM TRADE
        WHERE portfolio_id = %s AND security_id = %s AND (is_voided IS NULL OR is_voided = 0)
        ORDER BY trade_date ASC, trade_id ASC
    """, (portfolio_id, security_id))
    trades = cursor.fetchall()
    open_lots = []
    realized_pnl = 0.0
    for trade in trades:
        qty = int(trade['quantity'])
        trade_type = str(trade['trade_type']).upper()
        if trade_type == 'BUY':
            open_lots.append({
                'trade_id': int(trade['trade_id']),
                'quantity': qty,
                'price': float(trade['trade_price']),
            })
            continue
        remaining = qty
        while remaining > 0 and open_lots:
            lot = open_lots[0]
            consumed = min(remaining, int(lot['quantity']))
            realized_pnl += consumed * (float(trade['trade_price']) - float(lot['price']))
            lot['quantity'] -= consumed
            remaining -= consumed
            if lot['quantity'] <= 0:
                open_lots.pop(0)
    total_quantity = sum(int(lot['quantity']) for lot in open_lots)
    cost_basis = sum(float(lot['quantity']) * float(lot['price']) for lot in open_lots)
    return {
        'realized_pnl': round(realized_pnl, 2),
        'open_lots': open_lots,
        'cost_basis': round(cost_basis, 2),
        'quantity': total_quantity,
    }


def calculate_xirr(cash_flows):
    flows_by_date = {}
    for flow_date, amount in cash_flows:
        numeric_amount = float(amount)
        if isinstance(flow_date, date) and math.isfinite(numeric_amount):
            flows_by_date[flow_date] = flows_by_date.get(flow_date, 0.0) + numeric_amount
    valid_flows = [(flow_date, amount) for flow_date, amount in flows_by_date.items() if amount != 0]
    if len(valid_flows) < 2:
        return None
    if not any(amount < 0 for _, amount in valid_flows) or not any(amount > 0 for _, amount in valid_flows):
        return None

    ordered_flows = sorted(valid_flows)
    sign_changes = sum(
        (ordered_flows[index - 1][1] < 0) != (ordered_flows[index][1] < 0)
        for index in range(1, len(ordered_flows))
    )
    start_date = min(flow_date for flow_date, _ in valid_flows)
    year_fractions = [((flow_date - start_date).days / 365.0, amount) for flow_date, amount in valid_flows]
    if not any(year_fraction > 0 for year_fraction, _ in year_fractions):
        return None

    def net_present_value(log_rate):
        try:
            return sum(amount * math.exp(max(-700, min(700, -years * log_rate)))
                       for years, amount in year_fractions)
        except OverflowError:
            return math.inf

    lower = math.log1p(-0.999999)
    upper = math.log1p(1_000_000)
    steps = 2048
    previous_x = lower
    previous_value = net_present_value(previous_x)
    roots = []

    for step in range(1, steps + 1):
        current_x = lower + (upper - lower) * step / steps
        current_value = net_present_value(current_x)
        if previous_value == 0:
            roots.append(math.expm1(previous_x))
        elif current_value == 0 or (previous_value < 0) != (current_value < 0):
            left, right = previous_x, current_x
            left_value = previous_value
            for _ in range(100):
                middle = (left + right) / 2
                middle_value = net_present_value(middle)
                if middle_value == 0:
                    left = right = middle
                    break
                if (left_value < 0) != (middle_value < 0):
                    right = middle
                else:
                    left = middle
                    left_value = middle_value
            roots.append(math.expm1((left + right) / 2))
        previous_x, previous_value = current_x, current_value

    distinct_roots = []
    for root in roots:
        if math.isfinite(root) and all(abs(root - found) > 1e-6 for found in distinct_roots):
            distinct_roots.append(root)
    # Multiple cash-flow sign changes can imply multiple valid roots; omit an
    # estimate unless the dated flow pattern supports a unique solution.
    return distinct_roots[0] if sign_changes == 1 and len(distinct_roots) == 1 else None


def price_history_table_exists(cursor):
    cursor.execute(
        'SELECT COUNT(*) AS table_count FROM information_schema.tables '
        'WHERE table_schema = DATABASE() AND table_name = %s',
        ('price_history',),
    )
    return int(cursor.fetchone()['table_count']) > 0


def historical_period_start(period, today=None):
    current_day = today or date.today()
    if period == '1W':
        return current_day - timedelta(days=7)
    if period == '1M':
        year, month = current_day.year, current_day.month - 1
        if month == 0:
            year, month = year - 1, 12
        return date(year, month, min(current_day.day, monthrange(year, month)[1]))
    if period == '1Y':
        year = current_day.year - 1
        return date(year, current_day.month, min(current_day.day, monthrange(year, current_day.month)[1]))
    return None


def portfolio_historical_series(cursor, portfolio_id):
    if not price_history_table_exists(cursor):
        return []

    cursor.execute("""
        SELECT security_id, trade_type, quantity, trade_date, trade_id
        FROM TRADE
        WHERE portfolio_id = %s AND (is_voided IS NULL OR is_voided = 0)
        ORDER BY trade_date, trade_id
    """, (portfolio_id,))
    trades = cursor.fetchall()
    security_ids = sorted({int(trade['security_id']) for trade in trades})
    if not security_ids:
        return []

    placeholders = ', '.join(['%s'] * len(security_ids))
    cursor.execute(f"""
        SELECT security_id, price_date, CAST(close_price AS FLOAT) AS close_price
        FROM PRICE_HISTORY
        WHERE security_id IN ({placeholders}) AND price_date <= %s
        ORDER BY price_date, security_id
    """, tuple(security_ids) + (date.today(),))
    prices = cursor.fetchall()
    if not prices:
        return []

    price_rows = {}
    price_dates = set()
    price_indexes = {}
    for row in prices:
        security_id = int(row['security_id'])
        price_rows.setdefault(security_id, []).append(row)
        price_dates.add(row['price_date'])
        price_indexes.setdefault(security_id, 0)

    trades_by_day = {}
    for trade in trades:
        trades_by_day.setdefault(trade['trade_date'], []).append(trade)

    quantities = {}
    series = []
    trade_days = sorted(trades_by_day)
    trade_index = 0
    for price_day in sorted(price_dates):
        while trade_index < len(trade_days) and trade_days[trade_index] <= price_day:
            trade_day = trade_days[trade_index]
            for trade in trades_by_day[trade_day]:
                security_id = int(trade['security_id'])
                change = int(trade['quantity'])
                if str(trade['trade_type']).upper() == 'SELL':
                    change = -change
                quantities[security_id] = quantities.get(security_id, 0) + change
            trade_index += 1

        held = {security_id: quantity for security_id, quantity in quantities.items() if quantity > 0}
        if any(quantity < 0 for quantity in quantities.values()) or not held:
            continue

        market_value = 0.0
        complete_price_set = True
        for security_id, quantity in held.items():
            rows = price_rows.get(security_id, [])
            index = price_indexes.get(security_id, 0)
            while index < len(rows) and rows[index]['price_date'] <= price_day:
                index += 1
            price_indexes[security_id] = index
            if index == 0:
                complete_price_set = False
                break
            market_value += quantity * float(rows[index - 1]['close_price'])
        if complete_price_set:
            series.append({'date': price_day.isoformat(), 'value': round(market_value, 2)})
    return series


def write_audit_log(cursor, transaction_id, action_type, old_values, new_values, reason, performed_by='system'):
    cursor.execute(
        """
        INSERT INTO AUDIT_LOG (transaction_id, action_type, old_values, new_values, reason, performed_by)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (
            transaction_id,
            action_type,
            json.dumps(old_values, default=str),
            json.dumps(new_values, default=str),
            reason,
            performed_by,
        ),
    )


def rebuild_position_for_security(cursor, portfolio_id, security_id):
    metrics = collect_fifo_lots(cursor, portfolio_id, security_id)
    cursor.execute(
        'SELECT position_id FROM PORTFOLIO_POSITION WHERE portfolio_id = %s AND security_id = %s FOR UPDATE',
        (portfolio_id, security_id),
    )
    existing = cursor.fetchone()
    if metrics['quantity'] <= 0:
        if existing:
            cursor.execute(
                'DELETE FROM PORTFOLIO_POSITION WHERE portfolio_id = %s AND security_id = %s',
                (portfolio_id, security_id),
            )
        return metrics
    total_cost = metrics['cost_basis']
    average_price = (total_cost / metrics['quantity']) if metrics['quantity'] else 0.0
    if existing:
        cursor.execute(
            'UPDATE PORTFOLIO_POSITION SET quantity = %s, average_buy_price = %s WHERE position_id = %s',
            (metrics['quantity'], round(average_price, 2), existing['position_id']),
        )
    else:
        cursor.execute('SELECT COALESCE(MAX(position_id), 0) + 1 AS next_id FROM PORTFOLIO_POSITION')
        next_id = cursor.fetchone()['next_id']
        cursor.execute(
            'INSERT INTO PORTFOLIO_POSITION (position_id, portfolio_id, security_id, quantity, average_buy_price) VALUES (%s, %s, %s, %s, %s)',
            (next_id, portfolio_id, security_id, metrics['quantity'], round(average_price, 2)),
        )
    return metrics


def find_sell_trade_ids_consuming_buy(cursor, portfolio_id, security_id, buy_trade_id):
    cursor.execute(
        """
        SELECT trade_id, trade_type, quantity, trade_price
        FROM TRADE
        WHERE portfolio_id = %s AND security_id = %s AND (is_voided IS NULL OR is_voided = 0)
        ORDER BY trade_date ASC, trade_id ASC
        """,
        (portfolio_id, security_id),
    )
    rows = cursor.fetchall()
    open_lots = []
    consuming_sell_ids = []
    for trade in rows:
        trade_id = int(trade['trade_id'])
        if str(trade['trade_type']).upper() == 'BUY':
            open_lots.append({
                'trade_id': trade_id,
                'quantity': int(trade['quantity']),
                'price': float(trade['trade_price']),
            })
            continue
        remaining = int(trade['quantity'])
        while remaining > 0 and open_lots:
            lot = open_lots[0]
            consumed = min(remaining, int(lot['quantity']))
            if int(lot['trade_id']) == int(buy_trade_id):
                consuming_sell_ids.append(trade_id)
            lot['quantity'] -= consumed
            remaining -= consumed
            if lot['quantity'] <= 0:
                open_lots.pop(0)
    return sorted(set(consuming_sell_ids))


def holdings_summary(holdings):
    invested = sum(float(row['invested_value']) for row in holdings)
    current = sum(float(row['current_value']) for row in holdings)
    pnl = current - invested
    realized = sum(float(row.get('realized_pnl', 0)) for row in holdings)
    unrealized = sum(float(row.get('unrealized_pnl', 0)) for row in holdings)
    return {
        'total_invested': round(invested, 2),
        'current_value': round(current, 2),
        'total_pnl': round(pnl, 2),
        'total_realized_pnl': round(realized, 2),
        'total_unrealized_pnl': round(unrealized, 2),
        'pnl_percentage': round((pnl / invested * 100) if invested else 0, 2),
        'realized_pnl_percentage': round((realized / invested * 100) if invested else 0, 2),
        'holdings_count': len(holdings),
        'stocks_held': len({row['security_id'] for row in holdings}),
    }


@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'Flask backend is running.'}), 200


@app.route('/api/test-db', methods=['GET'])
def test_db():
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute('SELECT 1')
        cursor.fetchone()
        return jsonify({
            'status': 'success',
            'database': app.config['MYSQL_DB'],
            'message': 'Successfully connected to MySQL.',
        }), 200
    except Error as error:
        return database_error(error, 'Database health check')
    finally:
        close_database(cursor, connection)


@app.route('/api/investors', methods=['GET'])
def get_investors():
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        search = request.args.get('search', '').strip()
        query = """
            SELECT i.investor_id, i.investor_name
            FROM INVESTOR i
        """
        conditions = []
        params = []
        if search:
            conditions.append('(i.investor_name LIKE %s OR i.email LIKE %s OR i.phone LIKE %s)')
            params.extend((f'%{search}%', f'%{search}%', f'%{search}%'))
        if request.args.get('investor_id'):
            try:
                investor_id = parse_positive_id(request.args['investor_id'], 'Investor ID')
            except ValueError as error:
                return jsonify({'status': 'error', 'message': str(error)}), 400
            conditions.append('i.investor_id = %s')
            params.append(investor_id)
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        query += ' ORDER BY i.investor_name, i.investor_id'
        cursor.execute(query, tuple(params))
        investors = cursor.fetchall()
        return jsonify({'status': 'success', 'data': investors}), 200
    except Error as error:
        return database_error(error, 'Loading investors')
    finally:
        close_database(cursor, connection)


@app.route('/api/portfolios', methods=['GET', 'POST'])
def portfolios():
    if request.method == 'POST':
        data = get_json_object()
        if data is None:
            return jsonify({'status': 'error', 'message': 'A JSON request body is required.'}), 400
        name = str(data.get('portfolio_name', '')).strip()
        if not name or len(name) > 100:
            return jsonify({'status': 'error', 'message': 'Portfolio name is required and must be 100 characters or fewer.'}), 400
        try:
            investor_id = parse_positive_id(data.get('investor_id'), 'Investor ID')
            created_date = parse_date(data.get('created_date') or date.today().isoformat(), 'Created date')
        except ValueError as error:
            return jsonify({'status': 'error', 'message': str(error)}), 400

        connection = None
        cursor = None
        lock_acquired = False
        committed = False
        try:
            connection = get_db_connection()
            connection.autocommit = False
            cursor = connection.cursor(dictionary=True)
            cursor.execute('SELECT GET_LOCK(%s, 10) AS acquired', (WRITE_LOCK_NAME,))
            lock_acquired = cursor.fetchone()['acquired'] == 1
            if not lock_acquired:
                return jsonify({'status': 'error', 'message': 'Portfolio creation is busy. Please try again.'}), 503
            cursor.execute('SELECT investor_id FROM INVESTOR WHERE investor_id = %s', (investor_id,))
            if not cursor.fetchone():
                connection.rollback()
                return jsonify({'status': 'error', 'message': 'Selected investor was not found.'}), 404
            cursor.execute('SELECT COALESCE(MAX(portfolio_id), 0) + 1 AS next_id FROM PORTFOLIO')
            portfolio_id = cursor.fetchone()['next_id']
            cursor.execute("""
                INSERT INTO PORTFOLIO (portfolio_id, investor_id, portfolio_name, created_date)
                VALUES (%s, %s, %s, %s)
            """, (portfolio_id, investor_id, name, created_date))
            connection.commit()
            committed = True
            return jsonify({
                'status': 'success',
                'message': 'Portfolio created.',
                'data': {'portfolio_id': portfolio_id},
            }), 201
        except Error as error:
            if connection and not committed:
                connection.rollback()
            return database_error(error, 'Creating portfolio')
        finally:
            if lock_acquired and cursor:
                release_write_lock(cursor)
            close_database(cursor, connection)

    raw_investor_id = request.args.get('investor_id')
    try:
        investor_id = parse_positive_id(raw_investor_id, 'Investor ID')
    except ValueError as error:
        return jsonify({'status': 'error', 'message': str(error)}), 400
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT p.portfolio_id, p.investor_id, p.portfolio_name,
                   DATE_FORMAT(p.created_date, '%Y-%m-%d') AS created_date,
                   i.investor_name,
                   CAST(COALESCE(SUM(pp.quantity * pp.average_buy_price), 0) AS FLOAT) AS total_invested,
                   CAST(COALESCE(SUM(pp.quantity * s.current_price), 0) AS FLOAT) AS current_value
            FROM PORTFOLIO p
            JOIN INVESTOR i ON p.investor_id = i.investor_id
            LEFT JOIN PORTFOLIO_POSITION pp ON p.portfolio_id = pp.portfolio_id AND pp.quantity > 0
            LEFT JOIN SECURITY s ON pp.security_id = s.security_id
        """
        query += ' WHERE p.investor_id = %s'
        params = (investor_id,)
        query += """
            GROUP BY p.portfolio_id, p.investor_id, p.portfolio_name, p.created_date, i.investor_name
            ORDER BY p.created_date DESC, p.portfolio_id DESC
        """
        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.execute("""
            SELECT DISTINCT portfolio_id, security_id
            FROM TRADE
            WHERE COALESCE(is_voided, 0) = 0
        """)
        realized_by_portfolio = {}
        for key in cursor.fetchall():
            portfolio_id_value = int(key['portfolio_id'])
            metrics = collect_fifo_lots(cursor, portfolio_id_value, int(key['security_id']))
            realized_by_portfolio[portfolio_id_value] = (
                realized_by_portfolio.get(portfolio_id_value, 0.0) + float(metrics['realized_pnl'])
            )
        cursor.execute("""
            SELECT portfolio_id,
                   CAST(SUM(CASE WHEN trade_type = 'BUY'
                       THEN quantity * trade_price ELSE 0 END) AS FLOAT) AS gross_buy_amount
            FROM TRADE
            WHERE COALESCE(is_voided, 0) = 0
            GROUP BY portfolio_id
        """)
        gross_buys = {
            int(row['portfolio_id']): float(row['gross_buy_amount'] or 0)
            for row in cursor.fetchall()
        }
        for row in rows:
            row['realized_pnl'] = round(realized_by_portfolio.get(int(row['portfolio_id']), 0.0), 2)
            row['unrealized_pnl'] = round(float(row['current_value']) - float(row['total_invested']), 2)
            row['total_pnl'] = round(row['realized_pnl'] + row['unrealized_pnl'], 2)
            row['gross_buy_amount'] = round(gross_buys.get(int(row['portfolio_id']), 0.0), 2)
            row['return_percentage'] = round(
                row['total_pnl'] / row['gross_buy_amount'] * 100,
                2,
            ) if row['gross_buy_amount'] else None
        allocation_query = """
            SELECT p.portfolio_id, COALESCE(s.sector, 'Unclassified') AS sector,
                   COUNT(DISTINCT s.security_id) AS holding_count,
                   CAST(SUM(pp.quantity * s.current_price) AS FLOAT) AS current_value
            FROM PORTFOLIO p
            JOIN PORTFOLIO_POSITION pp ON pp.portfolio_id = p.portfolio_id AND pp.quantity > 0
            JOIN SECURITY s ON s.security_id = pp.security_id
        """
        allocation_query += ' WHERE p.investor_id = %s'
        allocation_params = (investor_id,)
        allocation_query += ' GROUP BY p.portfolio_id, s.sector ORDER BY p.portfolio_id, current_value DESC'
        cursor.execute(allocation_query, allocation_params)
        allocations = {}
        for allocation in cursor.fetchall():
            allocations.setdefault(allocation['portfolio_id'], []).append({
                'sector': allocation['sector'],
                'holding_count': int(allocation['holding_count']),
                'current_value': float(allocation['current_value']),
            })
        for row in rows:
            row['sector_allocation'] = allocations.get(row['portfolio_id'], [])
            row['holding_count'] = sum(item['holding_count'] for item in row['sector_allocation'])
        return jsonify({'status': 'success', 'data': rows}), 200
    except Error as error:
        return database_error(error, 'Loading portfolios')
    finally:
        close_database(cursor, connection)


def get_portfolio_detail_data(portfolio_id, investor_id):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.portfolio_id, p.investor_id, p.portfolio_name,
                   DATE_FORMAT(p.created_date, '%Y-%m-%d') AS created_date,
                   i.investor_name
            FROM PORTFOLIO p
            JOIN INVESTOR i ON i.investor_id = p.investor_id
            WHERE p.portfolio_id = %s AND p.investor_id = %s
        """, (portfolio_id, investor_id))
        portfolio = cursor.fetchone()
        if not portfolio:
            return jsonify({'status': 'error', 'message': 'Portfolio was not found.'}), 404

        cursor.execute("""
            SELECT t.trade_id, t.investor_id, t.portfolio_id, t.security_id,
                   t.trade_type, t.quantity, CAST(t.trade_price AS FLOAT) AS trade_price,
                   t.trade_date, COALESCE(t.is_voided, 0) AS is_voided,
                   t.void_reason, t.voided_by,
                   t.voided_at,
                   s.symbol, s.security_name, COALESCE(s.sector, 'Unclassified') AS sector,
                   CAST(s.current_price AS FLOAT) AS current_price
            FROM TRADE t
            JOIN SECURITY s ON s.security_id = t.security_id
            WHERE t.portfolio_id = %s
            ORDER BY t.trade_date DESC, t.trade_id DESC
        """, (portfolio_id,))
        transactions = cursor.fetchall()

        active_trades = [trade for trade in transactions if not int(trade['is_voided'])]
        cursor.execute("""
            SELECT pp.security_id, pp.quantity, CAST(pp.average_buy_price AS FLOAT) AS average_buy_price,
                   s.symbol, s.security_name, COALESCE(s.sector, 'Unclassified') AS sector,
                   CAST(s.current_price AS FLOAT) AS current_price
            FROM PORTFOLIO_POSITION pp
            JOIN SECURITY s ON s.security_id = pp.security_id
            WHERE pp.portfolio_id = %s AND pp.quantity > 0
        """, (portfolio_id,))
        position_rows = cursor.fetchall()
        positions_by_security = {int(row['security_id']): row for row in position_rows}
        security_ids = sorted(
            {int(trade['security_id']) for trade in transactions}
            | set(positions_by_security)
        )
        securities = {}
        for trade in transactions:
            securities[int(trade['security_id'])] = {
                'security_id': int(trade['security_id']),
                'symbol': trade['symbol'],
                'security_name': trade['security_name'],
                'sector': trade['sector'],
                'current_price': float(trade['current_price']),
            }
        for security_id, position in positions_by_security.items():
            securities[security_id] = {
                'security_id': security_id,
                'symbol': position['symbol'],
                'security_name': position['security_name'],
                'sector': position['sector'],
                'current_price': float(position['current_price']),
            }

        holdings = []
        total_realized = 0.0
        total_current = 0.0
        open_cost_basis = 0.0
        gross_buy_amount = 0.0
        cash_flows = []
        for trade in active_trades:
            amount = int(trade['quantity']) * float(trade['trade_price'])
            if str(trade['trade_type']).upper() == 'BUY':
                gross_buy_amount += amount
                cash_flows.append((trade['trade_date'], -amount))
            else:
                cash_flows.append((trade['trade_date'], amount))

        for security_id in security_ids:
            security = securities[security_id]
            metrics = collect_fifo_lots(cursor, portfolio_id, security_id)
            total_realized += float(metrics['realized_pnl'])
            position = positions_by_security.get(security_id)
            if not position:
                continue
            quantity = int(position['quantity'])
            current_price = float(security['current_price'])
            current_value = quantity * current_price
            uses_fifo_basis = int(metrics['quantity']) == quantity
            cost_basis = (
                float(metrics['cost_basis'])
                if uses_fifo_basis else quantity * float(position['average_buy_price'])
            )
            open_cost_basis += cost_basis
            total_current += current_value
            holdings.append({
                **security,
                'quantity': quantity,
                'average_buy_price': round(cost_basis / quantity, 2),
                'invested_value': round(cost_basis, 2),
                'current_value': round(current_value, 2),
                'realized_pnl': round(float(metrics['realized_pnl']), 2),
                'unrealized_pnl': round(current_value - cost_basis, 2),
                'cost_basis_source': (
                    'FIFO active trade lots'
                    if uses_fifo_basis else 'PORTFOLIO_POSITION.average_buy_price'
                ),
            })

        total_profit = total_realized + total_current - open_cost_basis
        return_denominator = gross_buy_amount or open_cost_basis
        return_percentage = (total_profit / return_denominator * 100) if return_denominator else None
        valuation_date = date.today()
        has_future_trade = any(trade['trade_date'] > valuation_date for trade in active_trades)
        if total_current > 0:
            cash_flows.append((valuation_date, total_current))
        xirr_value = None if has_future_trade else calculate_xirr(cash_flows)
        xirr_sufficient = (
            not has_future_trade
            and len({flow_date for flow_date, amount in cash_flows if amount != 0}) >= 2
            and any(amount < 0 for _, amount in cash_flows)
            and any(amount > 0 for _, amount in cash_flows)
        )

        allocations = {}
        for holding in holdings:
            sector = holding['sector']
            allocations[sector] = allocations.get(sector, 0.0) + float(holding['current_value'])
        sector_allocation = [
            {'sector': sector, 'current_value': round(value, 2)}
            for sector, value in sorted(allocations.items(), key=lambda item: item[1], reverse=True)
        ]
        for trade in transactions:
            trade['trade_date'] = trade['trade_date'].isoformat()
            trade['voided_at'] = trade['voided_at'].isoformat(sep=' ') if trade['voided_at'] else None
            trade['total_trade_amount'] = round(int(trade['quantity']) * float(trade['trade_price']), 2)

        performance_history = portfolio_historical_series(cursor, portfolio_id)
        history_available = len(performance_history) >= 2
        return jsonify({
            'status': 'success',
            'data': {
                **portfolio,
                'portfolio_value': round(total_current, 2),
                'total_invested': round(open_cost_basis, 2),
                'gross_buy_amount': round(gross_buy_amount, 2),
                'open_cost_basis': round(open_cost_basis, 2),
                'realized_pnl': round(total_realized, 2),
                'unrealized_pnl': round(total_current - open_cost_basis, 2),
                'total_pnl': round(total_profit, 2),
                'return_percentage': round(return_percentage, 2) if return_percentage is not None else None,
                'price_source': 'SECURITY.current_price',
                'xirr_percentage': round(xirr_value * 100, 4) if xirr_value is not None else None,
                'xirr_available': xirr_value is not None,
                'xirr_message': (
                    'XIRR includes active dated BUY/SELL cash flows and current remaining holdings valued at SECURITY.current_price.'
                    if xirr_value is not None else
                    'XIRR could not produce a unique valid rate for these cash flows.'
                    if xirr_sufficient else
                    'XIRR requires at least two dated cash flows with both an inflow and an outflow, and no future-dated trades.'
                ),
                'holdings': holdings,
                'sector_allocation': sector_allocation,
                'transactions': transactions,
                'historical_performance': performance_history,
                'historical_performance_available': history_available,
                'historical_performance_message': (
                    None if history_available else
                    'A historical portfolio chart requires at least two comparable valuations from PRICE_HISTORY.'
                ),
            },
        }), 200
    except Error as error:
        return database_error(error, 'Loading portfolio details')
    finally:
        close_database(cursor, connection)


@app.route('/api/portfolios/<int:portfolio_id>', methods=['GET', 'PUT', 'DELETE'])
def portfolio_detail(portfolio_id):
    data = get_json_object() if request.method in ('PUT', 'DELETE') else {}
    if request.method in ('PUT', 'DELETE') and data is None:
        return jsonify({'status': 'error', 'message': 'A JSON request body with investor_id is required.'}), 400
    try:
        investor_id = parse_positive_id(
            request.args.get('investor_id') if request.method == 'GET' else data.get('investor_id'),
            'Investor ID',
        )
    except ValueError as error:
        return jsonify({'status': 'error', 'message': str(error)}), 400
    if request.method == 'GET':
        return get_portfolio_detail_data(portfolio_id, investor_id)
    connection = None
    cursor = None
    committed = False
    try:
        connection = get_db_connection()
        connection.autocommit = False
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            'SELECT portfolio_id FROM PORTFOLIO WHERE portfolio_id = %s AND investor_id = %s FOR UPDATE',
            (portfolio_id, investor_id),
        )
        if not cursor.fetchone():
            return jsonify({'status': 'error', 'message': 'Portfolio was not found.'}), 404

        if request.method == 'PUT':
            name = str(data.get('portfolio_name', '')).strip()
            if not name or len(name) > 100:
                return jsonify({'status': 'error', 'message': 'Portfolio name is required and must be 100 characters or fewer.'}), 400
            cursor.execute('UPDATE PORTFOLIO SET portfolio_name = %s WHERE portfolio_id = %s', (name, portfolio_id))
            connection.commit()
            committed = True
            return jsonify({'status': 'success', 'message': 'Portfolio updated.'}), 200

        cursor.execute('SELECT COUNT(*) AS trade_count FROM TRADE WHERE portfolio_id = %s', (portfolio_id,))
        if cursor.fetchone()['trade_count']:
            connection.rollback()
            return jsonify({
                'status': 'error',
                'message': 'This portfolio has transaction history and cannot be deleted without removing that history.',
            }), 409
        cursor.execute('DELETE FROM PORTFOLIO_POSITION WHERE portfolio_id = %s', (portfolio_id,))
        cursor.execute('DELETE FROM PORTFOLIO WHERE portfolio_id = %s', (portfolio_id,))
        connection.commit()
        committed = True
        return jsonify({'status': 'success', 'message': 'Portfolio deleted.'}), 200
    except Error as error:
        if connection and not committed:
            connection.rollback()
        return database_error(error, 'Updating portfolio')
    finally:
        close_database(cursor, connection)


@app.route('/api/securities', methods=['GET'])
def get_securities():
    search = request.args.get('search', '').strip()
    sector = request.args.get('sector', '').strip()
    try:
        min_price = float(request.args['min_price']) if request.args.get('min_price') else None
        max_price = float(request.args['max_price']) if request.args.get('max_price') else None
        if any(value is not None and (not math.isfinite(value) or value < 0) for value in (min_price, max_price)):
            raise ValueError('Price filters must be non-negative numbers.')
        if min_price is not None and max_price is not None and min_price > max_price:
            raise ValueError('Minimum price cannot exceed maximum price.')
    except ValueError as error:
        return jsonify({'status': 'error', 'message': str(error)}), 400
    conditions = []
    params = []
    if search:
        conditions.append('(symbol LIKE %s OR security_name LIKE %s)')
        params.extend((f'%{search}%', f'%{search}%'))
    if sector:
        conditions.append("COALESCE(sector, 'Unclassified') = %s")
        params.append(sector)
    if min_price is not None:
        conditions.append('current_price >= %s')
        params.append(min_price)
    if max_price is not None:
        conditions.append('current_price <= %s')
        params.append(max_price)
    sort_columns = {
        'symbol': 'symbol',
        'price': 'current_price',
        'company': 'security_name',
        'sector': 'sector',
    }
    sort = request.args.get('sort', 'symbol')
    if sort not in sort_columns:
        return jsonify({'status': 'error', 'message': 'Unsupported security sort option.'}), 400
    order = 'DESC' if request.args.get('order', 'asc').lower() == 'desc' else 'ASC'
    query = """
        SELECT security_id, symbol, security_name, COALESCE(sector, 'Unclassified') AS sector,
               CAST(current_price AS FLOAT) AS current_price
        FROM SECURITY
    """
    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)
    query += f' ORDER BY {sort_columns[sort]} {order}, symbol'
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, tuple(params))
        return jsonify({'status': 'success', 'data': cursor.fetchall()}), 200
    except Error as error:
        return database_error(error, 'Loading securities')
    finally:
        close_database(cursor, connection)


@app.route('/api/market', methods=['GET'])
def get_market_overview():
    search = request.args.get('search', '').strip()
    sector = request.args.get('sector', '').strip()
    try:
        min_price = float(request.args['min_price']) if request.args.get('min_price') else None
        max_price = float(request.args['max_price']) if request.args.get('max_price') else None
        if any(value is not None and (not math.isfinite(value) or value < 0) for value in (min_price, max_price)):
            raise ValueError('Price filters must be non-negative numbers.')
        if min_price is not None and max_price is not None and min_price > max_price:
            raise ValueError('Minimum price cannot exceed maximum price.')
    except ValueError as error:
        return jsonify({'status': 'error', 'message': str(error)}), 400

    sort_columns = {'symbol': 's.symbol', 'price': 's.current_price', 'company': 's.security_name', 'sector': 's.sector'}
    sort = request.args.get('sort', 'symbol')
    if sort not in sort_columns:
        return jsonify({'status': 'error', 'message': 'Unsupported security sort option.'}), 400
    direction = 'DESC' if request.args.get('order', 'asc').lower() == 'desc' else 'ASC'
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT s.security_id, s.symbol, s.security_name, COALESCE(s.sector, 'Unclassified') AS sector,
                   CAST(s.current_price AS FLOAT) AS current_price
            FROM SECURITY s
        """
        conditions = []
        params = []
        if search:
            conditions.append('(s.symbol LIKE %s OR s.security_name LIKE %s)')
            params.extend((f'%{search}%', f'%{search}%'))
        if sector:
            conditions.append("COALESCE(s.sector, 'Unclassified') = %s")
            params.append(sector)
        if min_price is not None:
            conditions.append('s.current_price >= %s')
            params.append(min_price)
        if max_price is not None:
            conditions.append('s.current_price <= %s')
            params.append(max_price)
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        query += f' ORDER BY {sort_columns[sort]} {direction}, s.symbol'
        cursor.execute(query, tuple(params))
        securities = cursor.fetchall()

        return jsonify({
            'status': 'success',
            'price_source': 'SECURITY.current_price',
            'is_live': False,
            'indices': [
                {'name': name, 'symbol': symbol, 'available': False, 'current_value': None, 'previous_close': None, 'change_percentage': None}
                for name, symbol in (
                    ('NIFTY 50', 'NIFTY 50'),
                    ('SENSEX', 'SENSEX'),
                    ('BANK NIFTY', 'BANK NIFTY'),
                )
            ],
            'securities': securities,
            'most_bought': [],
            'most_held': [],
            'strongest_held_returns': [],
            'weakest_held_returns': [],
            'sector_performance': [],
            'market_sections_available': {
                'indices': False,
                'gainers': False,
                'losers': False,
                'traded_volume': False,
                'mtf': False,
                'intraday_volume': False,
                'volume_shockers': False,
                'sector_performance': False,
                'etfs': False,
                'us_stocks': False,
                'news': False,
            },
            'ipos_available': False,
            'news_available': False,
        }), 200
    except Error as error:
        return database_error(error, 'Loading market overview')
    finally:
        close_database(cursor, connection)


@app.route('/api/securities/<int:security_id>', methods=['GET'])
def security_detail(security_id):
    period = request.args.get('period', '1M').upper().strip()
    if period not in ('1W', '1M', '1Y', 'ALL'):
        return jsonify({'status': 'error', 'message': 'Period must be 1W, 1M, 1Y, or ALL.'}), 400
    try:
        investor_id = (
            parse_positive_id(request.args.get('investor_id'), 'Investor ID')
            if request.args.get('investor_id') else None
        )
    except ValueError as error:
        return jsonify({'status': 'error', 'message': str(error)}), 400

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT security_id, symbol, security_name, COALESCE(sector, 'Unclassified') AS sector,
                   CAST(current_price AS FLOAT) AS current_price
            FROM SECURITY WHERE security_id = %s
        """, (security_id,))
        security = cursor.fetchone()
        if not security:
            return jsonify({'status': 'error', 'message': 'Security was not found.'}), 404
        security.update({'portfolio_count': 0, 'shares_held': 0, 'holdings': []})
        if investor_id is not None:
            cursor.execute("""
                SELECT COUNT(DISTINCT pp.portfolio_id) AS portfolio_count,
                       CAST(COALESCE(SUM(pp.quantity), 0) AS UNSIGNED) AS shares_held
                FROM PORTFOLIO_POSITION pp
                JOIN PORTFOLIO p ON p.portfolio_id = pp.portfolio_id
                WHERE pp.security_id = %s AND pp.quantity > 0 AND p.investor_id = %s
            """, (security_id, investor_id))
            security.update(cursor.fetchone())
            cursor.execute("""
                SELECT p.portfolio_id, p.portfolio_name, i.investor_id, i.investor_name,
                       pp.quantity, CAST(pp.average_buy_price AS FLOAT) AS average_buy_price,
                       CAST(pp.quantity * s.current_price AS FLOAT) AS current_value
                FROM PORTFOLIO_POSITION pp
                JOIN PORTFOLIO p ON p.portfolio_id = pp.portfolio_id
                JOIN INVESTOR i ON i.investor_id = p.investor_id
                JOIN SECURITY s ON s.security_id = pp.security_id
                WHERE pp.security_id = %s AND pp.quantity > 0 AND p.investor_id = %s
                ORDER BY p.portfolio_name
            """, (security_id, investor_id))
            security['holdings'] = cursor.fetchall()
        history_available = price_history_table_exists(cursor)
        history = []
        if history_available:
            query = """
                SELECT DATE_FORMAT(price_date, '%Y-%m-%d') AS price_date,
                       CAST(close_price AS FLOAT) AS close_price
                FROM PRICE_HISTORY
                WHERE security_id = %s AND price_date <= %s
            """
            params = [security_id, date.today()]
            start_date = historical_period_start(period)
            if start_date:
                query += ' AND price_date >= %s'
                params.append(start_date)
            query += ' ORDER BY price_date ASC'
            cursor.execute(query, tuple(params))
            history = cursor.fetchall()

        if investor_id is not None:
            cursor.execute("""
            SELECT t.trade_id, t.investor_id, i.investor_name, t.portfolio_id, p.portfolio_name,
                   t.trade_type, t.quantity, CAST(t.trade_price AS FLOAT) AS trade_price,
                   CAST(t.quantity * t.trade_price AS FLOAT) AS total_trade_amount,
                   DATE_FORMAT(t.trade_date, '%Y-%m-%d') AS trade_date,
                   COALESCE(t.is_voided, 0) AS is_voided, t.void_reason,
                   t.voided_by, t.voided_at
            FROM TRADE t
            JOIN INVESTOR i ON i.investor_id = t.investor_id
            JOIN PORTFOLIO p ON p.portfolio_id = t.portfolio_id
            WHERE t.security_id = %s AND t.investor_id = %s
            ORDER BY t.trade_date DESC, t.trade_id DESC
            """, (security_id, investor_id))
            transactions = cursor.fetchall()
            for transaction in transactions:
                transaction['voided_at'] = (
                    transaction['voided_at'].isoformat(sep=' ')
                    if transaction['voided_at'] else None
                )
        else:
            transactions = []
        security['price_source'] = 'SECURITY.current_price'
        security['historical_price_source'] = 'PRICE_HISTORY imported closing prices'
        security['history_table_available'] = history_available
        security['history_available'] = bool(history)
        security['history_period'] = period
        security['historical_prices'] = history
        security['history_message'] = (
            'No historical prices have been imported for this security and period.'
            if not history else None
        )
        security['transactions'] = transactions
        security['investor_scope_available'] = investor_id is not None
        return jsonify({'status': 'success', 'data': security}), 200
    except Error as error:
        return database_error(error, 'Loading security details')
    finally:
        close_database(cursor, connection)


@app.route('/api/price-history/import', methods=['POST'])
def import_price_history():
    if request.content_length and request.content_length > 5 * 1024 * 1024:
        return jsonify({'status': 'error', 'message': 'CSV uploads must be 5 MB or smaller.'}), 413
    upload = request.files.get('file')
    if upload is None or not upload.filename:
        return jsonify({'status': 'error', 'message': 'Upload a CSV file using the file field.'}), 400
    if not upload.filename.lower().endswith('.csv'):
        return jsonify({'status': 'error', 'message': 'The uploaded file must have a .csv extension.'}), 400
    try:
        content = upload.stream.read(5 * 1024 * 1024 + 1)
        if len(content) > 5 * 1024 * 1024:
            return jsonify({'status': 'error', 'message': 'CSV uploads must be 5 MB or smaller.'}), 413
        text = content.decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(text))
        required_headers = {'security_id', 'price_date', 'close_price'}
        normalized_headers = [str(header or '').strip().lower() for header in (reader.fieldnames or [])]
        if not required_headers.issubset(set(normalized_headers)) or len(normalized_headers) != len(set(normalized_headers)):
            return jsonify({
                'status': 'error',
                'message': 'CSV headers must include unique security_id, price_date, and close_price columns.',
            }), 400

        rows = []
        for line_number, row in enumerate(reader, start=2):
            if len(rows) >= 10000:
                return jsonify({'status': 'error', 'message': 'CSV files may contain at most 10,000 data rows.'}), 400
            if None in row or any(value is None for value in row.values()):
                return jsonify({'status': 'error', 'message': f'CSV row {line_number} has a different number of fields than the header.'}), 400
            try:
                normalized = {str(key or '').strip().lower(): value for key, value in row.items()}
                security_id = parse_positive_id(normalized.get('security_id'), f'Security ID on row {line_number}')
                price_date = parse_date(normalized.get('price_date'), f'Price date on row {line_number}')
                close_price = Decimal(str(normalized.get('close_price', '')).strip())
            except (ValueError, InvalidOperation) as error:
                return jsonify({'status': 'error', 'message': str(error)}), 400
            if not close_price.is_finite() or close_price <= 0 or close_price > Decimal('9999999999.99'):
                return jsonify({'status': 'error', 'message': f'Close price on row {line_number} must be greater than zero and fit DECIMAL(12,2).'}), 400
            if close_price != close_price.quantize(Decimal('0.01')):
                return jsonify({'status': 'error', 'message': f'Close price on row {line_number} may have at most two decimal places.'}), 400
            rows.append((security_id, price_date, close_price))
        if not rows:
            return jsonify({'status': 'error', 'message': 'The CSV contains no historical price rows.'}), 400
    except UnicodeDecodeError:
        return jsonify({'status': 'error', 'message': 'The CSV must use UTF-8 encoding.'}), 400
    except csv.Error as error:
        return jsonify({'status': 'error', 'message': f'Invalid CSV data: {error}'}), 400

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        connection.autocommit = False
        cursor = connection.cursor(dictionary=True)
        if not price_history_table_exists(cursor):
            return jsonify({
                'status': 'error',
                'message': 'PRICE_HISTORY is not installed. Apply database/07_price_history.sql first.',
            }), 503

        security_ids = sorted({row[0] for row in rows})
        placeholders = ', '.join(['%s'] * len(security_ids))
        cursor.execute(
            f'SELECT security_id FROM SECURITY WHERE security_id IN ({placeholders})',
            tuple(security_ids),
        )
        known_security_ids = {int(row['security_id']) for row in cursor.fetchall()}
        unknown_ids = sorted(set(security_ids) - known_security_ids)
        if unknown_ids:
            connection.rollback()
            return jsonify({
                'status': 'error',
                'message': f'Unknown security_id value(s): {", ".join(map(str, unknown_ids))}.',
            }), 400

        cursor.executemany("""
            INSERT IGNORE INTO PRICE_HISTORY (security_id, price_date, close_price)
            VALUES (%s, %s, %s)
        """, rows)
        inserted = cursor.rowcount
        connection.commit()
        return jsonify({
            'status': 'success',
            'message': 'Historical prices imported without changing SECURITY.current_price.',
            'data': {
                'rows_received': len(rows),
                'rows_inserted': inserted,
                'rows_skipped_as_duplicates': len(rows) - inserted,
                'price_source': 'PRICE_HISTORY imported CSV',
                'current_price_modified': False,
            },
        }), 201
    except Error as error:
        if connection:
            connection.rollback()
        return database_error(error, 'Importing historical prices')
    finally:
        close_database(cursor, connection)


@app.route('/api/holdings', methods=['GET'])
def get_holdings():
    try:
        portfolio_id = parse_positive_id(request.args['portfolio_id'], 'Portfolio ID') if request.args.get('portfolio_id') else None
        investor_id = parse_positive_id(request.args.get('investor_id'), 'Investor ID')
    except ValueError as error:
        return jsonify({'status': 'error', 'message': str(error)}), 400
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        if portfolio_id:
            cursor.execute(
                'SELECT portfolio_id FROM PORTFOLIO WHERE portfolio_id = %s AND investor_id = %s',
                (portfolio_id, investor_id),
            )
            if not cursor.fetchone():
                return jsonify({'status': 'error', 'message': 'Portfolio was not found for the selected investor.'}), 404
        holdings = filtered_holdings(
            cursor,
            portfolio_id=portfolio_id,
            investor_id=investor_id,
            sector=request.args.get('sector', '').strip() or None,
            search=request.args.get('search', '').strip() or None,
            sort=request.args.get('sort', 'symbol'),
            order=request.args.get('order', 'asc'),
        )
        for row in holdings:
            metrics = collect_fifo_lots(cursor, int(row['portfolio_id']), int(row['security_id']))
            row['realized_pnl'] = float(metrics['realized_pnl'])
            fifo_quantity = int(metrics['quantity'])
            position_quantity = int(row['quantity'])
            cost_basis = (
                float(metrics['cost_basis'])
                if fifo_quantity == position_quantity
                else float(row['invested_value'])
            )
            row['cost_basis'] = cost_basis
            row['invested_value'] = round(cost_basis, 2)
            row['average_buy_price'] = round(cost_basis / position_quantity, 2) if position_quantity else 0.0
            row['unrealized_pnl'] = float(row['current_value']) - cost_basis
            row['pnl'] = row['unrealized_pnl']
            row['pnl_percentage'] = (
                row['unrealized_pnl'] / cost_basis * 100 if cost_basis else 0.0
            )
        return jsonify({
            'status': 'success',
            'summary': holdings_summary(holdings),
            'data': holdings,
        }), 200
    except Error as error:
        return database_error(error, 'Loading holdings')
    finally:
        close_database(cursor, connection)


@app.route('/api/trades', methods=['GET'])
def get_trades():
    try:
        portfolio_id = parse_positive_id(request.args['portfolio_id'], 'Portfolio ID') if request.args.get('portfolio_id') else None
        investor_id = parse_positive_id(request.args.get('investor_id'), 'Investor ID')
        try:
            limit = int(request.args.get('limit', 50))
        except ValueError:
            raise ValueError('Limit must be an integer between 1 and 1000.')
        if limit < 1 or limit > 1000:
            raise ValueError('Limit must be between 1 and 1000.')
        trade_type = request.args.get('trade_type', '').upper().strip()
        if trade_type and trade_type not in ('BUY', 'SELL'):
            raise ValueError('Transaction type must be BUY or SELL.')
        security_id = parse_positive_id(request.args['security_id'], 'Security ID') if request.args.get('security_id') else None
        from_date = parse_date(request.args['from_date'], 'Start date') if request.args.get('from_date') else None
        to_date = parse_date(request.args['to_date'], 'End date') if request.args.get('to_date') else None
        if from_date and to_date and from_date > to_date:
            raise ValueError('Start date must not be after end date.')
    except ValueError as error:
        return jsonify({'status': 'error', 'message': str(error)}), 400

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        if portfolio_id:
            cursor.execute(
                'SELECT portfolio_id FROM PORTFOLIO WHERE portfolio_id = %s AND investor_id = %s',
                (portfolio_id, investor_id),
            )
            if not cursor.fetchone():
                return jsonify({'status': 'error', 'message': 'Portfolio was not found for the selected investor.'}), 404
        query = """
            SELECT t.trade_id, t.investor_id, i.investor_name, t.portfolio_id, p.portfolio_name,
                   t.security_id, s.symbol, s.security_name, t.trade_type, t.quantity,
                   CAST(t.trade_price AS FLOAT) AS trade_price,
                   CAST(t.quantity * t.trade_price AS FLOAT) AS total_trade_amount,
                   DATE_FORMAT(t.trade_date, '%Y-%m-%d') AS trade_date,
                   COALESCE(t.is_voided, 0) AS is_voided,
                   t.void_reason,
                   t.voided_by,
                   t.voided_at
            FROM TRADE t
            JOIN INVESTOR i ON t.investor_id = i.investor_id
            JOIN PORTFOLIO p ON t.portfolio_id = p.portfolio_id
            JOIN SECURITY s ON t.security_id = s.security_id
        """
        conditions = ['t.investor_id = %s']
        params = [investor_id]
        for condition, value in (
            ('t.portfolio_id =', portfolio_id),
            ('t.trade_type =', trade_type or None),
            ('t.security_id =', security_id),
            ('t.trade_date >=', from_date),
            ('t.trade_date <=', to_date),
        ):
            if value is not None:
                conditions.append(f'{condition} %s')
                params.append(value)
        search = request.args.get('search', '').strip()
        if search:
            conditions.append('(s.symbol LIKE %s OR s.security_name LIKE %s)')
            params.extend((f'%{search}%', f'%{search}%'))
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        query += ' ORDER BY t.trade_date DESC, t.trade_id DESC LIMIT %s'
        params.append(limit)
        cursor.execute(query, tuple(params))
        trades = cursor.fetchall()
        for trade in trades:
            trade['voided_at'] = trade['voided_at'].isoformat(sep=' ') if trade['voided_at'] else None
        return jsonify({'status': 'success', 'data': trades}), 200
    except Error as error:
        return database_error(error, 'Loading transactions')
    finally:
        close_database(cursor, connection)


@app.route('/api/trade', methods=['POST'])
def execute_trade():
    data = get_json_object()
    if data is None:
        return jsonify({'status': 'error', 'message': 'A JSON request body is required.'}), 400
    try:
        investor_id = parse_positive_id(data.get('investor_id'), 'Investor ID')
        portfolio_id = parse_positive_id(data.get('portfolio_id'), 'Portfolio ID')
        security_id = parse_positive_id(data.get('security_id'), 'Security ID')
        quantity = parse_positive_id(data.get('quantity'), 'Quantity')
        trade_type = str(data.get('trade_type', '')).upper().strip()
        if trade_type not in ('BUY', 'SELL'):
            raise ValueError('Transaction type must be BUY or SELL.')
        trade_price = float(data.get('trade_price'))
        if not math.isfinite(trade_price) or trade_price <= 0:
            raise ValueError('Transaction price must be greater than zero.')
        trade_date = parse_date(data.get('trade_date'), 'Transaction date')
        performed_by = str(data.get('performed_by', 'system')).strip() or 'system'
    except (ValueError, TypeError) as error:
        return jsonify({'status': 'error', 'message': str(error)}), 400

    connection = None
    cursor = None
    lock_acquired = False
    committed = False
    try:
        connection = get_db_connection()
        connection.autocommit = False
        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT GET_LOCK(%s, 10) AS acquired', (WRITE_LOCK_NAME,))
        lock_acquired = cursor.fetchone()['acquired'] == 1
        if not lock_acquired:
            return jsonify({'status': 'error', 'message': 'Another transaction is being processed. Please try again.'}), 503

        cursor.execute('SELECT investor_id FROM INVESTOR WHERE investor_id = %s', (investor_id,))
        if not cursor.fetchone():
            return jsonify({'status': 'error', 'message': 'Selected investor was not found.'}), 404
        cursor.execute('SELECT investor_id FROM PORTFOLIO WHERE portfolio_id = %s FOR UPDATE', (portfolio_id,))
        portfolio = cursor.fetchone()
        if not portfolio:
            return jsonify({'status': 'error', 'message': 'Selected portfolio was not found.'}), 404
        if portfolio['investor_id'] != investor_id:
            return jsonify({'status': 'error', 'message': 'The selected portfolio does not belong to this investor.'}), 400
        cursor.execute('SELECT symbol FROM SECURITY WHERE security_id = %s', (security_id,))
        security = cursor.fetchone()
        if not security:
            return jsonify({'status': 'error', 'message': 'Selected security was not found.'}), 404

        current_fifo = collect_fifo_lots(cursor, portfolio_id, security_id)
        if trade_type == 'SELL' and current_fifo['quantity'] < quantity:
            return jsonify({
                'status': 'error',
                'message': f'Insufficient quantity to sell. Available: {current_fifo["quantity"]}; requested: {quantity}.',
            }), 400

        cursor.execute('SELECT COALESCE(MAX(trade_id), 0) + 1 AS next_id FROM TRADE')
        trade_id = cursor.fetchone()['next_id']
        trade_payload = {
            'trade_id': trade_id,
            'investor_id': investor_id,
            'security_id': security_id,
            'portfolio_id': portfolio_id,
            'trade_type': trade_type,
            'quantity': quantity,
            'trade_price': trade_price,
            'trade_date': trade_date.isoformat(),
            'is_voided': 0,
            'void_reason': None,
            'voided_by': None,
            'voided_at': None,
        }
        cursor.execute(
            """
            INSERT INTO TRADE
                (trade_id, investor_id, security_id, portfolio_id, trade_type, quantity, trade_price, trade_date, is_voided, void_reason, voided_by, voided_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0, NULL, NULL, NULL)
            """,
            (trade_id, investor_id, security_id, portfolio_id, trade_type, quantity, trade_price, trade_date),
        )

        if trade_type == 'BUY':
            rebuild_position_for_security(cursor, portfolio_id, security_id)
        else:
            rebuild_position_for_security(cursor, portfolio_id, security_id)

        write_audit_log(
            cursor,
            trade_id,
            'TRADE_CREATED',
            {},
            trade_payload,
            'Trade recorded via EquityDesk order entry.',
            performed_by,
        )

        connection.commit()
        committed = True
        return jsonify({
            'status': 'success',
            'message': f'{trade_type} order recorded: {quantity} {security["symbol"]} at {trade_price:,.2f}.',
            'data': {'trade_id': trade_id},
        }), 201
    except Error as error:
        if connection and not committed:
            connection.rollback()
        return database_error(error, 'Recording transaction')
    finally:
        if lock_acquired and cursor:
            release_write_lock(cursor)
        close_database(cursor, connection)


@app.route('/api/trades/<int:trade_id>/void', methods=['POST'])
def void_trade(trade_id):
    data = get_json_object()
    if data is None:
        return jsonify({'status': 'error', 'message': 'A JSON request body with investor_id is required.'}), 400
    try:
        investor_id = parse_positive_id(data.get('investor_id'), 'Investor ID')
    except ValueError as error:
        return jsonify({'status': 'error', 'message': str(error)}), 400
    reason = str(data.get('reason', '')).strip()
    performed_by = str(data.get('performed_by', 'system')).strip() or 'system'
    if not reason:
        return jsonify({'status': 'error', 'message': 'A void reason is required.'}), 400

    connection = None
    cursor = None
    committed = False
    try:
        connection = get_db_connection()
        connection.autocommit = False
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            'SELECT * FROM TRADE WHERE trade_id = %s AND investor_id = %s FOR UPDATE',
            (trade_id, investor_id),
        )
        trade = cursor.fetchone()
        if not trade:
            return jsonify({'status': 'error', 'message': 'Transaction was not found.'}), 404
        if trade.get('is_voided') == 1:
            return jsonify({'status': 'error', 'message': 'This transaction has already been voided.'}), 409

        affected_trade_ids = [int(trade['trade_id'])]
        if str(trade['trade_type']).upper() == 'BUY':
            dependent_sell_ids = find_sell_trade_ids_consuming_buy(
                cursor,
                int(trade['portfolio_id']),
                int(trade['security_id']),
                int(trade['trade_id']),
            )
            if dependent_sell_ids:
                return jsonify({
                    'status': 'error',
                    'message': 'This BUY trade has dependent SELL transactions. Void the SELL entries first or correct the trade sequence before voiding this lot.',
                }), 409
            affected_trade_ids = [int(trade['trade_id'])]

        for affected_id in sorted(set(affected_trade_ids)):
            cursor.execute('SELECT * FROM TRADE WHERE trade_id = %s FOR UPDATE', (affected_id,))
            affected = cursor.fetchone()
            if not affected:
                continue
            old_values = {
                'trade_id': int(affected['trade_id']),
                'trade_type': affected['trade_type'],
                'quantity': int(affected['quantity']),
                'trade_price': float(affected['trade_price']),
                'portfolio_id': int(affected['portfolio_id']),
                'security_id': int(affected['security_id']),
                'is_voided': int(affected.get('is_voided') or 0),
                'void_reason': affected.get('void_reason'),
            }
            cursor.execute(
                'UPDATE TRADE SET is_voided = 1, void_reason = %s, voided_by = %s, voided_at = NOW() WHERE trade_id = %s',
                (reason, performed_by, affected_id),
            )
            write_audit_log(
                cursor,
                affected_id,
                'TRADE_VOIDED',
                old_values,
                {
                    'trade_id': affected_id,
                    'is_voided': 1,
                    'void_reason': reason,
                    'voided_by': performed_by,
                    'voided_at': datetime.utcnow().isoformat(),
                },
                reason,
                performed_by,
            )

        rebuild_position_for_security(cursor, int(trade['portfolio_id']), int(trade['security_id']))
        connection.commit()
        committed = True
        return jsonify({
            'status': 'success',
            'message': 'Transaction voided successfully.',
            'data': {
                'trade_id': trade_id,
                'affected_trade_ids': sorted(set(affected_trade_ids)),
                'void_reason': reason,
            },
        }), 200
    except Error as error:
        if connection and not committed:
            connection.rollback()
        return database_error(error, 'Voiding transaction')
    finally:
        close_database(cursor, connection)


def watchlist_investor_id():
    raw_id = request.args.get('investor_id') if request.method == 'GET' else (get_json_object() or {}).get('investor_id')
    return parse_positive_id(raw_id, 'Investor ID')


@app.route('/api/watchlist', methods=['GET', 'POST', 'PUT', 'DELETE'])
def investor_watchlist():
    data = get_json_object() if request.method in ('POST', 'PUT', 'DELETE') else {}
    if request.method in ('POST', 'PUT', 'DELETE') and data is None:
        return jsonify({'status': 'error', 'message': 'A JSON request body is required.'}), 400
    try:
        investor_id = watchlist_investor_id()
        security_id = parse_positive_id(data.get('security_id'), 'Security ID') if request.method != 'GET' else None
        raw_target = data.get('target_price') if data else None
        target_price = None
        if raw_target not in (None, ''):
            target_price = float(raw_target)
            if not math.isfinite(target_price) or target_price <= 0:
                raise ValueError('Target price must be greater than zero.')
    except (ValueError, TypeError) as error:
        return jsonify({'status': 'error', 'message': str(error)}), 400

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        if request.method == 'GET':
            cursor.execute("""
                SELECT w.investor_id, w.security_id, s.symbol, s.security_name,
                       COALESCE(s.sector, 'Unclassified') AS sector,
                       CAST(s.current_price AS FLOAT) AS current_price,
                       CAST(w.target_price AS FLOAT) AS target_price,
                       w.created_at,
                       CASE WHEN w.target_price IS NOT NULL AND s.current_price >= w.target_price
                           THEN 1 ELSE 0 END AS target_reached
                FROM WATCHLIST w
                JOIN SECURITY s ON s.security_id = w.security_id
                WHERE w.investor_id = %s
                ORDER BY s.symbol
            """, (investor_id,))
            return jsonify({'status': 'success', 'investor_id': investor_id, 'data': cursor.fetchall()}), 200
        cursor.execute('SELECT investor_id FROM INVESTOR WHERE investor_id = %s', (investor_id,))
        if not cursor.fetchone():
            return jsonify({'status': 'error', 'message': 'Investor was not found.'}), 404
        cursor.execute('SELECT security_id FROM SECURITY WHERE security_id = %s', (security_id,))
        if not cursor.fetchone():
            return jsonify({'status': 'error', 'message': 'Security was not found.'}), 404

        if request.method == 'POST':
            cursor.execute("""
                INSERT INTO WATCHLIST (investor_id, security_id, target_price)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE target_price = COALESCE(VALUES(target_price), target_price)
            """, (investor_id, security_id, target_price))
            message = 'Security added to the investor watchlist.'
            status_code = 201
        elif request.method == 'PUT':
            cursor.execute("""
                UPDATE WATCHLIST SET target_price = %s
                WHERE investor_id = %s AND security_id = %s
            """, (target_price, investor_id, security_id))
            if cursor.rowcount == 0:
                cursor.execute("""
                    SELECT investor_id FROM WATCHLIST
                    WHERE investor_id = %s AND security_id = %s
                """, (investor_id, security_id))
                if not cursor.fetchone():
                    return jsonify({'status': 'error', 'message': 'Security is not on this investor’s watchlist.'}), 404
            message = 'Price target updated.'
            status_code = 200
        else:
            cursor.execute("""
                DELETE FROM WATCHLIST
                WHERE investor_id = %s AND security_id = %s
            """, (investor_id, security_id))
            if cursor.rowcount == 0:
                return jsonify({'status': 'error', 'message': 'Security is not on this investor’s watchlist.'}), 404
            message = 'Security removed from the investor watchlist.'
            status_code = 200
        connection.commit()
        return jsonify({'status': 'success', 'message': message}), status_code
    except Error as error:
        if connection:
            connection.rollback()
        return database_error(error, 'Updating investor watchlist')
    finally:
        close_database(cursor, connection)


@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    try:
        portfolio_id = parse_positive_id(request.args['portfolio_id'], 'Portfolio ID') if request.args.get('portfolio_id') else None
        investor_id = parse_positive_id(request.args.get('investor_id'), 'Investor ID')
    except ValueError as error:
        return jsonify({'status': 'error', 'message': str(error)}), 400

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        if portfolio_id:
            cursor.execute(
                'SELECT portfolio_id FROM PORTFOLIO WHERE portfolio_id = %s AND investor_id = %s',
                (portfolio_id, investor_id),
            )
            if not cursor.fetchone():
                return jsonify({'status': 'error', 'message': 'Portfolio was not found for the selected investor.'}), 404
        holdings = filtered_holdings(cursor, portfolio_id=portfolio_id, investor_id=investor_id)
        portfolio_query = """
            SELECT p.portfolio_id, p.portfolio_name, i.investor_name,
                   CAST(COALESCE(SUM(pp.quantity * pp.average_buy_price), 0) AS FLOAT) AS invested,
                   CAST(COALESCE(SUM(pp.quantity * s.current_price), 0) AS FLOAT) AS current_value
            FROM PORTFOLIO p
            JOIN INVESTOR i ON p.investor_id = i.investor_id
            LEFT JOIN PORTFOLIO_POSITION pp ON pp.portfolio_id = p.portfolio_id AND pp.quantity > 0
            LEFT JOIN SECURITY s ON s.security_id = pp.security_id
        """
        params = ()
        if portfolio_id:
            portfolio_query += ' WHERE p.portfolio_id = %s'
            params = (portfolio_id,)
        elif investor_id:
            portfolio_query += ' WHERE p.investor_id = %s'
            params = (investor_id,)
        portfolio_query += """
            GROUP BY p.portfolio_id, p.portfolio_name, i.investor_name
            ORDER BY current_value DESC, p.portfolio_id
        """
        cursor.execute(portfolio_query, params)
        performance = cursor.fetchall()
        trade_query = """
            SELECT t.trade_type, COUNT(*) AS trade_count,
                   CAST(COALESCE(SUM(t.quantity * t.trade_price), 0) AS FLOAT) AS trade_value
            FROM TRADE t
        """
        trade_conditions = ['COALESCE(t.is_voided, 0) = 0']
        trade_params = []
        if portfolio_id:
            trade_conditions.append('t.portfolio_id = %s')
            trade_params.append(portfolio_id)
        elif investor_id:
            trade_conditions.append('t.investor_id = %s')
            trade_params.append(investor_id)
        if trade_conditions:
            trade_query += ' WHERE ' + ' AND '.join(trade_conditions)
        trade_query += ' GROUP BY t.trade_type'
        cursor.execute(trade_query, tuple(trade_params))
        trade_activity = cursor.fetchall()
        monthly_query = """
            SELECT DATE_FORMAT(t.trade_date, '%Y-%m') AS month,
                   SUM(CASE WHEN t.trade_type = 'BUY' THEN 1 ELSE 0 END) AS buy_count,
                   SUM(CASE WHEN t.trade_type = 'SELL' THEN 1 ELSE 0 END) AS sell_count,
                   CAST(SUM(CASE WHEN t.trade_type = 'BUY' THEN t.quantity * t.trade_price ELSE 0 END) AS FLOAT) AS buy_value,
                   CAST(SUM(CASE WHEN t.trade_type = 'SELL' THEN t.quantity * t.trade_price ELSE 0 END) AS FLOAT) AS sell_value
            FROM TRADE t
        """
        monthly_conditions = ['COALESCE(t.is_voided, 0) = 0']
        monthly_params = []
        if portfolio_id:
            monthly_conditions.append('t.portfolio_id = %s')
            monthly_params.append(portfolio_id)
        elif investor_id:
            monthly_conditions.append('t.investor_id = %s')
            monthly_params.append(investor_id)
        if monthly_conditions:
            monthly_query += ' WHERE ' + ' AND '.join(monthly_conditions)
        monthly_query += " GROUP BY DATE_FORMAT(t.trade_date, '%Y-%m') ORDER BY month"
        cursor.execute(monthly_query, tuple(monthly_params))
        monthly_activity = cursor.fetchall()
        summary = holdings_summary(holdings)
        sectors = {}
        stocks = {}
        for holding in holdings:
            current_value = float(holding['current_value'])
            sector = holding['sector'] or 'Unclassified'
            sectors[sector] = sectors.get(sector, 0) + current_value
            stocks[holding['symbol']] = stocks.get(holding['symbol'], 0) + current_value
        sector_allocation = [
            {'name': name, 'value': round(value, 2)}
            for name, value in sorted(sectors.items(), key=lambda item: item[1], reverse=True)
        ]
        stock_allocation = [
            {'name': name, 'value': round(value, 2)}
            for name, value in sorted(stocks.items(), key=lambda item: item[1], reverse=True)
        ]
        top_performers = sorted(holdings, key=lambda row: float(row['pnl_percentage']), reverse=True)
        worst_performers = sorted(holdings, key=lambda row: float(row['pnl_percentage']))
        concentration = max(
            [value / summary['current_value'] * 100 for value in sectors.values()]
            if summary['current_value'] else [0]
        )
        stock_concentration = max(
            [value / summary['current_value'] * 100 for value in stocks.values()]
            if summary['current_value'] else [0]
        )
        return jsonify({
            'status': 'success',
            'summary': summary,
            'sector_allocation': sector_allocation,
            'stock_allocation': stock_allocation,
            'portfolio_performance': [
                {**row, 'invested': float(row['invested']), 'current_value': float(row['current_value'])}
                for row in performance
            ],
            'top_performers': top_performers[:5],
            'worst_performers': worst_performers[:5],
            'trade_activity': trade_activity,
            'monthly_activity': monthly_activity,
            'investor_comparison': [],
            'risk': {
                'largest_sector_weight': round(concentration, 1),
                'largest_stock_weight': round(stock_concentration, 1),
                'sector_count': len(sectors),
                'stock_count': len(stocks),
                'category': 'High concentration' if concentration >= 40 or stock_concentration >= 25
                else 'Moderate concentration' if concentration >= 25 or stock_concentration >= 15
                else 'Broadly diversified',
            },
        }), 200
    except Error as error:
        return database_error(error, 'Calculating analytics')
    finally:
        close_database(cursor, connection)


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
