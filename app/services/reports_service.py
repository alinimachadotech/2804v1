"""Servicos read-only para relatorios NextRouter."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Callable

from app.core.cache import redis_get_json, redis_set_json
from app.core.settings import settings
from app.integrations.nextrouter.client import NextRouterClient
from app.integrations.nextrouter.parser import normalize_money_collection
from app.schemas.reports import ReadOnlyQueryOut
from app.services.audit_service import sanitize_payload
from app.services.balance_service import RouterNotFoundError
from app.services.router_service import get_router_secret_by_name


DataNormalizer = Callable[[Any], Any]
ReportFetcher = Callable[[NextRouterClient, Any, str | None, int, int, dict[str, Any]], Any]


def _cache_part(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.:-]+", "_", str(value).strip().lower())


def _cache_key(
    namespace: str,
    router_name: str,
    customer_id: str | None,
    start: int,
    limit: int,
    filters: dict[str, Any],
) -> str:
    fingerprint = json.dumps(
        {
            "customer_id": customer_id,
            "start": start,
            "limit": limit,
            "filters": filters,
        },
        sort_keys=True,
        default=str,
    )
    digest = hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()[:24]
    return f"gerax:readonly:{namespace}:{_cache_part(router_name)}:{digest}"


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


def _clean_filters(filters: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in filters.items() if value is not None}


def _query(
    *,
    namespace: str,
    router_name: str,
    customer_id: str | None = None,
    start: int = 0,
    limit: int = 100,
    filters: dict[str, Any] | None = None,
    fetcher: ReportFetcher,
    cache_normalizer: DataNormalizer | None = None,
    use_cache: bool = True,
) -> ReadOnlyQueryOut:
    router = _get_router_or_raise(router_name)
    customer_id = str(customer_id) if customer_id not in (None, "") else None
    start = max(start, 0)
    limit = max(limit, 1)
    clean_filters = _clean_filters(filters or {})
    key = _cache_key(namespace, router.name, customer_id, start, limit, clean_filters)

    if use_cache:
        cached = redis_get_json(key)
        if cached and "data" in cached:
            data = cached["data"]
            if cache_normalizer is not None:
                data = cache_normalizer(data)
            return ReadOnlyQueryOut(
                router_name=router.name,
                customer_id=customer_id,
                start=start,
                limit=limit,
                filters=clean_filters,
                data=data,
                cached=True,
            )

    data = sanitize_payload(
        fetcher(_build_client(), router, customer_id, start, limit, clean_filters)
    )

    redis_set_json(
        key,
        {"data": data},
        ttl_seconds=max(settings.read_only_cache_ttl_seconds, 1),
    )

    return ReadOnlyQueryOut(
        router_name=router.name,
        customer_id=customer_id,
        start=start,
        limit=limit,
        filters=clean_filters,
        data=data,
        cached=False,
    )


def get_cdr_report(
    router_name: str,
    *,
    customer_id: str | None = None,
    start: int = 0,
    limit: int = 100,
    **filters: Any,
) -> ReadOnlyQueryOut:
    return _query(
        namespace="cdr",
        router_name=router_name,
        customer_id=customer_id,
        start=start,
        limit=limit,
        filters=filters,
        fetcher=lambda client, router, cid, s, l, f: client.get_cdr(
            router, customer_id=cid, start=s, limit=l, **f
        ),
        cache_normalizer=normalize_money_collection,
    )


def get_cdr_disconnection_report(
    router_name: str,
    *,
    customer_id: str | None = None,
    start: int = 0,
    limit: int = 100,
    **filters: Any,
) -> ReadOnlyQueryOut:
    return _query(
        namespace="cdr-disconnections",
        router_name=router_name,
        customer_id=customer_id,
        start=start,
        limit=limit,
        filters=filters,
        fetcher=lambda client, router, cid, s, l, f: client.get_cdr_disconnection(
            router, customer_id=cid, start=s, limit=l, **f
        ),
        cache_normalizer=normalize_money_collection,
    )


def get_cdr_sipcodes_report(
    router_name: str,
    *,
    customer_id: str | None = None,
    start: int = 0,
    limit: int = 100,
) -> ReadOnlyQueryOut:
    return _query(
        namespace="cdr-sipcodes",
        router_name=router_name,
        customer_id=customer_id,
        start=start,
        limit=limit,
        fetcher=lambda client, router, cid, s, l, f: client.get_cdr_sipcodes(
            router, customer_id=cid, start=s, limit=l, **f
        ),
    )


def get_profit_customers_report(
    router_name: str,
    *,
    customer_id: str | None = None,
    start: int = 0,
    limit: int = 100,
    **filters: Any,
) -> ReadOnlyQueryOut:
    return _query(
        namespace="profit-customers",
        router_name=router_name,
        customer_id=customer_id,
        start=start,
        limit=limit,
        filters=filters,
        fetcher=lambda client, router, cid, s, l, f: client.get_profit_customers(
            router, customer_id=cid, start=s, limit=l, **f
        ),
        cache_normalizer=normalize_money_collection,
    )


def get_profit_gateways_report(
    router_name: str,
    *,
    customer_id: str | None = None,
    start: int = 0,
    limit: int = 100,
    **filters: Any,
) -> ReadOnlyQueryOut:
    return _query(
        namespace="profit-gateways",
        router_name=router_name,
        customer_id=customer_id,
        start=start,
        limit=limit,
        filters=filters,
        fetcher=lambda client, router, cid, s, l, f: client.get_profit_gateways(
            router, customer_id=cid, start=s, limit=l, **f
        ),
        cache_normalizer=normalize_money_collection,
    )
