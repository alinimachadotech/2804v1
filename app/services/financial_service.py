"""Business service read-only para historico financeiro NextRouter."""

from __future__ import annotations

from datetime import date, timedelta
import hashlib
import json
import re

from app.core.cache import redis_get_json, redis_set_json
from app.core.settings import settings
from app.integrations.nextrouter.client import NextRouterClient
from app.integrations.nextrouter.parser import normalize_credit_history
from app.schemas.financial import CreditHistoryOut
from app.services.audit_service import sanitize_payload
from app.services.balance_service import RouterNotFoundError
from app.services.router_service import get_router_secret_by_name


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


def _cache_part(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.:-]+", "_", str(value).strip().lower())


def _cache_key(
    router_name: str,
    customer_id: str,
    date_ini: str,
    date_end: str,
    start: int,
    limit: int,
) -> str:
    fingerprint = json.dumps(
        {
            "customer_id": customer_id,
            "date_ini": date_ini,
            "date_end": date_end,
            "start": start,
            "limit": limit,
        },
        sort_keys=True,
    )
    digest = hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()[:24]
    return f"gerax:readonly:credit-history:{_cache_part(router_name)}:{digest}"


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
    key = _cache_key(router.name, customer_id, date_ini, date_end, start, limit)

    cached = redis_get_json(key)
    if cached and isinstance(cached.get("items"), list):
        return CreditHistoryOut(
            router_name=router.name,
            customer_id=customer_id,
            start=start,
            limit=limit,
            date_ini=date_ini,
            date_end=date_end,
            items=normalize_credit_history(cached["items"]),
            cached=True,
        )

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
    safe_items = items if isinstance(items, list) else []

    redis_set_json(
        key,
        {"items": safe_items},
        ttl_seconds=max(settings.read_only_cache_ttl_seconds, 1),
    )

    return CreditHistoryOut(
        router_name=router.name,
        customer_id=customer_id,
        start=start,
        limit=limit,
        date_ini=date_ini,
        date_end=date_end,
        items=safe_items,
        cached=False,
    )
