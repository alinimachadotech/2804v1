from typing import List, Optional

from pydantic import BaseModel


class UserLogin(BaseModel):
    email: str
    password: str


class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    user_type: str
    role: str
    customer_id: Optional[int] = None
    is_active: bool = True


class UserRead(BaseModel):
    id: int
    name: str
    email: str
    user_type: str
    role: str
    is_active: bool
    customer_id: Optional[int] = None

    class Config:
        orm_mode = True
        from_attributes = True


class CurrentUser(BaseModel):
    id: int
    name: str
    email: str
    user_type: str
    role: str
    permissions: List[str]
    customer_id: Optional[int] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: CurrentUser