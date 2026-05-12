"""Endpoints read-only de relatorios."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.v1.errors import handle_service_error
from app.schemas.reports import ReadOnlyQueryOut
from app.services.reports_service import (
    get_cdr_disconnection_report,
    get_cdr_report,
    get_cdr_sipcodes_report,
    get_profit_customers_report,
    get_profit_gateways_report,
)


router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])


@router.get("/cdr", response_model=ReadOnlyQueryOut)
def read_cdr(
    router_name: str = Query(..., min_length=1),
    customer_id: str | None = None,
    date_ini: str | None = None,
    date_end: str | None = None,
    time_ini: str | None = None,
    time_end: str | None = None,
    device_id: str | None = None,
    record_type: str | None = Query(None, alias="type"),
    start: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    try:
        return get_cdr_report(
            router_name,
            customer_id=customer_id,
            date_ini=date_ini,
            date_end=date_end,
            time_ini=time_ini,
            time_end=time_end,
            device_id=device_id,
            type=record_type,
            start=start,
            limit=limit,
        )
    except Exception as exc:
        handle_service_error(exc)


@router.get("/cdr-disconnections", response_model=ReadOnlyQueryOut)
def read_cdr_disconnections(
    router_name: str = Query(..., min_length=1),
    customer_id: str | None = None,
    date_ini: str | None = None,
    date_end: str | None = None,
    time_ini: str | None = None,
    time_end: str | None = None,
    sip_code: str | None = None,
    start: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    try:
        return get_cdr_disconnection_report(
            router_name,
            customer_id=customer_id,
            date_ini=date_ini,
            date_end=date_end,
            time_ini=time_ini,
            time_end=time_end,
            sip_code=sip_code,
            start=start,
            limit=limit,
        )
    except Exception as exc:
        handle_service_error(exc)


@router.get("/sip-codes", response_model=ReadOnlyQueryOut)
def read_sip_codes(
    router_name: str = Query(..., min_length=1),
    customer_id: str | None = None,
    start: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    try:
        return get_cdr_sipcodes_report(
            router_name,
            customer_id=customer_id,
            start=start,
            limit=limit,
        )
    except Exception as exc:
        handle_service_error(exc)


@router.get("/profit/customers", response_model=ReadOnlyQueryOut)
def read_profit_customers(
    router_name: str = Query(..., min_length=1),
    customer_id: str | None = None,
    date_ini: str | None = None,
    date_end: str | None = None,
    time_ini: str | None = None,
    time_end: str | None = None,
    src: str | None = None,
    dst: str | None = None,
    call_type: str | None = None,
    gateways: str | None = None,
    customers: str | None = None,
    start: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    try:
        return get_profit_customers_report(
            router_name,
            customer_id=customer_id,
            date_ini=date_ini,
            date_end=date_end,
            time_ini=time_ini,
            time_end=time_end,
            src=src,
            dst=dst,
            call_type=call_type,
            gateways=gateways,
            customers=customers,
            start=start,
            limit=limit,
        )
    except Exception as exc:
        handle_service_error(exc)


@router.get("/profit/gateways", response_model=ReadOnlyQueryOut)
def read_profit_gateways(
    router_name: str = Query(..., min_length=1),
    customer_id: str | None = None,
    date_ini: str | None = None,
    date_end: str | None = None,
    time_ini: str | None = None,
    time_end: str | None = None,
    src: str | None = None,
    dst: str | None = None,
    call_type: str | None = None,
    gateways: str | None = None,
    customers: str | None = None,
    start: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    try:
        return get_profit_gateways_report(
            router_name,
            customer_id=customer_id,
            date_ini=date_ini,
            date_end=date_end,
            time_ini=time_ini,
            time_end=time_end,
            src=src,
            dst=dst,
            call_type=call_type,
            gateways=gateways,
            customers=customers,
            start=start,
            limit=limit,
        )
    except Exception as exc:
        handle_service_error(exc)
