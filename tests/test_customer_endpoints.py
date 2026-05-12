"""Testes dos endpoints de clientes."""

from decimal import Decimal
from unittest.mock import ANY, patch

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.balance import CustomerBalanceOut
from app.schemas.customer import CustomerStatusChangeOut
from app.schemas.financial import CreditHistoryOut, FinancialOperationOut
from app.services.financial_service import InsufficientBalanceError


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


@patch("app.api.v1.endpoints.customers.deactivate_customer")
def test_deactivate_endpoint_passes_confirm_false(mock_deactivate):
    mock_deactivate.return_value = CustomerStatusChangeOut(
        router_name="Router Test",
        customer_id="customer-1",
        action="deactivate",
        requested_status=0,
        previous_status=1,
        action_executed=False,
        message="Acao nao executada. Reenvie com confirm=true para desativar.",
    )

    response = client.post(
        "/api/v1/customers/customer-1/deactivate",
        params={"router_name": "Router Test"},
    )

    assert response.status_code == 200
    assert response.json()["action_executed"] is False
    mock_deactivate.assert_called_once_with(
        "Router Test",
        "customer-1",
        confirm=False,
        db=ANY,
    )


@patch("app.api.v1.endpoints.customers.credit_customer")
def test_credit_endpoint_requires_reason_before_service(mock_credit):
    response = client.post(
        "/api/v1/customers/customer-1/credit",
        params={"router_name": "Router Test"},
        json={"amount": "10.00"},
    )

    assert response.status_code == 422
    mock_credit.assert_not_called()


@patch("app.api.v1.endpoints.customers.debit_customer")
def test_debit_endpoint_maps_insufficient_balance(mock_debit):
    mock_debit.side_effect = InsufficientBalanceError("Saldo insuficiente para debito")

    response = client.post(
        "/api/v1/customers/customer-1/debit",
        params={"router_name": "Router Test"},
        json={"amount": "10.00", "reason": "test debit"},
    )

    assert response.status_code == 400


@patch("app.api.v1.endpoints.customers.get_credit_history")
def test_credit_history_endpoint_uses_router_name_and_pagination(mock_history):
    mock_history.return_value = CreditHistoryOut(
        router_name="Router Test",
        customer_id="customer-1",
        start=0,
        limit=50,
        date_ini="2026-01-01",
        date_end="2026-01-31",
        items=[{"amount": Decimal("10.00"), "reason": "test"}],
    )

    response = client.get(
        "/api/v1/customers/customer-1/credit-history",
        params={
            "router_name": "Router Test",
            "date_ini": "2026-01-01",
            "date_end": "2026-01-31",
            "limit": 50,
        },
    )

    assert response.status_code == 200
    assert response.json()["limit"] == 50
    mock_history.assert_called_once_with(
        "Router Test",
        "customer-1",
        date_ini="2026-01-01",
        date_end="2026-01-31",
        start=0,
        limit=50,
    )


@patch("app.api.v1.endpoints.customers.credit_customer")
def test_credit_endpoint_success(mock_credit):
    mock_credit.return_value = FinancialOperationOut(
        router_name="Router Test",
        customer_id="customer-1",
        operation="credit",
        amount=Decimal("10.00"),
        reason="test credit",
        balance_before=Decimal("1.00"),
        balance_after=Decimal("11.00"),
    )

    response = client.post(
        "/api/v1/customers/customer-1/credit",
        params={"router_name": "Router Test"},
        json={"amount": "10.00", "reason": "test credit"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["operation"] == "credit"
    assert data["amount"] == "10.00"
