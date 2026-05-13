from types import SimpleNamespace

import pytest

from app.core.auth import get_current_user
from app.main import app


def test_user(role: str = "admin"):
    return SimpleNamespace(
        id=1,
        name="Test User",
        email="test@example.test",
        user_type="employee",
        role=role,
        is_active=True,
        customer_id=None,
    )


@pytest.fixture(autouse=True)
def authenticated_api_user():
    app.dependency_overrides[get_current_user] = lambda: test_user("admin")
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def auth_override():
    def as_role(role: str):
        app.dependency_overrides[get_current_user] = lambda: test_user(role)

    def disable():
        app.dependency_overrides.pop(get_current_user, None)

    return SimpleNamespace(as_role=as_role, disable=disable)
