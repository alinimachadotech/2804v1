from typing import Any

from pydantic import BaseModel, Field


class CustomerOut(BaseModel):
    router_name: str
    customer_id: str
    name: str | None = None
    status: str | int | bool | None = None
    is_active: bool | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    cached: bool = False
