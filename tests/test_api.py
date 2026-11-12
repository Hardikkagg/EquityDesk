import sys
import unittest
from pathlib import Path
from unittest.mock import patch


BACKEND_PATH = Path(__file__).resolve().parents[1] / 'backend'
sys.path.insert(0, str(BACKEND_PATH))

import app as backend_app


class ApiSmokeTests(unittest.TestCase):
    def setUp(self):
        backend_app.app.config.update(TESTING=True)
        self.client = backend_app.app.test_client()

    def test_health_and_frontend_are_served_without_a_running_server(self):
        health = self.client.get('/api/health')
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.get_json()['status'], 'healthy')
        frontend = self.client.get('/')
        self.assertEqual(frontend.status_code, 200)
        frontend.close()

    def test_invalid_trade_requests_do_not_access_the_database(self):
        invalid_requests = (
            {
                'investor_id': 1,
                'portfolio_id': 1,
                'security_id': 1,
                'trade_type': 'SELL',
                'quantity': 0,
                'trade_price': 125.5,
                'trade_date': '2026-01-15',
            },
            {
                'investor_id': 1,
                'portfolio_id': 1,
                'security_id': 1,
                'trade_type': 'HOLD',
                'quantity': 1,
                'trade_price': 125.5,
                'trade_date': '2026-01-15',
            },
        )
        with patch.object(
            backend_app,
            'get_db_connection',
            side_effect=AssertionError('invalid requests must be rejected before database access'),
        ):
            responses = [self.client.post('/api/trade', json=body) for body in invalid_requests]
        self.assertEqual([response.status_code for response in responses], [400, 400])


if __name__ == '__main__':
    unittest.main()
