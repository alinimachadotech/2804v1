from typing import Any

from pydantic import BaseModel, Field


class CreditHistoryOut(BaseModel):
    router_name: str
    customer_id: str
    start: int
    limit: int
    date_ini: str
    date_end: str
    items: list[dict[str, Any]] = Field(default_factory=list)
    cached: bool = False
