"""Business service para operacoes financeiras NextRouter."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from app.core.settings import settings
from app.integrations.nextrouter.client import NextRouterClient
from app.integrations.nextrouter.parser import parse_money
from app.schemas.financial import CreditHistoryOut, FinancialOperationOut
from app.services.audit_service import record_audit_action, sanitize_payload
from app.services.balance_service import (
    RouterNotFoundError,
    get_customer_balance,
)
from app.services.router_service import get_router_secret_by_name


class FinancialValidationError(ValueError):
    """Dados financeiros invalidos."""


class InsufficientBalanceError(FinancialValidationError):
    """Saldo insuficiente para debito."""


def _get_router_or_raise(router_name: str):
    router = get_router_secret_by_name(router_name)
    if router is None:
        raise RouterNotFoundError("Router nao encontrado")
    return router


def _build_client() -> NextRouterClient:
    return NextRouterClient(
        timeout=settings.nextrouter_timeout_seconds,
        verify_ssl=settings.nextrouter_verify_ssl,
    )


def _require_reason(reason: str) -> str:
    normalized = (reason or "").strip()
    if not normalized:
        raise FinancialValidationError("reason e obrigatorio")
    return normalized


def _require_positive_amount(amount: Any) -> Decimal:
    parsed = parse_money(amount, default=None)
    if parsed <= 0:
        raise FinancialValidationError("amount deve ser maior que zero")
    return parsed


def _execute_operation(
    *,
    router_name: str,
    customer_id: str,
    amount: Any,
    operation: str,
    reason: str,
    is_hidden: int = 0,
    db=None,
) -> FinancialOperationOut:
    customer_id = str(customer_id)
    router = _get_router_or_raise(router_name)
    parsed_amount = _require_positive_amount(amount)
    normalized_reason = _require_reason(reason)

    before = get_customer_balance(router.name, customer_id, use_cache=False)

    if operation == "debit" and before.balance < parsed_amount:
        raise InsufficientBalanceError("Saldo insuficiente para debito")

    result = sanitize_payload(
        _build_client().manage_credit(
            router,
            customer_id,
            parsed_amount,
            operation,
            normalized_reason,
            is_hidden=is_hidden,
        )
    )

    balance_after = None
    try:
        balance_after = get_customer_balance(router.name, customer_id, use_cache=False).balance
    except Exception:
        balance_after = None

    audit_recorded = record_audit_action(
        action=f"financial.{operation}",
        router_name=router.name,
        customer_id=customer_id,
        before={"balance": str(before.balance)},
        after={"balance": str(balance_after) if balance_after is not None else None, "result": result},
        metadata={"amount": str(parsed_amount), "reason": normalized_reason},
        db=db,
    )

    return FinancialOperationOut(
        router_name=router.name,
        customer_id=customer_id,
        operation=operation,
        amount=parsed_amount,
        reason=normalized_reason,
        balance_before=before.balance,
        balance_after=balance_after,
        audit_recorded=audit_recorded,
        result=result if isinstance(result, dict) else {"response": result},
    )


def credit_customer(
    router_name: str,
    customer_id: str,
    amount: Any,
    reason: str,
    *,
    is_hidden: int = 0,
    db=None,
) -> FinancialOperationOut:
    return _execute_operation(
        router_name=router_name,
        customer_id=customer_id,
        amount=amount,
        operation="credit",
        reason=reason,
        is_hidden=is_hidden,
        db=db,
    )


def debit_customer(
    router_name: str,
    customer_id: str,
    amount: Any,
    reason: str,
    *,
    is_hidden: int = 0,
    db=None,
) -> FinancialOperationOut:
    return _execute_operation(
        router_name=router_name,
        customer_id=customer_id,
        amount=amount,
        operation="debit",
        reason=reason,
        is_hidden=is_hidden,
        db=db,
    )


def set_customer_credit(
    router_name: str,
    customer_id: str,
    amount: Any,
    reason: str,
    *,
    is_hidden: int = 0,
    db=None,
) -> FinancialOperationOut:
    return _execute_operation(
        router_name=router_name,
        customer_id=customer_id,
        amount=amount,
        operation="set",
        reason=reason,
        is_hidden=is_hidden,
        db=db,
    )


def get_credit_history(
    router_name: str,
    customer_id: str,
    *,
    date_ini: str | None = None,
    date_end: str | None = None,
    start: int = 0,
    limit: int = 100,
) -> CreditHistoryOut:
    customer_id = str(customer_id)
    router = _get_router_or_raise(router_name)

    if date_end is None:
        date_end = date.today().isoformat()
    if date_ini is None:
        date_ini = (date.fromisoformat(date_end) - timedelta(days=30)).isoformat()

    start = max(start, 0)
    limit = max(limit, 1)

    items = sanitize_payload(
        _build_client().get_credit_history(
            router,
            customer_id,
            date_ini,
            date_end,
            start=start,
            limit=limit,
        )
    )

    return CreditHistoryOut(
        router_name=router.name,
        customer_id=customer_id,
        start=start,
        limit=limit,
        date_ini=date_ini,
        date_end=date_end,
        items=items if isinstance(items, list) else [],
    )
