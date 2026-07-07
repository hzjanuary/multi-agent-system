"""Generic CRUD repository implementation."""

from collections.abc import Sequence
from typing import Any

from sqlalchemy import select

from app.db import Base
from app.repositories.base import BaseRepository


class CRUDRepository[ModelT: Base](BaseRepository[ModelT]):
    """Reusable async CRUD operations for SQLAlchemy models.

    The repository never creates sessions and never commits transactions.
    Callers own transaction boundaries and decide when to flush or commit.
    """

    async def get(self, id_: object) -> ModelT | None:
        """Return one model by primary key, or None when not found."""
        return await self.session.get(self.model_type, id_)

    async def list(self, *, limit: int = 100, offset: int = 0) -> Sequence[ModelT]:
        """Return models ordered by the database default order."""
        statement = select(self.model_type).limit(limit).offset(offset)
        result = await self.session.scalars(statement)
        return result.all()

    def add(self, model: ModelT) -> ModelT:
        """Add a model to the current session without committing."""
        self.session.add(model)
        return model

    async def delete(self, model: ModelT) -> None:
        """Mark a model for deletion without committing."""
        await self.session.delete(model)

    async def refresh(self, model: ModelT) -> None:
        """Refresh a model from the database."""
        await self.session.refresh(model)

    def update_fields(self, model: ModelT, values: dict[str, Any]) -> ModelT:
        """Assign field values to a model without flushing or committing."""
        for field_name, value in values.items():
            setattr(model, field_name, value)
        return model
