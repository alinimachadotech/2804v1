"""Business service para saldos de clientes."""

from __future__ import annotations

import re
from decimal import Decimal

from app.core.cache import redis_get_json, redis_set_json
from app.core.settings import settings
from app.integrations.nextrouter.client import NextRouterClient
from app.integrations.nextrouter.parser import parse_money
from app.schemas.balance import CustomerBalanceOut
from app.services.router_service import get_router_secret_by_name


class RouterNotFoundError(ValueError):
    """Router nao encontrado na configuracao segura."""


def _cache_part(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.:-]+", "_", str(value).strip().lower())


def _cache_key(router_name: str, customer_id: str) -> str:
    return f"gerax:customer-balance:{_cache_part(router_name)}:{_cache_part(customer_id)}"


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


def _out_from_cached(payload: dict) -> CustomerBalanceOut:
    return CustomerBalanceOut(
        router_name=str(payload["router_name"]),
        customer_id=str(payload["customer_id"]),
        balance=parse_money(payload["balance"]),
        cached=True,
    )


def get_customer_balance(
    router_name: str,
    customer_id: str,
    *,
    use_cache: bool = True,
) -> CustomerBalanceOut:
    """Consulta saldo por router/customer_id com cache Redis opcional."""
    customer_id = str(customer_id)
    router = _get_router_or_raise(router_name)
    key = _cache_key(router.name, customer_id)

    if use_cache:
        cached = redis_get_json(key)
        if cached:
            return _out_from_cached(cached)

    payload = _build_client().get_customer_balance(router, customer_id)
    balance = payload.get("balance", Decimal("0"))

    result = CustomerBalanceOut(
        router_name=router.name,
        customer_id=str(payload.get("customer_id") or customer_id),
        balance=parse_money(balance),
        cached=False,
    )

    redis_set_json(
        key,
        result.model_dump(mode="json"),
        ttl_seconds=max(settings.balance_cache_ttl_seconds, 1),
    )

    return result
