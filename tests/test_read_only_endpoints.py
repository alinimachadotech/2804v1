"""Testes dos endpoints read-only novos."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.integrations.nextrouter.exceptions import NextRouterServerError
from app.schemas.online_calls import OnlineAggregateAllRoutersOut
from app.schemas.reports import ReadOnlyQueryOut


client = TestClient(app)


@patch("app.api.v1.endpoints.reports.get_cdr_report")
def test_reports_cdr_endpoint_uses_filters_and_pagination(mock_report):
    mock_report.return_value = ReadOnlyQueryOut(
        router_name="Router Test",
        start=10,
        limit=50,
        filters={"date_ini": "2026-01-01", "type": "answered"},
        data=[],
    )

    response = client.get(
        "/api/v1/reports/cdr",
        params={
            "router_name": "Router Test",
            "date_ini": "2026-01-01",
            "date_end": "2026-01-01",
            "time_ini": "00:00:00",
            "time_end": "00:05:00",
            "type": "answered",
            "start": 10,
            "limit": 50,
        },
    )

    assert response.status_code == 200
    assert response.json()["limit"] == 50
    mock_report.assert_called_once_with(
        "Router Test",
        customer_id=None,
        date_ini="2026-01-01",
        date_end="2026-01-01",
        time_ini="00:00:00",
        time_end="00:05:00",
        device_id=None,
        type="answered",
        start=10,
        limit=50,
    )


@patch("app.api.v1.endpoints.reports.get_cdr_disconnection_report")
def test_reports_cdr_disconnections_accepts_time_filters(mock_report):
    mock_report.return_value = ReadOnlyQueryOut(
        router_name="Router Test",
        customer_id="179",
        start=0,
        limit=10,
        filters={
            "date_ini": "2026-05-12",
            "date_end": "2026-05-12",
            "time_ini": "00:00:00",
            "time_end": "00:05:00",
        },
        data=[],
    )

    response = client.get(
        "/api/v1/reports/cdr-disconnections",
        params={
            "router_name": "Router21/gerax",
            "customer_id": "179",
            "date_ini": "2026-05-12",
            "date_end": "2026-05-12",
            "time_ini": "00:00:00",
            "time_end": "00:05:00",
            "start": 0,
            "limit": 10,
        },
    )

    assert response.status_code == 200
    mock_report.assert_called_once_with(
        "Router21/gerax",
        customer_id="179",
        date_ini="2026-05-12",
        date_end="2026-05-12",
        time_ini="00:00:00",
        time_end="00:05:00",
        sip_code=None,
        start=0,
        limit=10,
    )


@patch("app.api.v1.endpoints.reports.get_cdr_report")
def test_reports_cdr_local_error_detail_is_sanitized(mock_report):
    mock_report.side_effect = NextRouterServerError(
        "Erro HTTP 500 do NextRouter",
        diagnostics={
            "status_code": 500,
            "body_preview": "upstream failed **** ****",
            "endpoint": "cdr",
            "path": "/api/cdr/***/***/179",
        },
    )

    response = client.get(
        "/api/v1/reports/cdr",
        params={
            "router_name": "Router21/gerax",
            "customer_id": "179",
            "date_ini": "2026-05-12",
            "date_end": "2026-05-12",
            "time_ini": "00:00:00",
            "time_end": "00:05:00",
            "start": 0,
            "limit": 10,
        },
    )

    assert response.status_code == 502
    detail = response.json()["detail"]
    assert detail["upstream_status_code"] == 500
    assert detail["endpoint"] == "cdr"
    assert detail["path"] == "/api/cdr/***/***/179"
    serialized = str(detail)
    assert "token-fake-secret" not in serialized
    assert "key-fake-secret" not in serialized


@patch("app.api.v1.endpoints.contacts.get_contacts")
def test_contacts_endpoint_uses_get_with_start_limit(mock_contacts):
    mock_contacts.return_value = ReadOnlyQueryOut(
        router_name="Router Test",
        customer_id="customer-1",
        start=0,
        limit=25,
        data=[],
    )

    response = client.get(
        "/api/v1/contacts",
        params={
            "router_name": "Router Test",
            "customer_id": "customer-1",
            "limit": 25,
        },
    )

    assert response.status_code == 200
    assert response.json()["customer_id"] == "customer-1"
    mock_contacts.assert_called_once_with(
        "Router Test",
        customer_id="customer-1",
        start=0,
        limit=25,
    )


@patch("app.api.v1.endpoints.online_calls.get_online_calls_by_router")
def test_noc_online_calls_endpoint_is_read_only_get(mock_calls):
    mock_calls.return_value = {
        "router_name": "Router Test",
        "id_rota": "10",
        "summary": True,
        "id_record": None,
        "data": [],
        "cached": False,
    }

    response = client.get(
        "/api/v1/noc/online/calls",
        params={"router_name": "Router Test", "id_rota": "10", "summary": True},
    )

    assert response.status_code == 200
    mock_calls.assert_called_once_with(
        "Router Test",
        id_rota="10",
        summary=True,
        id_record=None,
    )


@patch("app.api.v1.endpoints.online_calls.get_online_aggregate_all_routers")
def test_noc_online_aggregate_filters_by_router_name(mock_aggregate):
    mock_aggregate.return_value = OnlineAggregateAllRoutersOut(
        total=10,
        ringing=2,
        talking=8,
        clients_count=1,
        routes_count=1,
        servers_count=1,
        top_clients=[{"name": "Client A", "total": 10, "ringing": 2, "talking": 8}],
        routers=[
            {
                "router_id": 1,
                "router_name": "Router21/gerax",
                "total": 10,
                "ringing": 2,
                "talking": 8,
                "status": "ok",
            }
        ],
        failures=[],
        routes=[],
        top_routes=[],
        top_routes_by_router=[],
        servers=[],
    )

    response = client.get(
        "/api/v1/noc/online/aggregate",
        params={"router_name": "Router21/gerax"},
    )

    assert response.status_code == 200
    assert response.json()["routers"][0]["router_name"] == "Router21/gerax"
    mock_aggregate.assert_called_once_with(router_name="Router21/gerax")
