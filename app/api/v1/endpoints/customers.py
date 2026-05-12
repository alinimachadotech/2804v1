"""Endpoints de negocio para clientes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.integrations.nextrouter.exceptions import (
    NextRouterAuthError,
    NextRouterBadRequestError,
    NextRouterError,
    NextRouterNotFoundError,
    NextRouterPayloadTooLargeError,
    NextRouterRateLimitError,
    NextRouterServerError,
    NextRouterTimeoutError,
    NextRouterValidationError,
)
from app.schemas.balance import CustomerBalanceOut
from app.schemas.customer import CustomerOut, CustomerStatusChangeOut
from app.schemas.financial import (
    CreditHistoryOut,
    FinancialOperationIn,
    FinancialOperationOut,
)
from app.services.balance_service import (
    RouterNotFoundError,
    get_customer_balance,
)
from app.services.customer_service import (
    activate_customer,
    deactivate_customer,
    get_customer,
)
from app.services.financial_service import (
    FinancialValidationError,
    InsufficientBalanceError,
    credit_customer,
    debit_customer,
    get_credit_history,
)


router = APIRouter(prefix="/api/v1/customers", tags=["Customers"])


def _handle_error(exc: Exception):
    if isinstance(exc, RouterNotFoundError):
        raise HTTPException(status_code=404, detail="Router nao encontrado")
    if isinstance(exc, InsufficientBalanceError):
        raise HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, FinancialValidationError):
        raise HTTPException(status_code=422, detail=str(exc))
    if isinstance(exc, NextRouterAuthError):
        raise HTTPException(status_code=401, detail="Falha de autenticacao com NextRouter")
    if isinstance(exc, NextRouterBadRequestError):
        raise HTTPException(status_code=400, detail="Requisicao invalida para NextRouter")
    if isinstance(exc, NextRouterNotFoundError):
        raise HTTPException(status_code=404, detail="Recurso nao encontrado no NextRouter")
    if isinstance(exc, NextRouterPayloadTooLargeError):
        raise HTTPException(status_code=413, detail="Payload grande demais para NextRouter")
    if isinstance(exc, NextRouterValidationError):
        raise HTTPException(status_code=422, detail="NextRouter recusou a validacao")
    if isinstance(exc, NextRouterRateLimitError):
        raise HTTPException(status_code=429, detail="Rate limit do NextRouter excedido")
    if isinstance(exc, NextRouterTimeoutError):
        raise HTTPException(status_code=504, detail="Timeout ao comunicar com NextRouter")
    if isinstance(exc, NextRouterServerError):
        raise HTTPException(status_code=502, detail="Erro 5xx do NextRouter")
    if isinstance(exc, NextRouterError):
        raise HTTPException(status_code=502, detail="Erro ao comunicar com NextRouter")
    raise exc


@router.get("/{customer_id}/balance", response_model=CustomerBalanceOut)
def read_customer_balance(
    customer_id: str,
    router_name: str = Query(..., min_length=1),
):
    try:
        return get_customer_balance(router_name, customer_id)
    except Exception as exc:
        _handle_error(exc)


@router.get("/{customer_id}", response_model=CustomerOut)
def read_customer(
    customer_id: str,
    router_name: str = Query(..., min_length=1),
):
    try:
        return get_customer(router_name, customer_id)
    except Exception as exc:
        _handle_error(exc)


@router.post("/{customer_id}/activate", response_model=CustomerStatusChangeOut)
def activate_customer_endpoint(
    customer_id: str,
    router_name: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    try:
        return activate_customer(router_name, customer_id, db=db)
    except Exception as exc:
        _handle_error(exc)


@router.post("/{customer_id}/deactivate", response_model=CustomerStatusChangeOut)
def deactivate_customer_endpoint(
    customer_id: str,
    router_name: str = Query(..., min_length=1),
    confirm: bool = Query(False),
    db: Session = Depends(get_db),
):
    try:
        return deactivate_customer(router_name, customer_id, confirm=confirm, db=db)
    except Exception as exc:
        _handle_error(exc)


@router.post("/{customer_id}/credit", response_model=FinancialOperationOut)
def credit_customer_endpoint(
    customer_id: str,
    payload: FinancialOperationIn,
    router_name: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    try:
        return credit_customer(
            router_name,
            customer_id,
            payload.amount,
            payload.reason,
            is_hidden=payload.is_hidden,
            db=db,
        )
    except Exception as exc:
        _handle_error(exc)


@router.post("/{customer_id}/debit", response_model=FinancialOperationOut)
def debit_customer_endpoint(
    customer_id: str,
    payload: FinancialOperationIn,
    router_name: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    try:
        return debit_customer(
            router_name,
            customer_id,
            payload.amount,
            payload.reason,
            is_hidden=payload.is_hidden,
            db=db,
        )
    except Exception as exc:
        _handle_error(exc)


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
        _handle_error(exc)
