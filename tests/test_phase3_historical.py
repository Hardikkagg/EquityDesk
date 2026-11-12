import sys
import unittest
import uuid
from datetime import date, timedelta
from pathlib import Path

import mysql.connector

BACKEND_PATH = Path(__file__).resolve().parents[1] / 'backend'
PROJECT_PATH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_PATH))

import app as backend_app


TEST_DB = f'equitydesk_phase3_test_{uuid.uuid4().hex[:12]}'
DB_CONFIG = {
    'host': backend_app.app.config['MYSQL_HOST'],
    'port': backend_app.app.config['MYSQL_PORT'],
    'user': backend_app.app.config['MYSQL_USER'],
    'password': backend_app.app.config['MYSQL_PASSWORD'],
}


def make_connection(database=None):
    kwargs = dict(DB_CONFIG)
    if database:
        kwargs['database'] = database
    return mysql.connector.connect(**kwargs)


class HistoricalPricesAndXirrTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        connection = make_connection()
        cursor = connection.cursor()
        cursor.execute(f'CREATE DATABASE `{TEST_DB}`')
        cursor.close()
        connection.close()

        connection = make_connection(TEST_DB)
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE investor (
                investor_id INT PRIMARY KEY,
                investor_name VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL UNIQUE,
                phone VARCHAR(15),
                date_joined DATE NOT NULL
            ) ENGINE=InnoDB
        """)
        cursor.execute("""
            CREATE TABLE portfolio (
                portfolio_id INT PRIMARY KEY,
                investor_id INT NOT NULL,
                portfolio_name VARCHAR(100) NOT NULL,
                created_date DATE NOT NULL,
                CONSTRAINT fk_phase3_portfolio_investor FOREIGN KEY (investor_id) REFERENCES investor(investor_id)
            ) ENGINE=InnoDB
        """)
        cursor.execute("""
            CREATE TABLE security (
                security_id INT PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL UNIQUE,
                security_name VARCHAR(100) NOT NULL,
                sector VARCHAR(50),
                current_price DECIMAL(12,2) NOT NULL
            ) ENGINE=InnoDB
        """)
        cursor.execute("""
            CREATE TABLE portfolio_position (
                position_id INT PRIMARY KEY,
                portfolio_id INT NOT NULL,
                security_id INT NOT NULL,
                quantity INT NOT NULL,
                average_buy_price DECIMAL(12,2) NOT NULL,
                CONSTRAINT fk_phase3_position_portfolio FOREIGN KEY (portfolio_id) REFERENCES portfolio(portfolio_id),
                CONSTRAINT fk_phase3_position_security FOREIGN KEY (security_id) REFERENCES security(security_id)
            ) ENGINE=InnoDB
        """)
        cursor.execute("""
            CREATE TABLE trade (
                trade_id INT PRIMARY KEY,
                investor_id INT NOT NULL,
                security_id INT NOT NULL,
                portfolio_id INT NOT NULL,
                trade_type VARCHAR(10) NOT NULL,
                quantity INT NOT NULL,
                trade_price DECIMAL(12,2) NOT NULL,
                trade_date DATE NOT NULL,
                is_voided TINYINT(1) NOT NULL DEFAULT 0,
                void_reason VARCHAR(255) NULL,
                voided_by VARCHAR(100) NULL,
                voided_at DATETIME NULL,
                CONSTRAINT fk_phase3_trade_investor FOREIGN KEY (investor_id) REFERENCES investor(investor_id),
                CONSTRAINT fk_phase3_trade_security FOREIGN KEY (security_id) REFERENCES security(security_id),
                CONSTRAINT fk_phase3_trade_portfolio FOREIGN KEY (portfolio_id) REFERENCES portfolio(portfolio_id),
                CONSTRAINT chk_phase3_trade_type CHECK (trade_type IN ('BUY', 'SELL'))
            ) ENGINE=InnoDB
        """)
        migration = (PROJECT_PATH / 'database' / '07_price_history.sql').read_text(encoding='utf-8')
        cursor.execute(migration)
        cursor.execute(migration)
        cursor.execute("""
            CREATE TABLE watchlist (
                investor_id INT NOT NULL,
                security_id INT NOT NULL,
                target_price DECIMAL(12,2),
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (investor_id, security_id),
                CONSTRAINT fk_phase3_watchlist_investor FOREIGN KEY (investor_id) REFERENCES investor(investor_id),
                CONSTRAINT fk_phase3_watchlist_security FOREIGN KEY (security_id) REFERENCES security(security_id)
            ) ENGINE=InnoDB
        """)
        cursor.execute("INSERT INTO investor VALUES (1, 'Test Investor', 'test@example.invalid', NULL, '2023-01-01')")
        cursor.execute("INSERT INTO portfolio VALUES (10, 1, 'Growth', '2023-01-02')")
        cursor.execute("INSERT INTO portfolio VALUES (11, 1, 'Separate', '2023-01-02')")
        cursor.execute("INSERT INTO investor VALUES (2, 'Other Investor', 'other@example.invalid', NULL, '2023-01-01')")
        cursor.execute("INSERT INTO portfolio VALUES (12, 2, 'Private Portfolio', '2023-01-02')")
        cursor.execute("INSERT INTO security VALUES (20, 'TEST', 'Test Company', 'Technology', 160.00)")
        cursor.execute("INSERT INTO security VALUES (21, 'OTHER', 'Other Company', 'Finance', 50.00)")
        connection.commit()
        cursor.close()
        connection.close()

        backend_app.app.config.update(
            TESTING=True,
            MYSQL_HOST=DB_CONFIG['host'],
            MYSQL_PORT=DB_CONFIG['port'],
            MYSQL_USER=DB_CONFIG['user'],
            MYSQL_PASSWORD=DB_CONFIG['password'],
            MYSQL_DB=TEST_DB,
        )

    @classmethod
    def tearDownClass(cls):
        connection = make_connection()
        cursor = connection.cursor()
        cursor.execute(f'DROP DATABASE `{TEST_DB}`')
        cursor.close()
        connection.close()

    def setUp(self):
        connection = make_connection(TEST_DB)
        cursor = connection.cursor()
        cursor.execute('DELETE FROM price_history')
        cursor.execute('DELETE FROM trade')
        cursor.execute('DELETE FROM portfolio_position')
        cursor.execute('DELETE FROM watchlist')
        connection.commit()
        cursor.close()
        connection.close()
        self.client = backend_app.app.test_client()

    def insert_trade(self, trade_id, portfolio_id, trade_type, quantity, price, trade_date, is_voided=0):
        connection = make_connection(TEST_DB)
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO trade
                (trade_id, investor_id, security_id, portfolio_id, trade_type, quantity, trade_price, trade_date, is_voided)
            VALUES (%s, 1, 20, %s, %s, %s, %s, %s, %s)
        """, (trade_id, portfolio_id, trade_type, quantity, price, trade_date, is_voided))
        connection.commit()
        cursor.close()
        connection.close()

    def insert_position(self, position_id, portfolio_id, quantity, average_buy_price):
        connection = make_connection(TEST_DB)
        cursor = connection.cursor()
        cursor.execute(
            'INSERT INTO portfolio_position VALUES (%s, %s, 20, %s, %s)',
            (position_id, portfolio_id, quantity, average_buy_price),
        )
        connection.commit()
        cursor.close()
        connection.close()

    def post_csv(self, content):
        return self.client.post(
            '/api/price-history/import',
            data={'file': (io_bytes(content), 'prices.csv')},
            content_type='multipart/form-data',
        )

    def test_xirr_returns_known_annual_rate_and_rejects_insufficient_flows(self):
        rate = backend_app.calculate_xirr([
            (date(2023, 1, 1), -1000),
            (date(2024, 1, 1), 1100),
        ])
        self.assertIsNotNone(rate)
        self.assertAlmostEqual(rate, 0.10, places=5)
        self.assertIsNone(backend_app.calculate_xirr([(date(2024, 1, 1), -1000)]))
        self.assertIsNone(backend_app.calculate_xirr([
            (date(2024, 1, 1), -1000),
            (date(2024, 1, 1), 1100),
        ]))
        self.assertIsNone(backend_app.calculate_xirr([
            (date(2022, 1, 1), -100),
            (date(2023, 1, 1), 230),
            (date(2024, 1, 1), -132),
        ]))

    def test_csv_import_duplicate_prevention_and_current_price_is_unchanged(self):
        today = date.today()
        rows = [
            f'20,{today - timedelta(days=5)},155.00',
            f'20,{today - timedelta(days=20)},150.00',
            f'20,{today - timedelta(days=45)},145.00',
            f'20,{today - timedelta(days=400)},130.00',
            f'20,{today - timedelta(days=5)},999.00',
        ]
        response = self.post_csv('security_id,price_date,close_price\n' + '\n'.join(rows))
        self.assertEqual(response.status_code, 201, response.get_json())
        result = response.get_json()['data']
        self.assertEqual(result['rows_received'], 5)
        self.assertEqual(result['rows_inserted'], 4)
        self.assertEqual(result['rows_skipped_as_duplicates'], 1)
        self.assertFalse(result['current_price_modified'])

        connection = make_connection(TEST_DB)
        cursor = connection.cursor()
        cursor.execute('SELECT current_price FROM security WHERE security_id = 20')
        self.assertEqual(float(cursor.fetchone()[0]), 160.0)
        cursor.execute('SELECT close_price FROM price_history WHERE security_id = 20 AND price_date = %s', (today - timedelta(days=5),))
        self.assertEqual(float(cursor.fetchone()[0]), 155.0)
        cursor.close()
        connection.close()

    def test_csv_import_rejects_unknown_securities_and_invalid_prices(self):
        response = self.post_csv('security_id,price_date,close_price\n999,2024-01-01,10.00')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Unknown security_id', response.get_json()['message'])
        response = self.post_csv('security_id,price_date,close_price\n20,2024-01-01,0')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Close price', response.get_json()['message'])

    def test_security_history_periods_and_related_transactions(self):
        self.insert_trade(1, 10, 'BUY', 3, 100, '2024-01-01')
        connection = make_connection(TEST_DB)
        cursor = connection.cursor()
        cursor.execute('INSERT INTO portfolio_position VALUES (1, 10, 20, 3, 100)')
        connection.commit()
        cursor.close()
        connection.close()
        content = 'security_id,price_date,close_price\n' + '\n'.join([
            f'20,{date.today() - timedelta(days=5)},155',
            f'20,{date.today() - timedelta(days=20)},150',
            f'20,{date.today() - timedelta(days=45)},145',
            f'20,{date.today() - timedelta(days=400)},130',
        ])
        self.assertEqual(self.post_csv(content).status_code, 201)
        expected = {'1W': 1, '1M': 2, '1Y': 3, 'ALL': 4}
        for period, count in expected.items():
            response = self.client.get(f'/api/securities/20?period={period}&investor_id=1')
            self.assertEqual(response.status_code, 200, response.get_json())
            data = response.get_json()['data']
            self.assertEqual(len(data['historical_prices']), count)
            self.assertEqual(len(data['transactions']), 1)
            self.assertEqual(data['price_source'], 'SECURITY.current_price')
            self.assertEqual(data['portfolio_count'], 1)
            self.assertEqual(data['shares_held'], 3)
            self.assertEqual(len(data['holdings']), 1)
            self.assertEqual(data['holdings'][0]['portfolio_id'], 10)
        trade_history = self.client.get('/api/trades?investor_id=1&portfolio_id=10&limit=20')
        self.assertEqual(trade_history.status_code, 200, trade_history.get_json())
        self.assertEqual(len(trade_history.get_json()['data']), 1)

    def test_portfolio_list_includes_fifo_realized_and_unrealized_metrics(self):
        self.insert_trade(1, 10, 'BUY', 10, 100, '2024-01-01')
        self.insert_trade(2, 10, 'SELL', 2, 150, '2024-02-01')
        self.insert_position(1, 10, 8, 100)

        response = self.client.get('/api/portfolios?investor_id=1')
        self.assertEqual(response.status_code, 200, response.get_json())
        portfolios = {row['portfolio_id']: row for row in response.get_json()['data']}
        growth = portfolios[10]
        self.assertEqual(growth['realized_pnl'], 100.0)
        self.assertEqual(growth['unrealized_pnl'], 480.0)
        self.assertEqual(growth['total_pnl'], 580.0)
        self.assertEqual(growth['gross_buy_amount'], 1000.0)
        self.assertEqual(growth['return_percentage'], 58.0)
        self.assertEqual(growth['holding_count'], 1)

        empty = portfolios[11]
        self.assertEqual(empty['holding_count'], 0)
        self.assertEqual(empty['realized_pnl'], 0.0)
        self.assertIsNone(empty['return_percentage'])

    def test_holdings_keep_fifo_basis_and_pnl_separate_by_portfolio(self):
        self.insert_trade(1, 10, 'BUY', 10, 100, '2024-01-01')
        self.insert_trade(2, 10, 'SELL', 2, 150, '2024-02-01')
        self.insert_trade(3, 11, 'BUY', 5, 120, '2024-01-01')
        self.insert_position(1, 10, 8, 100)
        self.insert_position(2, 11, 5, 120)

        response = self.client.get('/api/holdings?investor_id=1')
        self.assertEqual(response.status_code, 200, response.get_json())
        holdings = {row['portfolio_id']: row for row in response.get_json()['data']}
        self.assertEqual(len(holdings), 2)
        self.assertEqual(holdings[10]['invested_value'], 800.0)
        self.assertEqual(holdings[10]['realized_pnl'], 100.0)
        self.assertEqual(holdings[10]['unrealized_pnl'], 480.0)
        self.assertEqual(holdings[11]['invested_value'], 600.0)
        self.assertEqual(holdings[11]['realized_pnl'], 0.0)
        self.assertEqual(holdings[11]['unrealized_pnl'], 200.0)

    def test_investor_scope_prevents_cross_investor_detail_and_activity_access(self):
        self.insert_trade(1, 10, 'BUY', 3, 100, '2024-01-01')
        self.insert_position(1, 10, 3, 100)

        private_detail = self.client.get('/api/portfolios/10?investor_id=2')
        self.assertEqual(private_detail.status_code, 404)
        private_holdings = self.client.get('/api/holdings?investor_id=2&portfolio_id=10')
        self.assertEqual(private_holdings.status_code, 404)
        private_trades = self.client.get('/api/trades?investor_id=2&portfolio_id=10')
        self.assertEqual(private_trades.status_code, 404)
        private_update = self.client.put('/api/portfolios/10', json={
            'investor_id': 2,
            'portfolio_name': 'Unauthorized rename',
        })
        self.assertEqual(private_update.status_code, 404)
        private_delete = self.client.delete('/api/portfolios/10', json={'investor_id': 2})
        self.assertEqual(private_delete.status_code, 404)
        private_security = self.client.get('/api/securities/20?investor_id=2')
        self.assertEqual(private_security.status_code, 200)
        security_data = private_security.get_json()['data']
        self.assertEqual(security_data['portfolio_count'], 0)
        self.assertEqual(security_data['shares_held'], 0)
        self.assertEqual(security_data['holdings'], [])
        self.assertEqual(security_data['transactions'], [])

        own_portfolios = self.client.get('/api/portfolios?investor_id=2')
        self.assertEqual([row['portfolio_id'] for row in own_portfolios.get_json()['data']], [12])
        own_analytics = self.client.get('/api/analytics?investor_id=2')
        self.assertEqual(own_analytics.status_code, 200)
        self.assertEqual(own_analytics.get_json()['summary']['stocks_held'], 0)
        self.assertEqual(own_analytics.get_json()['investor_comparison'], [])

    def test_portfolio_crud_stays_inside_selected_investor_scope(self):
        created = self.client.post('/api/portfolios', json={
            'investor_id': 1,
            'portfolio_name': 'Temporary Test Portfolio',
        })
        self.assertEqual(created.status_code, 201, created.get_json())
        portfolio_id = created.get_json()['data']['portfolio_id']

        updated = self.client.put(f'/api/portfolios/{portfolio_id}', json={
            'investor_id': 1,
            'portfolio_name': 'Renamed Test Portfolio',
        })
        self.assertEqual(updated.status_code, 200, updated.get_json())
        detail = self.client.get(f'/api/portfolios/{portfolio_id}?investor_id=1')
        self.assertEqual(detail.status_code, 200, detail.get_json())
        self.assertEqual(detail.get_json()['data']['portfolio_name'], 'Renamed Test Portfolio')

        deleted = self.client.delete(f'/api/portfolios/{portfolio_id}', json={'investor_id': 1})
        self.assertEqual(deleted.status_code, 200, deleted.get_json())
        self.assertEqual(self.client.get(f'/api/portfolios/{portfolio_id}?investor_id=1').status_code, 404)

    def test_market_discover_does_not_expose_investor_activity_as_market_data(self):
        response = self.client.get('/api/market')
        self.assertEqual(response.status_code, 200, response.get_json())
        data = response.get_json()
        self.assertEqual(data['price_source'], 'SECURITY.current_price')
        self.assertFalse(data['is_live'])
        self.assertEqual(data['most_bought'], [])
        self.assertEqual(data['most_held'], [])
        self.assertFalse(data['market_sections_available']['volume_shockers'])
        self.assertEqual(len(data['securities']), 2)

    def test_watchlist_add_target_update_and_remove_are_isolated_to_investor(self):
        added = self.client.post('/api/watchlist', json={
            'investor_id': 1,
            'security_id': 20,
        })
        self.assertEqual(added.status_code, 201, added.get_json())
        duplicate = self.client.post('/api/watchlist', json={
            'investor_id': 1,
            'security_id': 20,
        })
        self.assertEqual(duplicate.status_code, 201, duplicate.get_json())
        other_investor_list = self.client.get('/api/watchlist?investor_id=2')
        self.assertEqual(other_investor_list.status_code, 200, other_investor_list.get_json())
        self.assertEqual(other_investor_list.get_json()['data'], [])
        cross_investor_remove = self.client.delete('/api/watchlist', json={
            'investor_id': 2,
            'security_id': 20,
        })
        self.assertEqual(cross_investor_remove.status_code, 404)

        updated = self.client.put('/api/watchlist', json={
            'investor_id': 1,
            'security_id': 20,
            'target_price': 150,
        })
        self.assertEqual(updated.status_code, 200, updated.get_json())
        listed = self.client.get('/api/watchlist?investor_id=1')
        self.assertEqual(listed.status_code, 200, listed.get_json())
        self.assertEqual(len(listed.get_json()['data']), 1)
        connection = make_connection(TEST_DB)
        cursor = connection.cursor()
        cursor.execute('SELECT COUNT(*) FROM watchlist WHERE investor_id = 1 AND security_id = 20')
        self.assertEqual(cursor.fetchone()[0], 1)
        cursor.close()
        connection.close()
        self.assertEqual(float(listed.get_json()['data'][0]['target_price']), 150.0)
        self.assertEqual(listed.get_json()['data'][0]['target_reached'], 1)

        removed = self.client.delete('/api/watchlist', json={
            'investor_id': 1,
            'security_id': 20,
        })
        self.assertEqual(removed.status_code, 200, removed.get_json())
        self.assertEqual(self.client.get('/api/watchlist?investor_id=1').get_json()['data'], [])
        invalid = self.client.get('/api/securities/20?period=2Y')
        self.assertEqual(invalid.status_code, 400)

    def test_portfolio_detail_fifo_metrics_xirr_and_voided_trade_exclusion(self):
        self.insert_trade(1, 10, 'BUY', 10, 100, '2024-01-01')
        self.insert_trade(2, 10, 'BUY', 10, 120, '2024-02-01')
        self.insert_trade(3, 10, 'SELL', 15, 150, '2024-03-01')
        self.insert_trade(4, 10, 'BUY', 99, 900, '2024-04-01', is_voided=1)
        self.insert_trade(5, 11, 'BUY', 100, 50, '2024-01-01')
        self.insert_trade(6, 10, 'SELL', 1, 160, '2024-04-15')
        self.insert_position(1, 10, 4, 120)
        response = self.client.get('/api/portfolios/10?investor_id=1')
        self.assertEqual(response.status_code, 200, response.get_json())
        portfolio = response.get_json()['data']
        self.assertEqual(portfolio['portfolio_value'], 640.0)
        self.assertEqual(portfolio['open_cost_basis'], 480.0)
        self.assertEqual(portfolio['total_invested'], 480.0)
        self.assertEqual(portfolio['gross_buy_amount'], 2200.0)
        self.assertEqual(portfolio['realized_pnl'], 690.0)
        self.assertEqual(portfolio['unrealized_pnl'], 160.0)
        self.assertAlmostEqual(portfolio['return_percentage'], (850 / 2200) * 100, places=2)
        self.assertTrue(portfolio['xirr_available'])
        self.assertGreater(portfolio['xirr_percentage'], 0)
        self.assertEqual([row['quantity'] for row in portfolio['holdings']], [4])
        self.assertEqual(len(portfolio['transactions']), 5)
        self.assertTrue(any(row['is_voided'] for row in portfolio['transactions']))
        self.assertFalse(portfolio['historical_performance_available'])

    def test_portfolio_history_needs_and_uses_real_price_history(self):
        self.insert_trade(1, 10, 'BUY', 3, 100, '2024-01-01')
        content = 'security_id,price_date,close_price\n' + '\n'.join([
            f'20,{date.today() - timedelta(days=5)},155',
            f'20,{date.today() - timedelta(days=20)},150',
        ])
        self.assertEqual(self.post_csv(content).status_code, 201)
        response = self.client.get('/api/portfolios/10?investor_id=1')
        self.assertEqual(response.status_code, 200, response.get_json())
        portfolio = response.get_json()['data']
        self.assertTrue(portfolio['historical_performance_available'])
        self.assertEqual(len(portfolio['historical_performance']), 2)

    def test_portfolio_detail_keeps_stored_positions_without_trade_ledger_rows(self):
        self.insert_position(1, 10, 2, 100)
        response = self.client.get('/api/portfolios/10?investor_id=1')
        self.assertEqual(response.status_code, 200, response.get_json())
        portfolio = response.get_json()['data']
        self.assertEqual(portfolio['portfolio_value'], 320.0)
        self.assertEqual(portfolio['total_invested'], 200.0)
        self.assertEqual(portfolio['unrealized_pnl'], 120.0)
        self.assertEqual(portfolio['holdings'][0]['cost_basis_source'], 'PORTFOLIO_POSITION.average_buy_price')

    def test_xirr_is_unavailable_without_sufficient_cash_flows(self):
        self.insert_trade(1, 10, 'BUY', 1, 100, date.today().isoformat())
        self.insert_position(1, 10, 1, 100)
        response = self.client.get('/api/portfolios/10?investor_id=1')
        self.assertEqual(response.status_code, 200)
        portfolio = response.get_json()['data']
        self.assertFalse(portfolio['xirr_available'])
        self.assertIsNone(portfolio['xirr_percentage'])


def io_bytes(content):
    from io import BytesIO
    return BytesIO(content.encode('utf-8'))


if __name__ == '__main__':
    unittest.main()
