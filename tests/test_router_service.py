from fastapi.testclient import TestClient

from app.main import app
from app.services.router_service import get_router_secret_by_router_id


client = TestClient(app)


def test_list_routers():
    response = client.get("/api/v1/routers")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)


def test_router_payload_does_not_expose_credentials():
    response = client.get("/api/v1/routers")

    assert response.status_code == 200

    data = response.json()

    serialized = str(data).lower()

    assert "token" not in serialized
    assert "api_token" not in serialized
    assert "key" not in serialized
    assert "password" not in serialized


def test_router_options():
    response = client.get("/api/v1/routers/options")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)


def test_get_router_not_found():
    response = client.get("/api/v1/routers/999999")

    assert response.status_code == 404


def test_get_router_secret_by_id_not_found():
    """Testa busca de router com credenciais - não encontrado."""
    result = get_router_secret_by_router_id(999)
    assert result is None


def test_get_router_secret_by_id_invalid():
    """Testa busca com ID inválido."""
    result = get_router_secret_by_router_id(-1)
    assert result is None
    
    result = get_router_secret_by_router_id(0)
    assert result is None