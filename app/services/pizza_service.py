from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.db.models.pizza import Pizza
from app.db.models.size import Size
from app.db.models.topping import Topping
from app.db.models.order import Order
from app.db.schemas.pizza import OrderCreate

class PizzaService:
    @staticmethod
    def get_all_pizzas(db: Session) -> List[Pizza]:
        return db.query(Pizza).all()
    
    @staticmethod
    def get_all_sizes(db: Session) -> List[Size]:
        return db.query(Size).all()
    
    @staticmethod
    def get_all_toppings(db: Session) -> List[Topping]:
        return db.query(Topping).all()
    
    @staticmethod
    def create_order(db: Session, order_data: OrderCreate) -> Order:
        try:
            print(order_data)
            # Get pizza and size
            pizza = db.query(Pizza).get(order_data.pizza_id)
            size = db.query(Size).get(order_data.size_id)
            toppings = db.query(Topping).filter(Topping.id.in_(order_data.topping_ids)).all()
            
            # Calculate total price
            base_price = pizza.base_price * size.multiplier
            toppings_price = sum(topping.price for topping in toppings)
            total_price = base_price + toppings_price
            
            # Create order
            order = Order(
                customer_name=order_data.customer_name,
                phone_number=order_data.phone_number,
                address=order_data.address,
                pizza_id=order_data.pizza_id,
                size_id=order_data.size_id,
                payment_method=order_data.payment_method,
                total_price=total_price
            )        
            db.add(order)
            db.commit()
            db.refresh(order)
            
            return order
        except Exception as e:
            raise Exception(f"Failed to create order: {str(e)}")
    
    @staticmethod
    def get_order(db: Session, order_id: UUID) -> Order:
        return db.query(Order).filter(Order.id == order_id).first() 