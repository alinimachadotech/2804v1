"""Testes dos endpoints read-only novos."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
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
        date_end=None,
        time_ini=None,
        time_end=None,
        device_id=None,
        type="answered",
        start=10,
        limit=50,
    )


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
