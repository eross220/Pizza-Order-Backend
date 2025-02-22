import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), nullable=False
    )

    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

class Serializable:
    """Serializable mixin for converting models to dictionaries."""
    
    def serialize(self, exclude_metadata: bool = False) -> dict:
        columns = [x.name for x in self.__table__.columns]
        if exclude_metadata:
            columns = [col for col in columns if col not in ("id", "created_at")]
            
        return {
            column: str(value) if isinstance(value, (uuid.UUID, datetime)) else value
            for column, value in ((col, getattr(self, col)) for col in columns)
        }
