"""Saved benchmark data must remain accessible inside the deployed backend."""

import json

from fastapi.testclient import TestClient

from app.main import app
from app import web


def test_backend_bundle_serves_report_without_repository_reports(monkeypatch, tmp_path):
    backend = tmp_path / "deployment" / "backend"
    static = backend / "app" / "static"
    static.mkdir(parents=True)
    report = {
        "recorded_at": "2026-01-01T00:00:00+00:00", "postgres_version": "test",
        "environment": "packaging test fixture", "results": [],
        "parameters": {"warmup_batches": 5, "batch_size": 100},
    }
    (static / "benchmark.json").write_text(json.dumps(report), encoding="utf-8")
    monkeypatch.setattr(web, "__file__", str(backend / "app" / "web.py"))
    monkeypatch.chdir(backend)
    monkeypatch.delenv("BENCHMARK_REPORT_DIR", raising=False)
    with TestClient(app) as client:
        response = client.get("/benchmark.json")
        page = client.get("/benchmark")
    assert response.status_code == 200
    assert response.json() == report
    assert page.status_code == 200 and "packaging test fixture" in page.text


def test_explicit_report_directory_is_respected(monkeypatch, tmp_path):
    custom = tmp_path / "custom"
    monkeypatch.setenv("BENCHMARK_REPORT_DIR", str(custom))
    assert web.report_path() == custom / "benchmark.json"
    with TestClient(app) as client:
        assert client.get("/benchmark.json").status_code == 404


def test_local_report_directory_remains_available(monkeypatch, tmp_path):
    reports = tmp_path / "reports"
    reports.mkdir()
    report = {"environment": "local report fixture"}
    (reports / "benchmark.json").write_text(json.dumps(report), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("BENCHMARK_REPORT_DIR", raising=False)
    with TestClient(app) as client:
        response = client.get("/benchmark.json")
    assert response.status_code == 200 and response.json() == report
