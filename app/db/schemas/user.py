
# standard library imports
from datetime import datetime
from typing import List, Optional
from uuid import UUID

# third-party imports
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from app.tools.generic import check_password
from app.db.models.user import Gender, Role, ActivationStatus
from app.db.schemas.base import BaseResponse


class BaseEmailModel(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def to_lower(cls, v: str) -> str:
        return v.lower()

class BasePasswordModel(BaseEmailModel):
    password: str
    @field_validator("password")
    @classmethod
    def validate_password(cls, v:str)-> str:
        error = check_password(v)
        if error:
            raise ValueError(error)
        return v

class BaseUserModel(BasePasswordModel):
    pass

class UserBasicOut(BaseEmailModel):
    id:UUID
    role: Role
    activation_status: ActivationStatus
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[Gender] = None
    phone_number: Optional[str] = None
    identiy_number: Optional[str] = None
    address: Optional[str] = None

class RegisterationRequest(BaseUserModel):
    first_name : str = ...
    last_name: str = ...
    gender: Optional[Gender] = None
    phone_number : Optional[str] = None  
    identity_number: Optional[str] = None
    address: Optional[str] = None

class UserLoginRequest(BaseEmailModel):
    password: str

class UserResetPasswordRequest(BasePasswordModel):
    token: str = ...

class ActivationRequest(BasePasswordModel):
    token: str = ...

class UserTokenRequest(BaseModel):
    token: str = ...

class UserTokenResponse(BaseResponse):
    access_token: str = ...
    user: UserBasicOut = ...
    refresh_token: str = ...


class UserFullResponse(BaseResponse):
    user: UserBasicOut = ...

