"""
Generic Base Repository Interface pattern.

Provides basic CRUD signatures to ensure strict separation of concerns
between the data layer and domain business logic.
"""

from typing import Any, Generic, List, Optional, Type, TypeVar
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Base repository implementing standard CRUD operations asynchronously.
    """

    def __init__(self, model: Type[ModelType]) -> None:
        self.model = model

    async def get(
        self,
        db_session: AsyncSession,
        id: Any,
    ) -> Optional[ModelType]:
        """
        Fetch a record by primary key ID.
        """
        query = select(self.model).where(self.model.id == id)
        result = await db_session.execute(query)
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        db_session: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ModelType]:
        """
        Fetch multiple paginated records.
        """
        query = select(self.model).offset(skip).limit(limit)
        result = await db_session.execute(query)
        return list(result.scalars().all())

    async def create(
        self,
        db_session: AsyncSession,
        *,
        obj_in: dict,
    ) -> ModelType:
        """
        Insert a new model entity.
        """
        db_obj = self.model(**obj_in)
        db_session.add(db_obj)
        await db_session.commit()
        await db_session.refresh(db_obj)
        return db_obj

    async def delete(
        self,
        db_session: AsyncSession,
        *,
        id: Any,
    ) -> Optional[ModelType]:
        """
        Delete a record by ID.
        """
        db_obj = await self.get(db_session, id)
        if db_obj:
            await db_session.delete(db_obj)
            await db_session.commit()
        return db_obj
