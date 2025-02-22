from fastapi import APIRouter
from app.routes.v1 import pizza

api_router = APIRouter()
api_router.include_router(pizza.router, tags=["pizza"])