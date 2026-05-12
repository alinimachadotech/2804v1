"""Testes da camada de servicos de negocio."""

from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from app.services.audit_service import sanitize_payload
from app.services.balance_service import get_customer_balance
from app.services.customer_service import get_customer


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


@patch("app.services.customer_service.redis_get_json")
@patch("app.services.customer_service.redis_set_json")
@patch("app.services.customer_service.get_router_secret_by_name")
@patch("app.services.customer_service.NextRouterClient")
def test_customer_service_is_read_only_and_uses_cache(
    mock_client_class,
    mock_get_router,
    mock_set_cache,
    mock_get_cache,
):
    mock_get_cache.return_value = None
    mock_get_router.return_value = fake_router()
    mock_client_class.return_value.get_customer.return_value = {
        "customer_id": "customer-1",
        "name": "Cliente Teste",
        "status": 1,
        "raw": {"id_cliente": "customer-1"},
    }

    result = get_customer("Router Test", "customer-1")

    assert result.customer_id == "customer-1"
    assert result.is_active is True
    mock_client_class.return_value.get_customer.assert_called_once()
    mock_set_cache.assert_called_once()


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
