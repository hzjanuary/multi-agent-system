"""Smoke tests for the FastAPI application skeleton."""

from fastapi import FastAPI

from app.main import app, create_app


def test_app_can_be_imported() -> None:
    assert isinstance(app, FastAPI)
    assert app.title == "Multi-Agent OS"


def test_app_factory_creates_fastapi_instance() -> None:
    created_app = create_app()

    assert isinstance(created_app, FastAPI)
    assert created_app.version == "0.2.0"
