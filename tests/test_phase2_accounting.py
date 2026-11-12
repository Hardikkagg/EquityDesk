import sys
import unittest
import uuid
from pathlib import Path

import mysql.connector

BACKEND_PATH = Path(__file__).resolve().parents[1] / 'backend'
sys.path.insert(0, str(BACKEND_PATH))

import app as backend_app

TEST_DB = f'equitydesk_phase2_test_{uuid.uuid4().hex[:12]}'
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
    return mysql.connector.connect(autocommit=True, **kwargs)


class Phase2AccountingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        conn = make_connection()
        cur = conn.cursor()
        cur.execute(f'CREATE DATABASE `{TEST_DB}`')
        cur.close(); conn.close()

        conn = make_connection(TEST_DB)
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE investor (
                investor_id INT PRIMARY KEY,
                investor_name VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL UNIQUE,
                phone VARCHAR(15),
                date_joined DATE NOT NULL
            )
        ''')
        cur.execute('''
            CREATE TABLE portfolio (
                portfolio_id INT PRIMARY KEY,
                investor_id INT NOT NULL,
                portfolio_name VARCHAR(100) NOT NULL,
                created_date DATE NOT NULL,
                CONSTRAINT fk_portfolio_investor FOREIGN KEY (investor_id) REFERENCES investor(investor_id)
            )
        ''')
        cur.execute('''
            CREATE TABLE security (
                security_id INT PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL UNIQUE,
                security_name VARCHAR(100) NOT NULL,
                sector VARCHAR(50),
                current_price DECIMAL(12,2) NOT NULL
            )
        ''')
        cur.execute('''
            CREATE TABLE portfolio_position (
                position_id INT PRIMARY KEY,
                portfolio_id INT NOT NULL,
                security_id INT NOT NULL,
                quantity INT NOT NULL,
                average_buy_price DECIMAL(12,2) NOT NULL,
                CONSTRAINT fk_position_portfolio FOREIGN KEY (portfolio_id) REFERENCES portfolio(portfolio_id),
                CONSTRAINT fk_position_security FOREIGN KEY (security_id) REFERENCES security(security_id)
            )
        ''')
        cur.execute('''
            CREATE TABLE trade (
                trade_id INT PRIMARY KEY AUTO_INCREMENT,
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
                CONSTRAINT fk_trade_investor FOREIGN KEY (investor_id) REFERENCES investor(investor_id),
                CONSTRAINT fk_trade_security FOREIGN KEY (security_id) REFERENCES security(security_id),
                CONSTRAINT fk_trade_portfolio FOREIGN KEY (portfolio_id) REFERENCES portfolio(portfolio_id),
                CONSTRAINT chk_trade_type CHECK (trade_type IN ('BUY', 'SELL'))
            )
        ''')
        cur.execute('''
            CREATE TABLE audit_log (
                audit_id BIGINT NOT NULL AUTO_INCREMENT,
                transaction_id INT NOT NULL,
                action_type VARCHAR(50) NOT NULL,
                old_values JSON NULL,
                new_values JSON NULL,
                reason VARCHAR(255) NULL,
                performed_by VARCHAR(100) NOT NULL DEFAULT 'system',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (audit_id),
                KEY idx_audit_transaction (transaction_id),
                KEY idx_audit_action (action_type, created_at),
                CONSTRAINT fk_audit_trade FOREIGN KEY (transaction_id) REFERENCES trade(trade_id) ON DELETE RESTRICT
            )
        ''')
        cur.close(); conn.close()

        backend_app.app.config.update(
            TESTING=True,
            MYSQL_DB=TEST_DB,
        )

    @classmethod
    def tearDownClass(cls):
        conn = make_connection()
        cur = conn.cursor()
        cur.execute(f'DROP DATABASE IF EXISTS `{TEST_DB}`')
        cur.close(); conn.close()

    def setUp(self):
        self.reset_test_data()
        self.client = backend_app.app.test_client()
        self.seed_base_records()

    def reset_test_data(self):
        conn = make_connection(TEST_DB)
        cur = conn.cursor()
        cur.execute('SET FOREIGN_KEY_CHECKS = 0')
        for table in ['audit_log', 'trade', 'portfolio_position', 'portfolio', 'security', 'investor']:
            cur.execute(f'TRUNCATE TABLE `{table}`')
        cur.execute('SET FOREIGN_KEY_CHECKS = 1')
        cur.close(); conn.close()

    def seed_base_records(self):
        conn = make_connection(TEST_DB)
        cur = conn.cursor()
        cur.execute("INSERT INTO investor (investor_id, investor_name, email, phone, date_joined) VALUES (1, 'Test Investor', 'investor@test.com', '9999999999', '2024-01-01')")
        cur.execute("INSERT INTO portfolio (portfolio_id, investor_id, portfolio_name, created_date) VALUES (10, 1, 'Primary', '2024-01-02')")
        cur.execute("INSERT INTO security (security_id, symbol, security_name, sector, current_price) VALUES (20, 'ABC', 'Alpha Battery Co', 'Technology', 150.00)")
        cur.close(); conn.close()

    def api_trade(self, payload):
        return self.client.post('/api/trade', json=payload)

    def test_fifo_sell_matches_oldest_lots_and_partial_sells(self):
        buy_one = {"investor_id": 1, "portfolio_id": 10, "security_id": 20, "trade_type": "BUY", "quantity": 10, "trade_price": 100.0, "trade_date": "2024-02-01"}
        buy_two = {"investor_id": 1, "portfolio_id": 10, "security_id": 20, "trade_type": "BUY", "quantity": 10, "trade_price": 120.0, "trade_date": "2024-02-02"}
        sell_one = {"investor_id": 1, "portfolio_id": 10, "security_id": 20, "trade_type": "SELL", "quantity": 15, "trade_price": 150.0, "trade_date": "2024-02-03"}
        sell_two = {"investor_id": 1, "portfolio_id": 10, "security_id": 20, "trade_type": "SELL", "quantity": 5, "trade_price": 160.0, "trade_date": "2024-02-04"}

        self.assertEqual(self.api_trade(buy_one).status_code, 201)
        self.assertEqual(self.api_trade(buy_two).status_code, 201)
        self.assertEqual(self.api_trade(sell_one).status_code, 201)

        conn = make_connection(TEST_DB)
        cur = conn.cursor(dictionary=True)
        metrics = backend_app.collect_fifo_lots(cur, 10, 20)
        cur.close(); conn.close()

        self.assertEqual(metrics['quantity'], 5)
        self.assertEqual(metrics['cost_basis'], 600.0)
        self.assertEqual(metrics['realized_pnl'], 650.0)

        self.assertEqual(self.api_trade(sell_two).status_code, 201)
        conn = make_connection(TEST_DB)
        cur = conn.cursor(dictionary=True)
        metrics = backend_app.collect_fifo_lots(cur, 10, 20)
        cur.close(); conn.close()

        self.assertEqual(metrics['quantity'], 0)
        self.assertEqual(metrics['cost_basis'], 0.0)
        self.assertEqual(metrics['realized_pnl'], 850.0)

    def test_sell_cannot_exceed_available_quantity(self):
        buy = {
            "investor_id": 1, "portfolio_id": 10, "security_id": 20,
            "trade_type": "BUY", "quantity": 5, "trade_price": 100.0,
            "trade_date": "2024-02-01",
        }
        sell = {
            "investor_id": 1, "portfolio_id": 10, "security_id": 20,
            "trade_type": "SELL", "quantity": 6, "trade_price": 110.0,
            "trade_date": "2024-02-02",
        }
        self.assertEqual(self.api_trade(buy).status_code, 201)
        response = self.api_trade(sell)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Insufficient quantity', response.get_json()['message'])

        conn = make_connection(TEST_DB)
        cur = conn.cursor(dictionary=True)
        cur.execute('SELECT COUNT(*) AS trade_count FROM trade')
        self.assertEqual(int(cur.fetchone()['trade_count']), 1)
        cur.execute('SELECT quantity FROM portfolio_position WHERE portfolio_id = 10 AND security_id = 20')
        self.assertEqual(int(cur.fetchone()['quantity']), 5)
        cur.execute('SELECT COUNT(*) AS audit_count FROM audit_log')
        self.assertEqual(int(cur.fetchone()['audit_count']), 1)
        cur.close(); conn.close()

    def test_voiding_sell_transaction_reverses_realized_pnl_and_creates_audit_entry(self):
        self.api_trade({"investor_id": 1, "portfolio_id": 10, "security_id": 20, "trade_type": "BUY", "quantity": 10, "trade_price": 100.0, "trade_date": "2024-02-01"})
        sell_response = self.api_trade({"investor_id": 1, "portfolio_id": 10, "security_id": 20, "trade_type": "SELL", "quantity": 5, "trade_price": 150.0, "trade_date": "2024-02-02"})
        self.assertEqual(sell_response.status_code, 201)

        sell_id = sell_response.get_json()['data']['trade_id']
        void_response = self.client.post(f'/api/trades/{sell_id}/void', json={'investor_id': 1, 'reason': 'Test sell correction', 'performed_by': 'qa-agent'})
        self.assertEqual(void_response.status_code, 200)

        conn = make_connection(TEST_DB)
        cur = conn.cursor(dictionary=True)
        cur.execute('SELECT is_voided, void_reason FROM trade WHERE trade_id = %s', (sell_id,))
        row = cur.fetchone()
        self.assertEqual(int(row['is_voided']), 1)
        self.assertEqual(row['void_reason'], 'Test sell correction')
        cur.execute('SELECT COUNT(*) AS audit_count FROM audit_log WHERE transaction_id = %s AND action_type = %s', (sell_id, 'TRADE_VOIDED'))
        self.assertEqual(int(cur.fetchone()['audit_count']), 1)
        metrics = backend_app.collect_fifo_lots(cur, 10, 20)
        cur.close(); conn.close()

        self.assertEqual(metrics['quantity'], 10)
        self.assertEqual(metrics['realized_pnl'], 0.0)

    def test_another_investor_cannot_void_a_trade_by_trade_id(self):
        conn = make_connection(TEST_DB)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO investor (investor_id, investor_name, email, date_joined) VALUES (2, 'Other Investor', 'other@test.com', '2024-01-01')"
        )
        cur.execute(
            "INSERT INTO portfolio (portfolio_id, investor_id, portfolio_name, created_date) VALUES (20, 2, 'Other Portfolio', '2024-01-02')"
        )
        conn.commit()
        cur.close(); conn.close()

        buy_response = self.api_trade({
            "investor_id": 1, "portfolio_id": 10, "security_id": 20,
            "trade_type": "BUY", "quantity": 2, "trade_price": 100.0,
            "trade_date": "2024-02-01",
        })
        self.assertEqual(buy_response.status_code, 201)
        trade_id = buy_response.get_json()['data']['trade_id']
        response = self.client.post(
            f'/api/trades/{trade_id}/void',
            json={'investor_id': 2, 'reason': 'Cross-investor attempt', 'performed_by': 'qa-agent'},
        )
        self.assertEqual(response.status_code, 404)

        conn = make_connection(TEST_DB)
        cur = conn.cursor(dictionary=True)
        cur.execute('SELECT is_voided FROM trade WHERE trade_id = %s', (trade_id,))
        self.assertEqual(int(cur.fetchone()['is_voided']), 0)
        cur.execute(
            'SELECT COUNT(*) AS audit_count FROM audit_log WHERE transaction_id = %s AND action_type = %s',
            (trade_id, 'TRADE_VOIDED'),
        )
        self.assertEqual(int(cur.fetchone()['audit_count']), 0)
        cur.close(); conn.close()

    def test_voiding_buy_without_dependent_sell_is_allowed(self):
        buy_response = self.api_trade({"investor_id": 1, "portfolio_id": 10, "security_id": 20, "trade_type": "BUY", "quantity": 10, "trade_price": 100.0, "trade_date": "2024-02-01"})
        self.assertEqual(buy_response.status_code, 201)
        buy_id = buy_response.get_json()['data']['trade_id']

        response = self.client.post(f'/api/trades/{buy_id}/void', json={'investor_id': 1, 'reason': 'Remove extraneous buy', 'performed_by': 'qa-agent'})
        self.assertEqual(response.status_code, 200)

        conn = make_connection(TEST_DB)
        cur = conn.cursor(dictionary=True)
        cur.execute('SELECT is_voided, void_reason FROM trade WHERE trade_id = %s', (buy_id,))
        row = cur.fetchone()
        self.assertEqual(int(row['is_voided']), 1)
        self.assertEqual(row['void_reason'], 'Remove extraneous buy')
        cur.execute('SELECT COUNT(*) AS audit_count FROM audit_log WHERE transaction_id = %s AND action_type = %s', (buy_id, 'TRADE_VOIDED'))
        self.assertEqual(int(cur.fetchone()['audit_count']), 1)
        cur.close(); conn.close()

    def test_buy_void_rejects_when_dependent_sell_exists(self):
        self.api_trade({"investor_id": 1, "portfolio_id": 10, "security_id": 20, "trade_type": "BUY", "quantity": 10, "trade_price": 100.0, "trade_date": "2024-02-01"})
        self.api_trade({"investor_id": 1, "portfolio_id": 10, "security_id": 20, "trade_type": "SELL", "quantity": 5, "trade_price": 150.0, "trade_date": "2024-02-02"})
        response = self.client.post('/api/trades/1/void', json={'investor_id': 1, 'reason': 'Attempt to cancel consumed lot', 'performed_by': 'qa-agent'})
        self.assertEqual(response.status_code, 409)
        self.assertIn('dependent SELL', response.get_json()['message'])

        conn = make_connection(TEST_DB)
        cur = conn.cursor(dictionary=True)
        cur.execute('SELECT is_voided FROM trade WHERE trade_id = %s', (1,))
        self.assertEqual(int(cur.fetchone()['is_voided']), 0)
        cur.execute('SELECT COUNT(*) AS audit_count FROM audit_log WHERE action_type = %s AND reason = %s', ('TRADE_VOIDED', 'Attempt to cancel consumed lot'))
        self.assertEqual(int(cur.fetchone()['audit_count']), 0)
        cur.close(); conn.close()


if __name__ == '__main__':
    unittest.main(verbosity=2)
