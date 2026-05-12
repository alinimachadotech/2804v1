from decimal import Decimal

from pydantic import BaseModel, field_serializer


class CustomerBalanceOut(BaseModel):
    router_name: str
    customer_id: str
    balance: Decimal
    cached: bool = False

    @field_serializer("balance")
    def serialize_balance(self, value: Decimal) -> str:
        return str(value)
