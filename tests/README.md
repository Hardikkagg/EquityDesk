# Tests

## Non-destructive routes and validation

```powershell
python -m unittest discover -s tests -p "test_routes.py"
```

These tests verify frontend asset delivery, Flask health, Market Discover as the default page, required investor scoping, and invalid input handling without changing database records.

## Database-backed application checks

The configured database has been smoke-tested for investor, portfolio, security, holding, trade, analytics, market, and watchlist endpoints. Portfolio create/edit/delete and watchlist add/target/update/remove were exercised using temporary records and cleaned up.

`test_api.py` uses Flask's test client and confirms invalid trade requests are rejected before database access:

```powershell
python tests/test_api.py
```
