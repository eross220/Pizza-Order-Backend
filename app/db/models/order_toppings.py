from app.db.database.base_class import Base
from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID

# Association table for order-topping many-to-many relationship
order_toppings = Table(
    'order_toppings',
    Base.metadata,
    Column('order_id', UUID(as_uuid=True), ForeignKey('orders.id')),
    Column('topping_id', UUID(as_uuid=True), ForeignKey('toppings.id'))
)