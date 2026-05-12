"""Business service para cadastro e status de clientes."""

from __future__ import annotations

import re
from typing import Any

from app.core.cache import redis_get_json, redis_set_json
from app.core.settings import settings
from app.integrations.nextrouter.client import NextRouterClient
from app.schemas.customer import (
    CustomerDeactivateImpactOut,
    CustomerOut,
    CustomerStatusChangeOut,
)
from app.services.audit_service import record_audit_action, sanitize_payload
from app.services.balance_service import (
    RouterNotFoundError,
    get_customer_balance,
)
from app.services.router_service import get_router_secret_by_name


ACTIVE_STATUS = 1
INACTIVE_STATUS = 0


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


def get_deactivation_impact(router_name: str, customer_id: str) -> CustomerDeactivateImpactOut:
    """Calcula impacto esperado antes de desativar um cliente."""
    customer = get_customer(router_name, customer_id, use_cache=False)

    current_balance = None
    try:
        current_balance = get_customer_balance(
            router_name,
            customer_id,
            use_cache=False,
        ).balance
    except Exception:
        current_balance = None

    return CustomerDeactivateImpactOut(
        router_name=customer.router_name,
        customer_id=customer.customer_id,
        current_status=customer.status,
        current_balance=current_balance,
    )


def activate_customer(
    router_name: str,
    customer_id: str,
    *,
    db=None,
) -> CustomerStatusChangeOut:
    """Ativa um cliente via statusCustomer."""
    customer_id = str(customer_id)
    router = _get_router_or_raise(router_name)
    before = get_customer(router.name, customer_id, use_cache=False)
    result = sanitize_payload(
        _build_client().set_customer_status(router, customer_id, ACTIVE_STATUS)
    )

    audit_recorded = record_audit_action(
        action="customer.activate",
        router_name=router.name,
        customer_id=customer_id,
        before=before.model_dump(mode="json"),
        after={"status": ACTIVE_STATUS, "result": result},
        db=db,
    )

    return CustomerStatusChangeOut(
        router_name=router.name,
        customer_id=customer_id,
        action="activate",
        requested_status=ACTIVE_STATUS,
        previous_status=before.status,
        action_executed=True,
        message="Cliente ativado",
        audit_recorded=audit_recorded,
        result=result if isinstance(result, dict) else {"response": result},
    )


def deactivate_customer(
    router_name: str,
    customer_id: str,
    *,
    confirm: bool = False,
    db=None,
) -> CustomerStatusChangeOut:
    """Desativa um cliente somente quando confirm=True."""
    customer_id = str(customer_id)
    router = _get_router_or_raise(router_name)
    impact = get_deactivation_impact(router.name, customer_id)

    if not confirm:
        return CustomerStatusChangeOut(
            router_name=router.name,
            customer_id=customer_id,
            action="deactivate",
            requested_status=INACTIVE_STATUS,
            previous_status=impact.current_status,
            action_executed=False,
            message="Acao nao executada. Reenvie com confirm=true para desativar.",
            impact=impact,
            audit_recorded=False,
        )

    result = sanitize_payload(
        _build_client().set_customer_status(router, customer_id, INACTIVE_STATUS)
    )

    audit_recorded = record_audit_action(
        action="customer.deactivate",
        router_name=router.name,
        customer_id=customer_id,
        before=impact.model_dump(mode="json"),
        after={"status": INACTIVE_STATUS, "result": result},
        db=db,
    )

    return CustomerStatusChangeOut(
        router_name=router.name,
        customer_id=customer_id,
        action="deactivate",
        requested_status=INACTIVE_STATUS,
        previous_status=impact.current_status,
        action_executed=True,
        message="Cliente desativado",
        impact=impact,
        audit_recorded=audit_recorded,
        result=result if isinstance(result, dict) else {"response": result},
    )
