"""Tests for middleware and exception handling."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.middleware import REQUEST_ID_HEADER


def build_test_app() -> FastAPI:
    app = create_app(Settings(_env_file=None))

    @app.get("/ok")
    async def ok() -> dict[str, bool]:
        return {"ok": True}

    @app.get("/boom")
    async def boom() -> None:
        raise RuntimeError("boom")

    return app


def test_request_without_request_id_receives_generated_request_id() -> None:
    client = TestClient(build_test_app())

    response = client.get("/ok")

    assert response.status_code == 200
    assert response.headers[REQUEST_ID_HEADER]


def test_request_with_request_id_preserves_provided_value() -> None:
    client = TestClient(build_test_app())
    request_id = "test-request-id"

    response = client.get("/ok", headers={REQUEST_ID_HEADER: request_id})

    assert response.status_code == 200
    assert response.headers[REQUEST_ID_HEADER] == request_id


def test_unhandled_exception_returns_structured_error_response() -> None:
    client = TestClient(build_test_app(), raise_server_exceptions=False)
    request_id = "error-request-id"

    response = client.get("/boom", headers={REQUEST_ID_HEADER: request_id})

    assert response.status_code == 500
    assert response.headers[REQUEST_ID_HEADER] == request_id
    assert response.json() == {
        "success": False,
        "data": None,
        "error": {
            "code": "internal_server_error",
            "message": "Internal server error",
            "details": {},
        },
        "request_id": request_id,
    }
