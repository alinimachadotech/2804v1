from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, field_serializer


class CustomerOut(BaseModel):
    router_name: str
    customer_id: str
    name: str | None = None
    status: str | int | bool | None = None
    is_active: bool | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    cached: bool = False


class CustomerDeactivateImpactOut(BaseModel):
    router_name: str
    customer_id: str
    current_status: str | int | bool | None = None
    current_balance: Decimal | None = None
    will_block_customer: bool = True
    balance_will_be_preserved: bool = True
    active_calls_impact: str = "unknown"
    requires_confirm: bool = True

    @field_serializer("current_balance")
    def serialize_current_balance(self, value: Decimal | None) -> str | None:
        return str(value) if value is not None else None


class CustomerStatusChangeOut(BaseModel):
    router_name: str
    customer_id: str
    action: str
    requested_status: str | int | bool
    previous_status: str | int | bool | None = None
    action_executed: bool
    message: str
    impact: CustomerDeactivateImpactOut | None = None
    audit_recorded: bool = False
    result: dict[str, Any] = Field(default_factory=dict)
