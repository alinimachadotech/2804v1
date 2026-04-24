from fastapi.testclient import TestClient

from app.main import app


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