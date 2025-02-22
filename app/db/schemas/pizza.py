from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
from app.db.models.order import PaymentMethod
from enum import Enum
from uuid import UUID
from app.db.schemas.base import BaseResponse

class OrderStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"

class PizzaBase(BaseModel):
    name: str
    description: Optional[str]
    base_price: float
    image: Optional[str]

class PizzaResponse(PizzaBase):
    id: UUID

    class Config:
        from_attributes = True

class SizeBase(BaseModel):
    name: str
    multiplier: float

class SizeResponse(SizeBase):
    id: UUID

    class Config:
        from_attributes = True

class ToppingBase(BaseModel):
    name: str
    price: float
    icon: Optional[str]

class ToppingResponse(ToppingBase):
    id: UUID

    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    customer_name: str
    phone_number: str
    address: str
    pizza_id: UUID
    size_id: UUID
    topping_ids: List[UUID]
    payment_method: PaymentMethod

class DeliveryDetails(BaseModel):
    name: str
    address: str
    phone: str
    email: Optional[EmailStr]
    payment_method: PaymentMethod
    special_instructions: Optional[str]

class OrderResponse(BaseModel):
    id: UUID
    customer_name: str
    phone_number: str
    address: str
    pizza_id: UUID
    size_id: UUID
    payment_method: PaymentMethod
    total_price: float
    
    class Config:
        from_attributes = True

class CreateOrderResponse(BaseResponse):
    data: Optional[OrderResponse] = None



