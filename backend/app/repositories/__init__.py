"""Repository abstractions for database access."""

from app.repositories.base import BaseRepository
from app.repositories.crud import CRUDRepository

__all__ = [
    "BaseRepository",
    "CRUDRepository",
]
