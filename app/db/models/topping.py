from sqlalchemy import Column, String, Float
from sqlalchemy.orm import relationship, mapped_column, Mapped, Session
from app.db.database.base_class import Serializable, Base

class Topping(Base, Serializable):
    __tablename__ = "toppings"

    name: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    icon: Mapped[str] = mapped_column(String, nullable=True) 