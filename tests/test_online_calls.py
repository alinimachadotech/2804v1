"""Testes para endpoints de chamadas online."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


@patch("app.api.v1.endpoints.online_calls.get_online_aggregate_by_router_id")
def test_get_online_aggregate_success(mock_get_online):
    """Testa requisição bem-sucedida."""
    mock_get_online.return_value = {"total_calls": 100, "active": 5}
    
    response = client.get("/api/v1/routers/1/online-aggregate")
    
    assert response.status_code == 200
    assert response.json() == {"total_calls": 100, "active": 5}
    mock_get_online.assert_called_once_with(1)


@patch("app.api.v1.endpoints.online_calls.get_online_aggregate_by_router_id")
def test_get_online_aggregate_router_not_found(mock_get_online):
    """Testa router não encontrado."""
    mock_get_online.side_effect = ValueError("Router 999 não encontrado")
    
    response = client.get("/api/v1/routers/999/online-aggregate")
    
    assert response.status_code == 404


@patch("app.api.v1.endpoints.online_calls.get_online_aggregate_by_router_id")
def test_get_online_aggregate_auth_error(mock_get_online):
    """Testa erro de autenticação."""
    from app.integrations.nextrouter.exceptions import NextRouterAuthError
    
    mock_get_online.side_effect = NextRouterAuthError("Credenciais inválidas")
    
    response = client.get("/api/v1/routers/1/online-aggregate")
    
    assert response.status_code == 401


@patch("app.api.v1.endpoints.online_calls.get_online_aggregate_by_router_id")
def test_get_online_aggregate_rate_limit(mock_get_online):
    """Testa rate limit."""
    from app.integrations.nextrouter.exceptions import NextRouterRateLimitError
    
    mock_get_online.side_effect = NextRouterRateLimitError("Rate limit exceeded")
    
    response = client.get("/api/v1/routers/1/online-aggregate")
    
    assert response.status_code == 429


@patch("app.api.v1.endpoints.online_calls.get_online_aggregate_by_router_id")
def test_get_online_aggregate_timeout(mock_get_online):
    """Testa timeout."""
    from app.integrations.nextrouter.exceptions import NextRouterTimeoutError
    
    mock_get_online.side_effect = NextRouterTimeoutError("Timeout")
    
    response = client.get("/api/v1/routers/1/online-aggregate")
    
    assert response.status_code == 504


@patch("app.api.v1.endpoints.online_calls.get_online_aggregate_by_router_id")
def test_get_online_aggregate_generic_error(mock_get_online):
    """Testa erro genérico."""
    from app.integrations.nextrouter.exceptions import NextRouterError
    
    mock_get_online.side_effect = NextRouterError("Erro genérico")
    
    response = client.get("/api/v1/routers/1/online-aggregate")
    
    assert response.status_code == 502
