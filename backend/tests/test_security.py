import asyncio
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import httpx
import pytest
from fastapi.testclient import TestClient
from openpyxl import load_workbook

from app.core.config import settings
from app.main import app
from app.services import ai_classifier
from app.services.export_workbook import _build_workbook
from app.services.workbook_safety import validate_workbook

TOKEN = "test-only-access-token-" * 3


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(settings, "api_access_token", TOKEN)
    monkeypatch.setattr(settings, "allow_uploads", False)
    app.middleware_stack = None
    with TestClient(app) as client:
        yield client


def auth():
    return {"Authorization": f"Bearer {TOKEN}"}


@pytest.mark.parametrize("path", ["/api/bookings", "/api/bookings/export", "/api/uploads", "/api/agents", "/api/errors", "/api/dashboard", "/api/filters", "/api/ai/status", "/docs", "/openapi.json"])
def test_all_data_requires_token(client, path):
    assert client.get(path).status_code == 401
    assert client.get(path, headers={"Authorization": "Bearer incorrect"}).status_code == 401


def test_health_is_public_but_missing_configuration_fails_closed(client, monkeypatch):
    assert client.get("/health").status_code == 200
    monkeypatch.setattr(settings, "api_access_token", "")
    assert client.get("/api/session", headers=auth()).status_code == 503


def test_authenticated_session_and_no_cache(client):
    response = client.get("/api/session", headers=auth())
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"


def test_upload_rejected_before_multipart_parsing(client):
    headers = {"Content-Type": "multipart/form-data; boundary=broken"}
    assert client.post("/api/uploads", content=b"invalid", headers=headers).status_code == 401
    assert client.post("/api/uploads", content=b"invalid", headers=headers | auth()).status_code == 403


def test_chunked_body_size_limit(client, monkeypatch):
    monkeypatch.setattr(settings, "allow_uploads", True)
    monkeypatch.setattr(settings, "max_upload_mb", 0)
    response = client.post("/api/uploads", content=iter([b"x" * 40000, b"x" * 40000]), headers=auth())
    assert response.status_code == 413


def test_failed_auth_rate_limit(client):
    for _ in range(30):
        assert client.get("/api/session").status_code == 401
    assert client.get("/api/session").status_code == 429
    # Invalid attempts do not lock the correctly authenticated operator out.
    assert client.get("/api/session", headers=auth()).status_code == 200


def workbook_zip(xml):
    output = BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr("xl/worksheets/sheet1.xml", xml)
    return output.getvalue()


def test_rejects_expanded_zip(monkeypatch):
    monkeypatch.setattr(settings, "max_expanded_mb", 1)
    content = workbook_zip(b"x" * (1024 * 1024 + 1))
    with pytest.raises(ValueError, match="expanded size"):
        validate_workbook(content)


def test_rejects_sparse_row_and_column_abuse(monkeypatch):
    monkeypatch.setattr(settings, "max_workbook_rows", 10)
    with pytest.raises(ValueError, match="row count"):
        validate_workbook(workbook_zip('<worksheet><row r="999999"/></worksheet>'))
    with pytest.raises(ValueError, match="column count"):
        validate_workbook(workbook_zip('<worksheet><row r="1"><c r="XFD1"/></row></worksheet>'))


def test_rejects_xml_entities():
    xml = '<!DOCTYPE a [<!ENTITY secret "sensitive">]><worksheet><row>&secret;</row></worksheet>'
    with pytest.raises(ValueError):
        validate_workbook(workbook_zip(xml))


def test_export_never_creates_formulas():
    content = _build_workbook("Demo", ["Text"], [['=HYPERLINK("https://example.invalid", "click")']], [30])
    cell = load_workbook(BytesIO(content)).active["A2"]
    assert cell.data_type == "s"
    assert cell.value.startswith("=HYPERLINK")


def test_external_ai_requires_explicit_opt_in(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "test-placeholder")
    monkeypatch.setattr(settings, "gemini_model", "test-model")
    monkeypatch.setattr(settings, "allow_external_ai", False)
    assert not ai_classifier.ai_enabled()


def test_provider_uses_header_and_redacts_failure(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "test-placeholder")
    monkeypatch.setattr(settings, "gemini_model", "test-model")
    monkeypatch.setattr(settings, "allow_external_ai", True)
    class Provider:
        def __init__(self, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def post(self, url, **kwargs):
            assert "params" not in kwargs
            assert kwargs["headers"] == {"x-goog-api-key": "test-placeholder"}
            return httpx.Response(403, request=httpx.Request("POST", url), text="private provider diagnostic")
    monkeypatch.setattr(ai_classifier.httpx, "AsyncClient", Provider)
    with pytest.raises(RuntimeError) as error:
        asyncio.run(ai_classifier.classify_issue("Invented example issue"))
    assert str(error.value) == "AI provider request failed. Try again later."


def test_upload_and_export_workflow_uses_authorized_synthetic_data(client, monkeypatch):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from sqlalchemy.pool import StaticPool
    from app.db.base import Base
    from app.db.session import get_db
    from test_excel_parser import workbook_bytes
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    def test_db():
        with Session(engine) as db:
            yield db
    app.dependency_overrides[get_db] = test_db
    monkeypatch.setattr(settings, "allow_uploads", True)
    try:
        response = client.post("/api/uploads?replace=true", headers=auth(), files={"file": ("fictional.xlsx", workbook_bytes())})
        assert response.status_code == 200, response.text
        assert response.json()["bookingCount"] == 1
        for path in ["/api/bookings", "/api/errors", "/api/dashboard", "/api/agents", "/api/filters"]:
            assert client.get(path, headers=auth()).status_code == 200
        export = client.get("/api/bookings/export", headers=auth())
        assert export.status_code == 200
        assert load_workbook(BytesIO(export.content)).active.max_row == 2
        assert client.get("/api/bookings/export").status_code == 401
        assert client.post("/api/uploads", files={"file": ("fictional.xlsx", workbook_bytes())}).status_code == 401
        assert len(client.get("/api/uploads", headers=auth()).json()) == 1
    finally:
        app.dependency_overrides.clear()
        engine.dispose()
