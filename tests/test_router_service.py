from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.core.settings import RouterSettings
from app.main import app
from app.services import router_service
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


def test_router_endpoint_uses_domain_base_url_and_router_verify_tls(monkeypatch):
    router_config = RouterSettings(
        name="Router21/gerax",
        ip="38.210.211.21",
        host="plataforma4.geraxtelecom.com.br",
        base_url="https://plataforma4.geraxtelecom.com.br",
        verify_tls=True,
        token=SecretStr("CHANGE_ME_TOKEN"),
        key=SecretStr("CHANGE_ME_KEY"),
    )
    fake_settings = type(
        "FakeSettings",
        (),
        {
            "routers": [router_config],
            "nextrouter_verify_ssl": False,
        },
    )()
    monkeypatch.setattr(router_service, "settings", fake_settings)

    response = client.get("/api/v1/routers")

    assert response.status_code == 200
    data = response.json()
    assert data == [
        {
            "id": 1,
            "name": "Router21/gerax",
            "slug": "router21-gerax-38-210-211-21",
            "ip": "38.210.211.21",
            "base_url": "https://plataforma4.geraxtelecom.com.br",
            "is_active": True,
            "verify_tls": True,
        }
    ]
    serialized = str(data).lower()
    assert "change_me_token" not in serialized
    assert "change_me_key" not in serialized


def test_router_endpoint_uses_host_when_base_url_is_absent(monkeypatch):
    router_config = RouterSettings(
        name="Router21/gerax",
        ip="38.210.211.21",
        host="plataforma4.geraxtelecom.com.br",
        token=SecretStr("CHANGE_ME_TOKEN"),
        key=SecretStr("CHANGE_ME_KEY"),
    )
    fake_settings = type(
        "FakeSettings",
        (),
        {
            "routers": [router_config],
            "nextrouter_verify_ssl": True,
        },
    )()
    monkeypatch.setattr(router_service, "settings", fake_settings)

    response = client.get("/api/v1/routers")

    assert response.status_code == 200
    assert response.json()[0]["base_url"] == "https://plataforma4.geraxtelecom.com.br"
    assert response.json()[0]["verify_tls"] is True


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
