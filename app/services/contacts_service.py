"""Servicos read-only para contatos NextRouter."""

from __future__ import annotations

from typing import Any

from app.integrations.nextrouter.parser import normalize_money_collection
from app.schemas.reports import ReadOnlyQueryOut
from app.services.reports_service import _query


def get_contacts(
    router_name: str,
    *,
    customer_id: str | None = None,
    start: int = 0,
    limit: int = 100,
    **filters: Any,
) -> ReadOnlyQueryOut:
    return _query(
        namespace="contacts",
        router_name=router_name,
        customer_id=customer_id,
        start=start,
        limit=limit,
        filters=filters,
        fetcher=lambda client, router, cid, s, l, f: client.get_contacts(
            router, customer_id=cid, start=s, limit=l, **f
        ),
        cache_normalizer=normalize_money_collection,
    )
