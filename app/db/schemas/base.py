from typing import TypeVar, Optional, Generic, Any
from pydantic import BaseModel, Field

DataT = TypeVar("DataT")

class BaseResponse(BaseModel, Generic[DataT]):
    """Base response model for API endpoints."""
    
    message: str = Field(..., description="Response message")
    status: int = Field(..., ge=100, le=599, description="HTTP status code")
    data: Optional[DataT] = Field(None, description="Response data")
