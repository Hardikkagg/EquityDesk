import sys
import unittest
from pathlib import Path
from unittest.mock import patch


BACKEND_PATH = Path(__file__).resolve().parents[1] / 'backend'
sys.path.insert(0, str(BACKEND_PATH))

import app as backend_app


class RouteTests(unittest.TestCase):
    def setUp(self):
        backend_app.app.config.update(TESTING=True)
        self.client = backend_app.app.test_client()

    def test_health_and_frontend_assets_are_served(self):
        health = self.client.get('/api/health')
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.get_json()['status'], 'healthy')
        homepage = self.client.get('/')
        self.assertIn(b'id="page-market" data-title="Market Discover"', homepage.data)
        self.assertIn(b'id="investor-filter"', homepage.data)
        homepage.close()
        for path in ('/', '/css/style.css', '/js/script.js'):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            response.close()

    def test_homepage_exposes_demo_label_and_card_grid_hosts(self):
        response = self.client.get('/')
        for marker in (
            b'DEMO MARKET DATA',
            b'id="investors-grid"',
            b'id="holdings-grid"',
            b'id="market-intraday"',
            b'id="market-mtf"',
            b'id="market-shockers"',
            b'id="market-etfs"',
            b'id="market-us"',
            b'id="market-news"',
        ):
            self.assertIn(marker, response.data)
        response.close()

    def test_invalid_trade_input_is_rejected_before_database_access(self):
        with patch.object(backend_app, 'get_db_connection', side_effect=AssertionError('database must not be accessed')):
            response = self.client.post('/api/trade', json={
                'investor_id': 1,
                'portfolio_id': 1,
                'security_id': 1,
                'trade_type': 'SELL',
                'quantity': 0,
                'trade_price': 125.5,
                'trade_date': '2026-01-15',
            })
        self.assertEqual(response.status_code, 400)
        self.assertIn('Quantity', response.get_json()['message'])

    def test_invalid_trade_type_and_date_are_rejected(self):
        with patch.object(backend_app, 'get_db_connection', side_effect=AssertionError('database must not be accessed')):
            invalid_type = self.client.post('/api/trade', json={
                'investor_id': 1,
                'portfolio_id': 1,
                'security_id': 1,
                'trade_type': 'HOLD',
                'quantity': 1,
                'trade_price': 125.5,
                'trade_date': '2026-01-15',
            })
            invalid_date = self.client.post('/api/trade', json={
                'investor_id': 1,
                'portfolio_id': 1,
                'security_id': 1,
                'trade_type': 'BUY',
                'quantity': 1,
                'trade_price': 125.5,
                'trade_date': 'not-a-date',
            })
        self.assertEqual(invalid_type.status_code, 400)
        self.assertEqual(invalid_date.status_code, 400)

    def test_portfolio_creation_requires_a_name(self):
        with patch.object(backend_app, 'get_db_connection', side_effect=AssertionError('database must not be accessed')):
            response = self.client.post('/api/portfolios', json={
                'investor_id': 1,
                'portfolio_name': '   ',
            })
        self.assertEqual(response.status_code, 400)
        self.assertIn('Portfolio name', response.get_json()['message'])

    def test_transaction_filters_are_validated(self):
        with patch.object(backend_app, 'get_db_connection', side_effect=AssertionError('database must not be accessed')):
            invalid_type = self.client.get('/api/trades?investor_id=1&trade_type=HOLD')
            invalid_limit = self.client.get('/api/trades?investor_id=1&limit=invalid')
            excessive_limit = self.client.get('/api/trades?investor_id=1&limit=1001')
            missing_investor = self.client.get('/api/analytics')
            missing_portfolio_scope = self.client.get('/api/portfolios')
            missing_holdings_scope = self.client.get('/api/holdings')
            missing_trade_scope = self.client.get('/api/trades')
            missing_portfolio_detail_scope = self.client.get('/api/portfolios/1')
            missing_void_scope = self.client.post('/api/trades/1/void', json={
                'reason': 'Scope validation',
            })
        self.assertEqual(invalid_type.status_code, 400)
        self.assertIn('BUY or SELL', invalid_type.get_json()['message'])
        self.assertEqual(invalid_limit.status_code, 400)
        self.assertEqual(excessive_limit.status_code, 400)
        self.assertEqual(missing_investor.status_code, 400)
        self.assertEqual(missing_portfolio_scope.status_code, 400)
        self.assertEqual(missing_holdings_scope.status_code, 400)
        self.assertEqual(missing_trade_scope.status_code, 400)
        self.assertEqual(missing_portfolio_detail_scope.status_code, 400)
        self.assertEqual(missing_void_scope.status_code, 400)

    def test_market_price_range_is_validated(self):
        response = self.client.get('/api/market?min_price=500&max_price=100')
        self.assertEqual(response.status_code, 400)
        self.assertIn('cannot exceed', response.get_json()['message'])

    def test_watchlist_requires_valid_investor_and_security(self):
        with patch.object(backend_app, 'get_db_connection', side_effect=AssertionError('database must not be accessed')):
            missing_investor = self.client.get('/api/watchlist')
            invalid_investor = self.client.post('/api/watchlist', json={
                'investor_id': 0,
                'security_id': 1,
            })
        self.assertEqual(missing_investor.status_code, 400)
        self.assertEqual(invalid_investor.status_code, 400)


if __name__ == '__main__':
    unittest.main()
