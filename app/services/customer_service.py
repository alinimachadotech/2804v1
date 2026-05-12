"""Business service read-only para cadastro de clientes."""

from __future__ import annotations

import re
from typing import Any

from app.core.cache import redis_get_json, redis_set_json
from app.core.settings import settings
from app.integrations.nextrouter.client import NextRouterClient
from app.schemas.customer import CustomerOut
from app.services.audit_service import sanitize_payload
from app.services.balance_service import RouterNotFoundError
from app.services.router_service import get_router_secret_by_name


def _cache_part(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.:-]+", "_", str(value).strip().lower())


def _cache_key(router_name: str, customer_id: str) -> str:
    return f"gerax:customer:{_cache_part(router_name)}:{_cache_part(customer_id)}"


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


def _status_to_active(status: Any) -> bool | None:
    if status is None:
        return None
    normalized = str(status).strip().lower()
    if normalized in {"1", "true", "active", "ativo", "enabled", "habilitado"}:
        return True
    if normalized in {"0", "false", "inactive", "inativo", "disabled", "desabilitado", "bloqueado"}:
        return False
    return None


def _customer_out(
    *,
    router_name: str,
    customer_id: str,
    payload: dict[str, Any],
    cached: bool = False,
) -> CustomerOut:
    raw = sanitize_payload(payload.get("raw") or payload)
    resolved_customer_id = payload.get("customer_id") or raw.get("id_cliente") or customer_id
    status = payload.get("status")

    return CustomerOut(
        router_name=router_name,
        customer_id=str(resolved_customer_id),
        name=payload.get("name"),
        status=status,
        is_active=_status_to_active(status),
        data=raw if isinstance(raw, dict) else {},
        cached=cached,
    )


def get_customer(
    router_name: str,
    customer_id: str,
    *,
    use_cache: bool = True,
) -> CustomerOut:
    """Consulta cadastro do cliente com cache Redis opcional."""
    customer_id = str(customer_id)
    router = _get_router_or_raise(router_name)
    key = _cache_key(router.name, customer_id)

    if use_cache:
        cached = redis_get_json(key)
        if cached:
            return CustomerOut(**cached, cached=True)

    payload = _build_client().get_customer(router, customer_id)
    result = _customer_out(
        router_name=router.name,
        customer_id=customer_id,
        payload=payload,
        cached=False,
    )

    redis_set_json(
        key,
        result.model_dump(mode="json"),
        ttl_seconds=max(settings.customer_cache_ttl_seconds, 1),
    )

    return result
