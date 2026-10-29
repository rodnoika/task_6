"""Opt-in real-service outage checks; the suite never stops a database itself."""

import pytest


pytestmark = pytest.mark.live


@pytest.mark.parametrize("path,params", [
    ("/api/users", {"locale": "en_US", "seed": "outage", "batch": 0, "batch_size": 10}),
    ("/api/locales", {}),
    ("/api/health", {}),
])
def test_database_outage_returns_503_without_fake_fallback(outage_api, path, params):
    status, body = outage_api.get(path, **params)
    assert status == 503, (path, status, body)
    assert body.get("detail"), body
    assert "users" not in body
    assert "postgresql://" not in str(body)
