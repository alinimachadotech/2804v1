"""Testes dos endpoints de clientes."""

from decimal import Decimal
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.balance import CustomerBalanceOut
from app.schemas.customer import CustomerOut
from app.schemas.financial import CreditHistoryOut


client = TestClient(app)


@patch("app.api.v1.endpoints.customers.get_customer_balance")
def test_get_customer_balance_endpoint(mock_get_balance):
    mock_get_balance.return_value = CustomerBalanceOut(
        router_name="Router Test",
        customer_id="customer-1",
        balance=Decimal("177.90"),
    )

    response = client.get(
        "/api/v1/customers/customer-1/balance",
        params={"router_name": "Router Test"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["router_name"] == "Router Test"
    assert data["customer_id"] == "customer-1"
    assert data["balance"] == "177.90"
    serialized = str(data).lower()
    assert "token" not in serialized
    assert "password" not in serialized


@patch("app.api.v1.endpoints.customers.get_customer")
def test_get_customer_endpoint(mock_get_customer):
    mock_get_customer.return_value = CustomerOut(
        router_name="Router Test",
        customer_id="customer-1",
        name="Cliente Teste",
        status=1,
        is_active=True,
        data={"id_cliente": "customer-1"},
    )

    response = client.get(
        "/api/v1/customers/customer-1",
        params={"router_name": "Router Test"},
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is True
    mock_get_customer.assert_called_once_with("Router Test", "customer-1")


@patch("app.api.v1.endpoints.customers.get_credit_history")
def test_credit_history_endpoint_uses_router_name_and_pagination(mock_history):
    mock_history.return_value = CreditHistoryOut(
        router_name="Router Test",
        customer_id="customer-1",
        start=0,
        limit=50,
        date_ini="2026-01-01",
        date_end="2026-01-01",
        items=[{"amount": Decimal("10.00"), "reason": "test"}],
    )

    response = client.get(
        "/api/v1/customers/customer-1/credit-history",
        params={
            "router_name": "Router Test",
            "date_ini": "2026-01-01",
            "date_end": "2026-01-01",
            "limit": 50,
        },
    )

    assert response.status_code == 200
    assert response.json()["limit"] == 50
    mock_history.assert_called_once_with(
        "Router Test",
        "customer-1",
        date_ini="2026-01-01",
        date_end="2026-01-01",
        start=0,
        limit=50,
    )


def test_mutation_customer_endpoints_are_not_exposed():
    blocked_paths = [
        "/api/v1/customers/customer-1/activate",
        "/api/v1/customers/customer-1/deactivate",
        "/api/v1/customers/customer-1/credit",
        "/api/v1/customers/customer-1/debit",
        "/api/v1/customers/customer-1/set-balance",
    ]

    for path in blocked_paths:
        response = client.post(
            path,
            params={"router_name": "Router Test"},
            json={"amount": "10.00", "reason": "blocked"},
        )
        assert response.status_code in {404, 405}
