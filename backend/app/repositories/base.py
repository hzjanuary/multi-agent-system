"""Base repository primitives."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Base


class BaseRepository[ModelT: Base]:
    """Base class for repositories using caller-owned async sessions."""

    def __init__(self, session: AsyncSession, model_type: type[ModelT]) -> None:
        self.session = session
        self.model_type = model_type
