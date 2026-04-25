"""Testes para o cliente NextRouter."""

import pytest
from unittest.mock import MagicMock, patch

from app.integrations.nextrouter.client import NextRouterClient
from app.integrations.nextrouter.exceptions import (
    NextRouterAuthError,
    NextRouterError,
    NextRouterNotFoundError,
    NextRouterRateLimitError,
    NextRouterTimeoutError,
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
