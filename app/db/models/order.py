from sqlalchemy import Column, String, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.db.models.order_toppings import order_toppings
from app.db.database.base_class import Base, Serializable
from enum import Enum

class PaymentMethod(str, Enum):
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"

class Order(Base, Serializable):
    __tablename__ = "orders"
    
    customer_name: Mapped[str] = mapped_column(String, nullable=False)
    phone_number: Mapped[str] = mapped_column(String, nullable=False)
    address: Mapped[str] = mapped_column(String, nullable=False)
    pizza_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("pizzas.id"))
    size_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sizes.id"))
    payment_method: Mapped[str] = mapped_column(SQLEnum(PaymentMethod), nullable=False)
    total_price: Mapped[float] = mapped_column(Float, nullable=False)

    # Relationships
    pizza = relationship("Pizza", back_populates="orders")
    size = relationship("Size", back_populates="orders")
    toppings = relationship("Topping", secondary=order_toppings, backref="orders", cascade="all, delete")

    def calculate_total_price(self) -> float:
        """Calculate the total price of an order including pizza, size and toppings"""
        total = self.pizza.base_price * self.size.multiplier
        if self.toppings:
            total += sum(topping.price for topping in self.toppings)
        return total