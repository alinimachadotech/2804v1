"""Endpoints de negocio para clientes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.v1.errors import handle_service_error
from app.core.auth import require_permissions
from app.schemas.balance import CustomerBalanceOut
from app.schemas.customer import CustomerOut
from app.schemas.financial import CreditHistoryOut
from app.services.balance_service import get_customer_balance
from app.services.customer_service import get_customer
from app.services.financial_service import get_credit_history


router = APIRouter(
    prefix="/api/v1/customers",
    tags=["Customers"],
    dependencies=[Depends(require_permissions(["customers:read"]))],
)


@router.get("/{customer_id}/balance", response_model=CustomerBalanceOut)
def read_customer_balance(
    customer_id: str,
    router_name: str = Query(..., min_length=1),
):
    try:
        return get_customer_balance(router_name, customer_id)
    except Exception as exc:
        handle_service_error(exc)


@router.get("/{customer_id}", response_model=CustomerOut)
def read_customer(
    customer_id: str,
    router_name: str = Query(..., min_length=1),
):
    try:
        return get_customer(router_name, customer_id)
    except Exception as exc:
        handle_service_error(exc)


@router.get("/{customer_id}/credit-history", response_model=CreditHistoryOut)
def read_credit_history(
    customer_id: str,
    router_name: str = Query(..., min_length=1),
    date_ini: str | None = None,
    date_end: str | None = None,
    start: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    try:
        return get_credit_history(
            router_name,
            customer_id,
            date_ini=date_ini,
            date_end=date_end,
            start=start,
            limit=limit,
        )
    except Exception as exc:
        handle_service_error(exc)
