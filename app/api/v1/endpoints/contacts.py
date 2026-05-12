"""Endpoints read-only de contatos."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.v1.errors import handle_service_error
from app.schemas.reports import ReadOnlyQueryOut
from app.services.contacts_service import get_contacts


router = APIRouter(prefix="/api/v1/contacts", tags=["Contacts"])


@router.get("", response_model=ReadOnlyQueryOut)
def read_contacts(
    router_name: str = Query(..., min_length=1),
    customer_id: str | None = None,
    start: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    try:
        return get_contacts(
            router_name,
            customer_id=customer_id,
            start=start,
            limit=limit,
        )
    except Exception as exc:
        handle_service_error(exc)
