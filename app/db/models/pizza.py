from app.db.database.base_class import Serializable, Base
from sqlalchemy import Column, String, Float
from sqlalchemy.orm import relationship, mapped_column, Mapped, Session

class Pizza(Base, Serializable):
    __tablename__ = "pizzas"

    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    base_price: Mapped[float] = mapped_column(Float, nullable=False)
    image: Mapped[str] = mapped_column(String, nullable=True)

    # Add relationship back to Order
    orders = relationship("Order", back_populates="pizza") 