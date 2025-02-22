from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.routes.deps import get_db
from app.services.pizza_service import PizzaService
from app.services.checkout_service import CheckoutService
from app.db.schemas.pizza import (
    OrderCreate, DeliveryDetails,
    PizzaResponse, SizeResponse, ToppingResponse, OrderResponse, CreateOrderResponse
)
from app.db.schemas.base import BaseResponse

router = APIRouter()

@router.get("/pizzas/", response_model=List[PizzaResponse])
def get_pizzas(db: Session = Depends(get_db)):
    try:
        return PizzaService.get_all_pizzas(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pizzas: {str(e)}")

@router.get("/sizes/", response_model=List[SizeResponse])
def get_sizes(db: Session = Depends(get_db)):
    try:
        return PizzaService.get_all_sizes(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sizes: {str(e)}")

@router.get("/toppings/", response_model=List[ToppingResponse])
def get_toppings(db: Session = Depends(get_db)):
    try:
        return PizzaService.get_all_toppings(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get toppings: {str(e)}")

@router.post("/orders/", response_model=BaseResponse)
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    try:
        created_order = PizzaService.create_order(db, order)
        return BaseResponse(
            message="Order created successfully",
            status=0,
            data=OrderResponse.model_validate(created_order)
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/orders/{order_id}/", response_model=OrderResponse)
def get_order(order_id: UUID, db: Session = Depends(get_db)):
    try:
        order = PizzaService.get_order(db, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        return BaseResponse(
            message="Order retrieved successfully",
            status=0,
            data=OrderResponse.model_validate(order)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get order: {str(e)}")

@router.post("/checkout/{order_id}/", response_model=OrderResponse)
def checkout_order(
    order_id: UUID,
    delivery_details: DeliveryDetails,
    db: Session = Depends(get_db)
):
    try:
        order = CheckoutService.process_checkout(db, order_id, delivery_details)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        return BaseResponse(
            message="Order processed successfully",
            status=0,
            data=OrderResponse.model_validate(order)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process checkout: {str(e)}")