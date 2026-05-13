from decimal import Decimal

from pydantic import BaseModel, field_serializer


class CustomerBalanceOut(BaseModel):
    router_name: str
    customer_id: str
    balance: Decimal
    usable_balance: Decimal | None = None
    customer_balance: Decimal | None = None
    customer_limit: Decimal | None = None
    tipo_tar: int | str | None = None
    cached: bool = False

    @field_serializer("balance", "usable_balance", "customer_balance", "customer_limit")
    def serialize_decimal(self, value: Decimal | None) -> str | None:
        return str(value) if value is not None else None
