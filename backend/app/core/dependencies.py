"""Application dependency helpers."""

from app.config import Settings, get_settings


def provide_settings() -> Settings:
    """Provide typed application settings for dependency injection."""
    return get_settings()
