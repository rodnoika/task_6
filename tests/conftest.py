"""Live integration fixtures; no service output is replaced with test doubles."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "live: requires the running FastAPI service")
    config.addinivalue_line("markers", "database: requires DATABASE_URL and psycopg")
    config.addinivalue_line("markers", "statistical: generates 10000 records for distribution checks")


@dataclass(frozen=True)
class Api:
    base_url: str

    def get_text(self, path, **params):
        query = urllib.parse.urlencode(params)
        url = self.base_url.rstrip("/") + path + ("?" + query if query else "")
        with urllib.request.urlopen(url, timeout=60) as response:
            return response.status, response.headers.get_content_type(), response.read().decode("utf-8")

    def get(self, path, **params):
        query = urllib.parse.urlencode(params)
        url = self.base_url.rstrip("/") + path + ("?" + query if query else "")
        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                return response.status, json.loads(response.read())
        except urllib.error.HTTPError as response:
            return response.code, json.loads(response.read())

    def users(self, *, locale="en_US", seed="42", batch=0, batch_size=10):
        status, payload = self.get(
            "/api/users", locale=locale, seed=seed, batch=batch, batch_size=batch_size
        )
        assert status == 200, (status, payload)
        return payload


@pytest.fixture(scope="session")
def api():
    client = Api(os.environ.get("API_BASE_URL", "http://localhost:8000"))
    try:
        status, payload = client.get("/api/locales")
    except (OSError, urllib.error.URLError) as exc:
        message = f"FastAPI service is unavailable at {client.base_url}: {exc}"
        if os.environ.get("REQUIRE_LIVE_API") == "1":
            pytest.fail(message)
        pytest.skip(message + "; set REQUIRE_LIVE_API=1 for strict acceptance runs")
    assert status == 200, (status, payload)
    return client


@pytest.fixture(scope="session")
def outage_api():
    base_url = os.environ.get("OUTAGE_API_BASE_URL")
    if not base_url:
        pytest.skip("Set OUTAGE_API_BASE_URL to an API process configured with an unavailable database")
    return Api(base_url)


@pytest.fixture(scope="session")
def db_connect():
    url = os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip("Set DATABASE_URL to run direct PostgreSQL acceptance checks")
    psycopg = pytest.importorskip("psycopg", reason="Install psycopg[binary] for direct SQL checks")

    def connect():
        return psycopg.connect(url, connect_timeout=10)

    # A configured database is required to work: do not silently skip a broken DB.
    with connect() as connection:
        connection.execute("SELECT 1")
    return connect


@pytest.fixture
def sql_users(db_connect):
    def generate(*, locale="en_US", seed="42", batch=0, batch_size=10):
        # Every invocation opens a different database session. PostgreSQL session
        # RNG state therefore cannot accidentally satisfy replay comparisons.
        with db_connect() as connection:
            result = connection.execute(
                "CALL faker.generate_batch(%s, %s, %s, %s, NULL)",
                (locale, seed, batch, batch_size),
            ).fetchone()
        assert result is not None and isinstance(result[0], dict), result
        return result[0]

    return generate


@pytest.fixture(scope="session")
def distribution_rows(db_connect):
    cache = {}

    def sample(locale):
        if locale not in cache:
            rows = []
            with db_connect() as connection:
                for batch in range(50):
                    result = connection.execute(
                        "CALL faker.generate_batch(%s, %s, %s, %s, NULL)",
                        (locale, "qa-distribution-v1", batch, 100),
                    ).fetchone()[0]
                    rows.extend(result["users"])
            assert len(rows) == 5000
            assert [row["position"] for row in rows] == list(range(1, 5001))
            cache[locale] = rows
        return cache[locale]

    return sample
