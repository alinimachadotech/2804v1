"""Testes da camada de servicos de negocio."""

from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.schemas.balance import CustomerBalanceOut
from app.schemas.customer import CustomerDeactivateImpactOut
from app.services.audit_service import sanitize_payload
from app.services.balance_service import get_customer_balance
from app.services.customer_service import deactivate_customer
from app.services.financial_service import (
    InsufficientBalanceError,
    debit_customer,
)


def fake_router():
    return SimpleNamespace(
        name="Router Test",
        ip="router.example.test",
        token="fake-token",
        key="fake-key",
    )


@patch("app.services.balance_service.redis_get_json")
@patch("app.services.balance_service.redis_set_json")
@patch("app.services.balance_service.get_router_secret_by_name")
@patch("app.services.balance_service.NextRouterClient")
def test_balance_service_uses_cache_miss_and_stores_decimal(
    mock_client_class,
    mock_get_router,
    mock_set_cache,
    mock_get_cache,
):
    mock_get_cache.return_value = None
    mock_get_router.return_value = fake_router()
    mock_client_class.return_value.get_customer_balance.return_value = {
        "customer_id": "customer-1",
        "balance": Decimal("177.90"),
    }

    result = get_customer_balance("Router Test", "customer-1")

    assert result.balance == Decimal("177.90")
    assert result.cached is False
    mock_set_cache.assert_called_once()
    cached_payload = mock_set_cache.call_args.args[1]
    assert cached_payload["balance"] == "177.90"


@patch("app.services.balance_service.redis_get_json")
@patch("app.services.balance_service.get_router_secret_by_name")
@patch("app.services.balance_service.NextRouterClient")
def test_balance_service_returns_cached_decimal(
    mock_client_class,
    mock_get_router,
    mock_get_cache,
):
    mock_get_router.return_value = fake_router()
    mock_get_cache.return_value = {
        "router_name": "Router Test",
        "customer_id": "customer-1",
        "balance": "177,90",
    }

    result = get_customer_balance("Router Test", "customer-1")

    assert result.balance == Decimal("177.90")
    assert result.cached is True
    mock_client_class.assert_not_called()


@patch("app.services.customer_service.get_deactivation_impact")
@patch("app.services.customer_service.get_router_secret_by_name")
@patch("app.services.customer_service.NextRouterClient")
def test_deactivate_customer_requires_confirm_before_status_change(
    mock_client_class,
    mock_get_router,
    mock_impact,
):
    mock_get_router.return_value = fake_router()
    mock_impact.return_value = CustomerDeactivateImpactOut(
        router_name="Router Test",
        customer_id="customer-1",
        current_status=1,
        current_balance=Decimal("10.00"),
    )

    result = deactivate_customer("Router Test", "customer-1", confirm=False)

    assert result.action_executed is False
    assert result.impact is not None
    mock_client_class.assert_not_called()


@patch("app.services.financial_service.get_customer_balance")
@patch("app.services.financial_service.get_router_secret_by_name")
@patch("app.services.financial_service.NextRouterClient")
def test_debit_customer_validates_balance_before_calling_router(
    mock_client_class,
    mock_get_router,
    mock_balance,
):
    mock_get_router.return_value = fake_router()
    mock_balance.return_value = CustomerBalanceOut(
        router_name="Router Test",
        customer_id="customer-1",
        balance=Decimal("5.00"),
    )

    with pytest.raises(InsufficientBalanceError):
        debit_customer("Router Test", "customer-1", Decimal("10.00"), "test debit")

    mock_client_class.assert_not_called()


def test_sanitize_payload_removes_credentials_recursively():
    payload = {
        "name": "Customer",
        "token": "should-not-leak",
        "nested": {"api_key": "should-not-leak", "status": "active"},
    }

    result = sanitize_payload(payload)

    assert "token" not in result
    assert "api_key" not in result["nested"]
    assert result["nested"]["status"] == "active"
