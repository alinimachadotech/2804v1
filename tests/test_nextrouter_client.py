"""Testes para o cliente NextRouter."""

from decimal import Decimal
import inspect
import logging
import pytest
from unittest.mock import MagicMock, patch

from app.integrations.nextrouter.client import NextRouterClient
from app.integrations.nextrouter.exceptions import (
    NextRouterAuthError,
    NextRouterError,
    NextRouterNotFoundError,
    NextRouterRateLimitError,
    NextRouterTimeoutError,
    NextRouterValidationError,
)


def test_nextrouter_client_init():
    """Testa inicialização do cliente."""
    client = NextRouterClient(base_url="https://192.168.1.100")
    assert client.base_url == "https://192.168.1.100"
    assert client.timeout == NextRouterClient.DEFAULT_TIMEOUT


def test_nextrouter_client_init_strips_trailing_slash():
    """Testa que URL com slash final é removido."""
    client = NextRouterClient(base_url="https://192.168.1.100/")
    assert client.base_url == "https://192.168.1.100"


def test_nextrouter_client_exposes_only_read_only_router_methods():
    source = inspect.getsource(NextRouterClient)

    assert ".post(" not in source
    assert ".delete(" not in source
    assert not hasattr(NextRouterClient, "set_customer_status")
    assert not hasattr(NextRouterClient, "manage_credit")
    assert not hasattr(NextRouterClient, "delete_online_call")


@patch("app.integrations.nextrouter.client.httpx.Client")
def test_get_online_calls_aggregate_success(mock_client_class):
    """Testa requisição bem-sucedida."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"total_calls": 100}
    
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = False
    mock_client.get.return_value = mock_response
    mock_client_class.return_value = mock_client
    
    client = NextRouterClient(base_url="https://192.168.1.100")
    result = client.get_online_calls_aggregate("token123", "key456")
    
    assert result == {"total_calls": 100}


@patch("app.integrations.nextrouter.client.httpx.Client")
def test_get_online_calls_aggregate_auth_error(mock_client_class):
    """Testa erro de autenticação (403)."""
    mock_response = MagicMock()
    mock_response.status_code = 403
    
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = False
    mock_client.get.return_value = mock_response
    mock_client_class.return_value = mock_client
    
    client = NextRouterClient(base_url="https://192.168.1.100")
    
    with pytest.raises(NextRouterAuthError):
        client.get_online_calls_aggregate("invalid", "token")


@patch("app.integrations.nextrouter.client.httpx.Client")
def test_get_online_calls_aggregate_not_found(mock_client_class):
    """Testa erro 404."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = False
    mock_client.get.return_value = mock_response
    mock_client_class.return_value = mock_client
    
    client = NextRouterClient(base_url="https://192.168.1.100")
    
    with pytest.raises(NextRouterNotFoundError):
        client.get_online_calls_aggregate("token123", "key456")


@patch("app.integrations.nextrouter.client.httpx.Client")
def test_get_online_calls_aggregate_rate_limit(mock_client_class):
    """Testa erro de rate limit (429)."""
    mock_response = MagicMock()
    mock_response.status_code = 429
    
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = False
    mock_client.get.return_value = mock_response
    mock_client_class.return_value = mock_client
    
    client = NextRouterClient(base_url="https://192.168.1.100")
    
    with pytest.raises(NextRouterRateLimitError):
        client.get_online_calls_aggregate("token123", "key456")


@patch("app.integrations.nextrouter.client.httpx.Client")
def test_get_online_calls_aggregate_timeout(mock_client_class):
    """Testa erro de timeout."""
    import httpx
    
    mock_client_class.side_effect = httpx.TimeoutException("Timeout")
    
    client = NextRouterClient(base_url="https://192.168.1.100")
    
    with pytest.raises(NextRouterTimeoutError):
        client.get_online_calls_aggregate("token123", "key456")


@patch("app.integrations.nextrouter.client.httpx.Client")
def test_request_logs_masked_url_and_uses_config(mock_client_class, caplog):
    """Testa montagem segura: URL real nao aparece nos logs."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"saldo": "177,90"}

    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = False
    mock_client.get.return_value = mock_response
    mock_client_class.return_value = mock_client

    router = {
        "base_url": "https://router.example.test",
        "token": "token-fake-secret",
        "key": "key-fake-secret",
    }
    client = NextRouterClient(timeout=7, verify_ssl=False)

    caplog.set_level(logging.DEBUG, logger="app.integrations.nextrouter.client")
    result = client.get_customer_balance(router, "customer-1")

    assert result["balance"] == Decimal("177.90")
    assert "token-fake-secret" not in caplog.text
    assert "key-fake-secret" not in caplog.text
    assert "/****/****" in caplog.text
    assert mock_client_class.call_args.kwargs["verify"] is False
    assert mock_client_class.call_args.kwargs["timeout"] == 7


@patch("app.integrations.nextrouter.client.httpx.Client")
def test_nextrouter_client_validation_error_422(mock_client_class):
    """Testa erro de validacao (422)."""
    mock_response = MagicMock()
    mock_response.status_code = 422

    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = False
    mock_client.get.return_value = mock_response
    mock_client_class.return_value = mock_client

    router = {
        "base_url": "https://router.example.test",
        "token": "token-fake-secret",
        "key": "key-fake-secret",
    }
    client = NextRouterClient()

    with pytest.raises(NextRouterValidationError):
        client.get_customer_balance(router, "customer-1")


@patch("app.integrations.nextrouter.client.httpx.Client")
def test_get_customer_balance_parses_money_and_params(mock_client_class):
    """Testa get_customer_balance com mock e Decimal."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id_cliente": "customer-1", "saldo": "177,90"}

    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = False
    mock_client.get.return_value = mock_response
    mock_client_class.return_value = mock_client

    router = {
        "base_url": "https://router.example.test",
        "token": "token-fake-secret",
        "key": "key-fake-secret",
    }
    client = NextRouterClient()

    result = client.get_customer_balance(router, "customer-1")

    assert result == {
        "customer_id": "customer-1",
        "balance": Decimal("177.90"),
    }
    called_url = mock_client.get.call_args.args[0]
    assert called_url.endswith("/api/getCustomerBalance/token-fake-secret/key-fake-secret/customer-1")
    assert mock_client.get.call_args.kwargs["params"] == {}


@patch("app.integrations.nextrouter.client.httpx.Client")
def test_get_credit_history_uses_get_path_and_pagination_only(mock_client_class):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{"valor": "10,00"}]

    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = False
    mock_client.get.return_value = mock_response
    mock_client_class.return_value = mock_client

    router = {
        "base_url": "https://router.example.test",
        "token": "token-fake-secret",
        "key": "key-fake-secret",
    }
    client = NextRouterClient()

    result = client.get_credit_history(
        router,
        "customer-1",
        date_ini="2026-01-01",
        date_end="2026-01-31",
        start=10,
        limit=50,
    )

    assert result[0]["amount"] == Decimal("10.00")
    called_url = mock_client.get.call_args.args[0]
    assert called_url.endswith("/api/manageCredit/token-fake-secret/key-fake-secret/customer-1")
    assert mock_client.get.call_args.kwargs["params"] == {
        "date_ini": "2026-01-01",
        "date_end": "2026-01-31",
        "start": 10,
        "limit": 50,
    }
    mock_client.post.assert_not_called()
    mock_client.delete.assert_not_called()
