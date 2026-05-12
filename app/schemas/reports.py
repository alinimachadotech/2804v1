from typing import Any

from pydantic import BaseModel, Field


class ReadOnlyQueryOut(BaseModel):
    router_name: str
    customer_id: str | None = None
    start: int = 0
    limit: int = 100
    filters: dict[str, Any] = Field(default_factory=dict)
    data: Any
    cached: bool = False
