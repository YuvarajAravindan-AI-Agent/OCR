"""Auth and limit enforcement at the HTTP layer.

These never reach the model: requests are rejected before OcrPipeline is
constructed, so they run fine without a GPU.

Settings are injected via dependency_overrides rather than environment
variables, so the developer's real src/ocr_pipeline/.env cannot influence
the results.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from ocr_pipeline.api import app
from ocr_pipeline.config import Settings, get_settings


@pytest.fixture
def client():
    yield TestClient(app)
    app.dependency_overrides.clear()


def configure(**kwargs) -> None:
    base = {
        "api_key": "test-key",
        "require_api_key": True,
        "device": "cpu",
        "max_pages": 10,
        "max_upload_bytes": 1024,
        "max_dpi": 400,
    }
    base.update(kwargs)
    settings = Settings(**base)
    app.dependency_overrides[get_settings] = lambda: settings


def test_healthz_needs_no_key(client):
    configure()
    assert client.get("/healthz").json() == {"status": "ok"}


def test_limits_endpoint_publishes_caps(client):
    configure()
    body = client.get("/v1/limits").json()
    assert body["max_pages"] == 10
    assert body["max_upload_bytes"] == 1024
    assert body["max_dpi"] == 400
    assert body["api_key_required"] is True


class TestAuth:
    def test_rejects_missing_key(self, client):
        configure()
        r = client.post("/v1/ocr/image", files={"file": ("a.png", b"x", "image/png")})
        assert r.status_code == 401

    def test_rejects_wrong_key(self, client):
        configure()
        r = client.post(
            "/v1/ocr/image",
            files={"file": ("a.png", b"x", "image/png")},
            headers={"X-API-Key": "wrong"},
        )
        assert r.status_code == 401

    def test_refuses_to_run_open_when_key_unset(self, client):
        # require_api_key on but no key configured -> fail closed, not open.
        configure(api_key=None)
        r = client.post("/v1/ocr/image", files={"file": ("a.png", b"x", "image/png")})
        assert r.status_code == 500
        assert "misconfigured" in r.json()["detail"]

    def test_can_be_disabled_for_local_dev(self, client):
        configure(require_api_key=False, api_key=None)
        # Passes auth, then fails on the empty-file check rather than 401.
        r = client.post("/v1/ocr/image", files={"file": ("a.png", b"", "image/png")})
        assert r.status_code != 401


class TestLimitsEnforced:
    def test_oversized_upload_rejected_with_413(self, client):
        configure(max_upload_bytes=1024)
        r = client.post(
            "/v1/ocr/image",
            files={"file": ("big.png", b"x" * 5000, "image/png")},
            headers={"X-API-Key": "test-key"},
        )
        assert r.status_code == 413
        assert "exceeds" in r.json()["detail"]

    def test_empty_upload_rejected(self, client):
        configure()
        r = client.post(
            "/v1/ocr/image",
            files={"file": ("a.png", b"", "image/png")},
            headers={"X-API-Key": "test-key"},
        )
        assert r.status_code == 413

    def test_bad_mode_rejected(self, client):
        configure()
        r = client.post(
            "/v1/ocr/image",
            files={"file": ("a.png", b"x", "image/png")},
            headers={"X-API-Key": "test-key"},
            params={"mode": "nonsense"},
        )
        assert r.status_code == 422

    def test_excessive_dpi_rejected(self, client):
        configure()
        r = client.post(
            "/v1/ocr/pdf",
            files={"file": ("a.pdf", b"%PDF-1.4", "application/pdf")},
            headers={"X-API-Key": "test-key"},
            params={"dpi": 2400},
        )
        assert r.status_code == 413

    def test_page_heavy_pdf_rejected_before_rasterising(self, client, tmp_path):
        import fitz

        configure(max_pages=5, max_upload_bytes=10 * 1024 * 1024)
        doc = fitz.open()
        for n in range(30):
            doc.new_page().insert_text((72, 72), f"page {n}")
        pdf = tmp_path / "many.pdf"
        doc.save(str(pdf))
        doc.close()

        r = client.post(
            "/v1/ocr/pdf",
            files={"file": ("many.pdf", pdf.read_bytes(), "application/pdf")},
            headers={"X-API-Key": "test-key"},
        )
        assert r.status_code == 413
        assert "30 pages; limit is 5" in r.json()["detail"]
