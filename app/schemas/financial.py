from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, field_serializer


class FinancialOperationIn(BaseModel):
    amount: Decimal = Field(gt=0)
    reason: str = Field(min_length=1, max_length=500)
    is_hidden: int = Field(default=0, ge=0, le=1)


class FinancialSetIn(BaseModel):
    amount: Decimal
    reason: str = Field(min_length=1, max_length=500)
    is_hidden: int = Field(default=0, ge=0, le=1)


class FinancialOperationOut(BaseModel):
    router_name: str
    customer_id: str
    operation: str
    amount: Decimal
    reason: str
    balance_before: Decimal | None = None
    balance_after: Decimal | None = None
    audit_recorded: bool = False
    result: dict[str, Any] = Field(default_factory=dict)

    @field_serializer("amount", "balance_before", "balance_after")
    def serialize_decimal(self, value: Decimal | None) -> str | None:
        return str(value) if value is not None else None


class CreditHistoryOut(BaseModel):
    router_name: str
    customer_id: str
    start: int
    limit: int
    date_ini: str
    date_end: str
    items: list[dict[str, Any]] = Field(default_factory=list)
