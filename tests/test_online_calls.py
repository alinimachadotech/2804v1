"""Testes para endpoints de chamadas online."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.services.online_calls_service import (
    build_top_routes,
    normalize_route_item,
    normalize_server_item,
)


client = TestClient(app)


# ============= Testes para endpoint single router =============

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


# ============= Testes para agregador multi-router =============

@patch("app.services.online_calls_service.list_routers")
@patch("app.services.online_calls_service.get_online_aggregate_by_router_id")
def test_get_online_aggregate_all_routers_success(mock_get_online, mock_list_routers):
    """Testa agregação bem-sucedida de múltiplos routers."""
    from app.schemas.router import RouterOut
    
    # Mock dos routers
    mock_list_routers.return_value = [
        RouterOut(id=1, name="Router 1", slug="router-1", ip="192.168.1.1",
                  base_url="https://192.168.1.1", is_active=True, verify_tls=False),
        RouterOut(id=2, name="Router 2", slug="router-2", ip="192.168.1.2",
                  base_url="https://192.168.1.2", is_active=True, verify_tls=False),
    ]
    
    # Simula dados de 2 routers com estrutura real
    mock_get_online.side_effect = [
        {
            "total": 100,
            "ringint": 10,
            "talking": 20,
            "clients": [
                # Formato 1: usando "cliente", "chamando", "falando"
                {"cliente": "Client A", "total": 50, "chamando": 5, "falando": 10},
                {"cliente": "Client B", "total": 50, "chamando": 5, "falando": 10},
            ],
            "routes": [{"id": 1}, {"id": 2}, {"id": 3}],
            "servers": [{"id": 1}, {"id": 2}],
        },
        {
            "total": 80,
            "ringint": 8,
            "talking": 15,
            "clients": [
                # Formato 2: usando "name", "ringing", "talking"
                {"name": "Client A", "total": 40, "ringing": 4, "talking": 8},
                {"name": "Client C", "total": 40, "ringing": 4, "talking": 7},
            ],
            "routes": [{"id": 1}, {"id": 2}, {"id": 3}],
            "servers": [{"id": 1}, {"id": 2}],
        }
    ]
    
    response = client.get("/api/v1/online/aggregate/all-routers")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verifica totais consolidados
    assert data["total"] == 180  # 100 + 80
    assert data["ringing"] == 18  # 10 + 8
    assert data["talking"] == 35  # 20 + 15
    
    # Verifica contadores de listas
    assert data["clients_count"] == 4  # 2 clientes de cada router
    assert data["routes_count"] == 6  # 3 rotas de cada router
    assert data["servers_count"] == 4  # 2 servidores de cada router
    
    # Verifica top_clients - deve ter consolidado Client A de ambos routers
    assert len(data["top_clients"]) == 3
    assert data["top_clients"][0]["name"] == "Client A"  # 90 total (50+40)
    assert data["top_clients"][0]["total"] == 90
    assert data["top_clients"][0]["ringing"] == 9  # 5+4
    assert data["top_clients"][0]["talking"] == 18  # 10+8
    assert data["top_clients"][1]["name"] == "Client B"  # 50 total
    assert data["top_clients"][1]["total"] == 50
    
    # Verifica routers summary
    assert len(data["routers"]) == 2
    assert data["routers"][0]["status"] == "ok"
    assert data["routers"][1]["status"] == "ok"
    
    # Verifica sem falhas
    assert len(data["failures"]) == 0


@patch("app.services.online_calls_service.list_routers")
@patch("app.services.online_calls_service.get_online_aggregate_by_router_id")
def test_get_online_aggregate_all_routers_partial_failure(mock_get_online, mock_list_routers):
    """Testa agregação com falha parcial de um router."""
    from app.integrations.nextrouter.exceptions import NextRouterTimeoutError
    from app.schemas.router import RouterOut
    
    # Mock dos routers
    mock_list_routers.return_value = [
        RouterOut(id=1, name="Router 1", slug="router-1", ip="192.168.1.1",
                  base_url="https://192.168.1.1", is_active=True, verify_tls=False),
        RouterOut(id=2, name="Router 2", slug="router-2", ip="192.168.1.2",
                  base_url="https://192.168.1.2", is_active=True, verify_tls=False),
    ]
    
    # Primeiro router OK, segundo falha
    mock_get_online.side_effect = [
        {
            "total": 100,
            "ringint": 10,
            "talking": 20,
            "clients": [
                {"cliente": "Client A", "total": 100, "ringing": 10, "talking": 20},
            ],
            "routes": [{"id": 1}],
            "servers": [{"id": 1}],
        },
        NextRouterTimeoutError("Timeout")
    ]
    
    response = client.get("/api/v1/online/aggregate/all-routers")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verifica que totais incluem apenas router OK
    assert data["total"] == 100
    assert data["ringing"] == 10
    assert data["talking"] == 20
    
    # Verifica contadores de listas (só router OK)
    assert data["clients_count"] == 1
    assert data["routes_count"] == 1
    assert data["servers_count"] == 1
    
    # Verifica routers summary
    assert len(data["routers"]) == 2
    assert data["routers"][0]["status"] == "ok"
    assert data["routers"][1]["status"] == "failed"
    
    # Verifica falhas
    assert len(data["failures"]) == 1
    assert data["failures"][0]["router_id"] == 2
    assert "Timeout" in data["failures"][0]["error"]


@patch("app.services.online_calls_service.list_routers")
@patch("app.services.online_calls_service.get_online_aggregate_by_router_id")
def test_online_aggregate_no_credentials_exposed(mock_get_online, mock_list_routers):
    """Testa que credenciais não aparecem na resposta."""
    from app.schemas.router import RouterOut
    
    # Mock dos routers
    mock_list_routers.return_value = [
        RouterOut(id=1, name="Router 1", slug="router-1", ip="192.168.1.1",
                  base_url="https://192.168.1.1", is_active=True, verify_tls=False),
    ]
    
    mock_get_online.return_value = {
        "total": 100,
        "ringint": 10,
        "talking": 20,
        "clients": [{"cliente": "Client A", "total": 100, "ringing": 10, "talking": 20}],
        "routes": [{"id": 1}],
        "servers": [{"id": 1}],
    }
    
    response = client.get("/api/v1/online/aggregate/all-routers")
    
    assert response.status_code == 200
    
    # Serializa e verifica que não há tokens/keys
    serialized = str(response.json()).lower()
    assert "token" not in serialized
    assert "key" not in serialized
    assert "password" not in serialized


@patch("app.services.online_calls_service.list_routers")
@patch("app.services.online_calls_service.get_online_aggregate_by_router_id")
def test_get_online_aggregate_all_routers_top_clients_order(mock_get_online, mock_list_routers):
    """Testa ordenação de top_clients por total descendente."""
    from app.schemas.router import RouterOut
    
    # Mock dos routers
    mock_list_routers.return_value = [
        RouterOut(id=1, name="Router 1", slug="router-1", ip="192.168.1.1",
                  base_url="https://192.168.1.1", is_active=True, verify_tls=False),
    ]
    
    mock_get_online.return_value = {
        "total": 100,
        "ringint": 10,
        "talking": 20,
        "clients": [
            {"cliente": "Client Z", "total": 30, "ringing": 3, "talking": 6},
            {"cliente": "Client A", "total": 50, "ringing": 5, "talking": 10},
            {"cliente": "Client M", "total": 20, "ringing": 2, "talking": 4},
        ],
        "routes": [{"id": 1}],
        "servers": [{"id": 1}],
    }
    
    response = client.get("/api/v1/online/aggregate/all-routers")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verifica ordem (descendente por total)
    assert data["top_clients"][0]["name"] == "Client A"  # 50
    assert data["top_clients"][1]["name"] == "Client Z"  # 30
    assert data["top_clients"][2]["name"] == "Client M"  # 20


@patch("app.services.online_calls_service.list_routers")
@patch("app.services.online_calls_service.get_online_aggregate_by_router_id")
def test_get_online_aggregate_with_fallback_ringing(mock_get_online, mock_list_routers):
    """Testa fallback de 'ringing' quando 'ringint' não existe."""
    from app.schemas.router import RouterOut
    
    # Mock dos routers
    mock_list_routers.return_value = [
        RouterOut(id=1, name="Router 1", slug="router-1", ip="192.168.1.1",
                  base_url="https://192.168.1.1", is_active=True, verify_tls=False),
    ]
    
    # API retorna 'ringing' em vez de 'ringint'
    mock_get_online.return_value = {
        "total": 100,
        "ringing": 12,  # Sem ringint, deve usar ringing
        "talking": 20,
        "clients": [{"cliente": "Client A", "total": 100, "ringing": 12, "talking": 20}],
        "routes": [],
        "servers": [],
    }
    
    response = client.get("/api/v1/online/aggregate/all-routers")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verifica que usou o 'ringing' como fallback
    assert data["ringing"] == 12


@patch("app.services.online_calls_service.list_routers")
@patch("app.services.online_calls_service.get_online_aggregate_by_router_id")
def test_get_online_aggregate_with_cliente_name_fallback(mock_get_online, mock_list_routers):
    """Testa fallback para 'name' quando 'cliente' não existe."""
    from app.schemas.router import RouterOut
    
    # Mock dos routers
    mock_list_routers.return_value = [
        RouterOut(id=1, name="Router 1", slug="router-1", ip="192.168.1.1",
                  base_url="https://192.168.1.1", is_active=True, verify_tls=False),
    ]
    
    # API retorna 'name' em vez de 'cliente'
    mock_get_online.return_value = {
        "total": 100,
        "ringint": 10,
        "talking": 20,
        "clients": [
            {"name": "Client A", "total": 50, "ringing": 5, "talking": 10},
            {"name": "Client B", "total": 50, "ringing": 5, "talking": 10},
        ],
        "routes": [],
        "servers": [],
    }
    
    response = client.get("/api/v1/online/aggregate/all-routers")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verifica que consolidou clientes corretamente mesmo com 'name'
    assert len(data["top_clients"]) == 2
    assert data["top_clients"][0]["name"] == "Client A"
    assert data["top_clients"][0]["total"] == 50


@patch("app.services.online_calls_service.list_routers")
@patch("app.services.online_calls_service.get_online_aggregate_by_router_id")
def test_get_online_aggregate_status_ok_not_success(mock_get_online, mock_list_routers):
    """Testa que status é 'ok' e não 'success' para routers bem-sucedidos."""
    from app.schemas.router import RouterOut
    
    # Mock dos routers
    mock_list_routers.return_value = [
        RouterOut(id=1, name="Router 1", slug="router-1", ip="192.168.1.1",
                  base_url="https://192.168.1.1", is_active=True, verify_tls=False),
    ]
    
    mock_get_online.return_value = {
        "total": 100,
        "ringint": 10,
        "talking": 20,
        "clients": [],
        "routes": [],
        "servers": [],
    }
    
    response = client.get("/api/v1/online/aggregate/all-routers")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verifica que usa 'ok' e não 'success'
    assert data["routers"][0]["status"] == "ok"


@patch("app.services.online_calls_service.list_routers")
@patch("app.services.online_calls_service.get_online_aggregate_by_router_id")
def test_get_online_aggregate_with_empty_lists(mock_get_online, mock_list_routers):
    """Testa agregação com listas vazias de clients/routes/servers."""
    from app.schemas.router import RouterOut
    
    # Mock dos routers
    mock_list_routers.return_value = [
        RouterOut(id=1, name="Router 1", slug="router-1", ip="192.168.1.1",
                  base_url="https://192.168.1.1", is_active=True, verify_tls=False),
    ]
    
    mock_get_online.return_value = {
        "total": 0,
        "ringint": 0,
        "talking": 0,
        "clients": [],
        "routes": [],
        "servers": [],
    }
    
    response = client.get("/api/v1/online/aggregate/all-routers")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verifica contadores com listas vazias
    assert data["total"] == 0
    assert data["ringing"] == 0
    assert data["talking"] == 0
    assert data["clients_count"] == 0
    assert data["routes_count"] == 0
    assert data["servers_count"] == 0
    assert len(data["top_clients"]) == 0


# ============= Testes para funções de normalização =============

def test_normalize_route_item():
    """Testa normalização de item de rota."""
    from app.schemas.router import RouterOut
    
    router = RouterOut(id=1, name="Router 1", slug="router-1", ip="192.168.1.1",
                       base_url="https://192.168.1.1", is_active=True, verify_tls=False)
    
    item = {
        "id": "route_123",
        "cliente": "Route A",
        "chamando": 10,
        "falando": 20,
        "total": 30,
        "asr": 25.5,
        "acd": "1.2",
        "pdd": "100ms",
        "pdd_int": 100,
        "alerta_pdd": 150,
        "total_calls": 50,
        "talk_time": 1000,
    }
    
    result = normalize_route_item(item, router)
    
    assert result["router_id"] == 1
    assert result["router_name"] == "Router 1"
    assert result["route_id"] == "route_123"
    assert result["route_name"] == "Route A"
    assert result["total"] == 30
    assert result["ringing"] == 10
    assert result["talking"] == 20
    assert result["asr"] == 25.5
    assert result["acd"] == "1.2"
    assert result["pdd"] == "100ms"
    assert result["pdd_int"] == 100
    assert result["alerta_pdd"] == 150
    assert result["total_calls"] == 50
    assert result["talk_time"] == 1000
    assert result["pdd_alert"] is False  # 100 <= 150
    assert result["asr_alert"] is True   # 25.5 < 30


def test_normalize_route_item_fallbacks():
    """Testa fallbacks em normalização de rota."""
    from app.schemas.router import RouterOut
    
    router = RouterOut(id=2, name="Router 2", slug="router-2", ip="192.168.1.2",
                       base_url="https://192.168.1.2", is_active=True, verify_tls=False)
    
    item = {
        "id": "route_456",
        "name": "Route B",  # usa name em vez de cliente
        "ringing": 5,       # usa ringing em vez de chamando
        "talking": 15,      # usa talking em vez de falando
        "total": 20,
        "asr": 35.0,        # > 30, sem alerta
        "pdd_int": 200,
        "alerta_pdd": 150,  # 200 > 150, alerta
    }
    
    result = normalize_route_item(item, router)
    
    assert result["route_name"] == "Route B"
    assert result["ringing"] == 5
    assert result["talking"] == 15
    assert result["asr_alert"] is False  # 35 >= 30
    assert result["pdd_alert"] is True   # 200 > 150


def test_build_top_routes():
    """Testa construção de top routes consolidadas."""
    routes = [
        {
            "route_name": "Route A",
            "total": 100,
            "ringing": 10,
            "talking": 20,
            "asr": 25.0,
            "pdd_int": 100,
        },
        {
            "route_name": "Route A",
            "total": 50,
            "ringing": 5,
            "talking": 10,
            "asr": 30.0,
            "pdd_int": 120,
        },
        {
            "route_name": "Route B",
            "total": 80,
            "ringing": 8,
            "talking": 16,
            "asr": None,
            "pdd_int": 90,
        },
    ]
    
    result = build_top_routes(routes)
    
    assert len(result) == 2
    
    # Route A consolidada
    route_a = next(r for r in result if r["route_name"] == "Route A")
    assert route_a["total"] == 150  # 100 + 50
    assert route_a["ringing"] == 15  # 10 + 5
    assert route_a["talking"] == 30  # 20 + 10
    assert route_a["avg_asr"] == 27.5  # (25+30)/2
    assert route_a["max_pdd_int"] == 120
    
    # Route B
    route_b = next(r for r in result if r["route_name"] == "Route B")
    assert route_b["total"] == 80
    assert route_b["avg_asr"] is None  # sem valores
    
    # Ordenação por total desc
    assert result[0]["route_name"] == "Route A"
    assert result[1]["route_name"] == "Route B"


def test_normalize_server_item():
    """Testa normalização de item de servidor."""
    from app.schemas.router import RouterOut
    
    router = RouterOut(id=3, name="Router 3", slug="router-3", ip="192.168.1.3",
                       base_url="https://192.168.1.3", is_active=True, verify_tls=False)
    
    item = {
        "server_ip": "192.168.1.100",
        "total": 200,
        "cps": "10.5",
        "chamando": 15,
        "falando": 25,
    }
    
    result = normalize_server_item(item, router)
    
    assert result["router_id"] == 3
    assert result["router_name"] == "Router 3"
    assert result["server_ip"] == "192.168.1.100"
    assert result["total"] == 200
    assert result["cps"] == "10.5"
    assert result["chamando"] == 15
    assert result["falando"] == 25


def test_normalize_server_item_fallback_ip():
    """Testa fallback para 'ip' quando 'server_ip' não existe."""
    from app.schemas.router import RouterOut
    
    router = RouterOut(id=4, name="Router 4", slug="router-4", ip="192.168.1.4",
                       base_url="https://192.168.1.4", is_active=True, verify_tls=False)
    
    item = {
        "ip": "10.0.0.1",
        "total": 100,
        "cps": "5.0",
        "chamando": 10,
        "falando": 20,
    }
    
    result = normalize_server_item(item, router)
    
    assert result["server_ip"] == "10.0.0.1"
