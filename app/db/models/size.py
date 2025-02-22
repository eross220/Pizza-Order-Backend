from app.db.database.base_class import Base, Serializable
from sqlalchemy import Column, String, Float
from sqlalchemy.orm import relationship, mapped_column, Mapped, Session

class Size(Base, Serializable):
    __tablename__ = "sizes"

    name: Mapped[str] = mapped_column(String, nullable=False)
    multiplier: Mapped[float] = mapped_column(Float, nullable=False)

    # Add relationship back to Order
    orders = relationship("Order", back_populates="size") 