from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.core import auth as auth_core
from app.core.security import create_access_token
from app.main import app


client = TestClient(app)


class FakeResult:
    def __init__(self, user):
        self.user = user

    def scalar_one_or_none(self):
        return self.user


class FakeDb:
    def __init__(self, user):
        self.user = user

    def execute(self, statement):
        return FakeResult(self.user)


def fake_user(role: str):
    return SimpleNamespace(
        id=1,
        name="Auth User",
        email="auth@example.test",
        user_type="employee",
        role=role,
        is_active=True,
        customer_id=None,
    )


def auth_headers(monkeypatch, role: str = "admin") -> dict[str, str]:
    monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret")
    token = create_access_token(
        subject="1",
        extra_data={
            "email": "auth@example.test",
            "user_type": "employee",
            "role": role,
        },
    )
    return {"Authorization": f"Bearer {token}"}


def override_db(user):
    def dependency():
        yield FakeDb(user)

    app.dependency_overrides[auth_core.get_db] = dependency


def test_business_endpoint_without_token_returns_401(auth_override):
    auth_override.disable()
    override_db(fake_user("admin"))

    response = client.get("/api/v1/routers")

    app.dependency_overrides.pop(auth_core.get_db, None)
    assert response.status_code == 401


def test_business_endpoint_with_valid_token_and_permission_returns_200(
    auth_override,
    monkeypatch,
):
    auth_override.disable()
    override_db(fake_user("suporte"))

    response = client.get("/api/v1/routers", headers=auth_headers(monkeypatch, "suporte"))

    app.dependency_overrides.pop(auth_core.get_db, None)
    assert response.status_code == 200


def test_business_endpoint_with_role_without_permission_returns_403(
    auth_override,
    monkeypatch,
):
    auth_override.disable()
    override_db(fake_user("client_viewer"))

    response = client.get(
        "/api/v1/routers",
        headers=auth_headers(monkeypatch, "client_viewer"),
    )

    app.dependency_overrides.pop(auth_core.get_db, None)
    assert response.status_code == 403


def test_health_and_login_remain_public(auth_override):
    auth_override.disable()

    health_response = client.get("/api/v1/health")
    login_response = client.post("/auth/login", json={})

    assert health_response.status_code == 200
    assert login_response.status_code == 422


def test_metrics_requires_metrics_permission(auth_override, monkeypatch):
    auth_override.disable()
    override_db(fake_user("noc"))

    response = client.get("/metrics", headers=auth_headers(monkeypatch, "noc"))

    app.dependency_overrides.pop(auth_core.get_db, None)
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]


def test_metrics_without_token_returns_401(auth_override):
    auth_override.disable()
    override_db(fake_user("noc"))

    response = client.get("/metrics")

    app.dependency_overrides.pop(auth_core.get_db, None)
    assert response.status_code == 401
