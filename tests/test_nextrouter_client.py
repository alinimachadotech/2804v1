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
    NextRouterServerError,
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


def test_nextrouter_client_base_url_priority():
    client = NextRouterClient()

    assert (
        client._base_url_for_router(
            {
                "base_url": "https://router-base.example.test/",
                "host": "router-host.example.test",
                "ip": "192.0.2.10",
            }
        )
        == "https://router-base.example.test"
    )
    assert (
        client._base_url_for_router(
            {
                "host": "router-host.example.test",
                "ip": "192.0.2.10",
            }
        )
        == "https://router-host.example.test"
    )
    assert (
        client._base_url_for_router(
            {
                "ip": "192.0.2.10",
            }
        )
        == "https://192.0.2.10"
    )


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
        "usable_balance": None,
        "customer_balance": None,
        "customer_limit": None,
        "tipo_tar": None,
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
        date_end="2026-01-01",
        start=10,
        limit=50,
    )

    assert result[0]["amount"] == Decimal("10.00")
    called_url = mock_client.get.call_args.args[0]
    assert called_url.endswith("/api/manageCredit/token-fake-secret/key-fake-secret/customer-1")
    assert mock_client.get.call_args.kwargs["params"] == {
        "date_ini": "2026-01-01",
        "date_end": "2026-01-01",
        "start": 10,
        "limit": 50,
    }
    mock_client.post.assert_not_called()
    mock_client.delete.assert_not_called()


@patch("app.integrations.nextrouter.client.httpx.Client")
def test_get_cdr_uses_customer_id_as_optional_path_param(mock_client_class):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "total_records": 1,
        "total_time": "00:00:30",
        "total_value": "1,50",
        "data": [{"valor": "1,50"}],
    }

    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = False
    mock_client.get.return_value = mock_response
    mock_client_class.return_value = mock_client

    router = {
        "base_url": "https://plataforma4.geraxtelecom.com.br",
        "token": "token-fake-secret",
        "key": "key-fake-secret",
    }
    client = NextRouterClient()

    result = client.get_cdr(
        router,
        customer_id="179",
        date_ini="2026-05-12",
        date_end="2026-05-12",
        time_ini="00:00:00",
        time_end="00:05:00",
        start=0,
        limit=10,
    )

    called_url = mock_client.get.call_args.args[0]
    assert called_url.endswith("/api/cdr/token-fake-secret/key-fake-secret/179")
    assert mock_client.get.call_args.kwargs["params"] == {
        "date_ini": "2026-05-12",
        "date_end": "2026-05-12",
        "time_ini": "00:00:00",
        "time_end": "00:05:00",
        "start": 0,
        "limit": 10,
    }
    assert result["total_records"] == 1
    assert result["total_time"] == "00:00:30"
    assert result["total_value"] == "1,50"
    assert result["data"] == [{"valor": Decimal("1.50")}]


@patch("app.integrations.nextrouter.client.httpx.Client")
def test_get_cdr_disconnection_uses_customer_id_as_optional_path_param(
    mock_client_class,
):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = []

    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = False
    mock_client.get.return_value = mock_response
    mock_client_class.return_value = mock_client

    router = {
        "base_url": "https://plataforma4.geraxtelecom.com.br",
        "token": "token-fake-secret",
        "key": "key-fake-secret",
    }
    client = NextRouterClient()

    client.get_cdr_disconnection(
        router,
        customer_id="179",
        date_ini="2026-05-12",
        date_end="2026-05-12",
        time_ini="00:00:00",
        time_end="00:05:00",
        start=0,
        limit=10,
    )

    called_url = mock_client.get.call_args.args[0]
    assert called_url.endswith(
        "/api/cdrDisconnection/token-fake-secret/key-fake-secret/179"
    )
    assert mock_client.get.call_args.kwargs["params"] == {
        "date_ini": "2026-05-12",
        "date_end": "2026-05-12",
        "time_ini": "00:00:00",
        "time_end": "00:05:00",
        "start": 0,
        "limit": 10,
    }


@patch("app.integrations.nextrouter.client.httpx.Client")
def test_profit_customers_maps_customer_id_to_customers_array(mock_client_class):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = []

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

    client.get_profit_customers(
        router,
        customer_id="179",
        date_ini="2026-05-12",
        date_end="2026-05-12",
        start=0,
        limit=10,
    )

    called_url = mock_client.get.call_args.args[0]
    assert called_url.endswith("/api/profitCustomers/token-fake-secret/key-fake-secret")
    assert mock_client.get.call_args.kwargs["params"] == {
        "date_ini": "2026-05-12",
        "date_end": "2026-05-12",
        "start": 0,
        "limit": 10,
        "customers[]": "179",
    }


@patch("app.integrations.nextrouter.client.httpx.Client")
def test_profit_gateways_maps_customer_id_to_customers_array(mock_client_class):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = []

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

    client.get_profit_gateways(router, customer_id="179", start=0, limit=10)

    called_url = mock_client.get.call_args.args[0]
    assert called_url.endswith("/api/profitGateways/token-fake-secret/key-fake-secret")
    assert mock_client.get.call_args.kwargs["params"] == {
        "start": 0,
        "limit": 10,
        "customers[]": "179",
    }


@patch("app.integrations.nextrouter.client.httpx.Client")
def test_profit_customers_accepts_multiple_customers_array(mock_client_class):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = []

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

    client.get_profit_customers(router, customers=["25", "39"], start=0, limit=10)

    assert mock_client.get.call_args.kwargs["params"] == {
        "start": 0,
        "limit": 10,
        "customers[]": ["25", "39"],
    }


@patch("app.integrations.nextrouter.client.httpx.Client")
def test_profit_gateways_accepts_multiple_gateways_array(mock_client_class):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = []

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

    client.get_profit_gateways(router, gateways=["1", "5"], start=0, limit=10)

    assert mock_client.get.call_args.kwargs["params"] == {
        "start": 0,
        "limit": 10,
        "gateways[]": ["1", "5"],
    }


@patch("app.integrations.nextrouter.client.httpx.Client")
def test_profit_reports_omit_array_filters_when_absent(mock_client_class):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = []

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

    client.get_profit_customers(router, start=20, limit=30)

    assert mock_client.get.call_args.kwargs["params"] == {
        "start": 20,
        "limit": 30,
    }


@patch("app.integrations.nextrouter.client.httpx.Client")
def test_profit_reports_keep_legacy_simple_filter_params(mock_client_class):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = []

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

    client.get_profit_customers(
        router,
        customers="25,39",
        gateways="1",
        start=0,
        limit=10,
    )

    assert mock_client.get.call_args.kwargs["params"] == {
        "start": 0,
        "limit": 10,
        "customers[]": ["25", "39"],
        "gateways[]": "1",
    }


@patch("app.integrations.nextrouter.client.httpx.Client")
def test_nextrouter_5xx_log_is_sanitized(mock_client_class, caplog):
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "server exploded token-fake-secret key-fake-secret"

    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = False
    mock_client.get.return_value = mock_response
    mock_client_class.return_value = mock_client

    router = {
        "name": "Router21/gerax",
        "base_url": "https://plataforma4.geraxtelecom.com.br",
        "token": "token-fake-secret",
        "key": "key-fake-secret",
    }
    client = NextRouterClient()

    caplog.set_level(logging.ERROR, logger="app.integrations.nextrouter.client")
    with pytest.raises(NextRouterServerError):
        client.get_cdr(router, customer_id="179")

    assert "Router21/gerax" in caplog.text
    assert "status_code=500" in caplog.text
    assert "https://plataforma4.geraxtelecom.com.br" in caplog.text
    assert "path=/api/cdr/***/***/179" in caplog.text
    assert "endpoint=cdr" in caplog.text
    assert "token-fake-secret" not in caplog.text
    assert "key-fake-secret" not in caplog.text
    assert "****" in caplog.text
