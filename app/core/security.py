import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from pwdlib import PasswordHash


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

password_hash = PasswordHash.recommended()


ROLE_PERMISSIONS = {
    "admin": [
        "*",
        "dashboard:noc:view",
        "dashboard:client:view",
        "routers:read",
        "routers:view",
        "routers:manage",
        "customers:read",
        "customers:view",
        "customers:manage",
        "reports:read",
        "noc:read",
        "metrics:read",
        "finance:view",
        "finance:manage",
        "infrastructure:view",
        "users:view",
        "users:manage",
    ],
    "noc": [
        "dashboard:noc:view",
        "routers:read",
        "routers:view",
        "noc:read",
        "metrics:read",
        "infrastructure:view",
    ],
    "financeiro": [
        "reports:read",
        "finance:view",
        "finance:manage",
    ],
    "suporte": [
        "customers:read",
        "customers:view",
        "routers:read",
        "routers:view",
    ],
    "client_admin": [
        "dashboard:client:view",
    ],
    "client_viewer": [
        "dashboard:client:view",
    ],
}


def get_jwt_secret_key() -> str:
    secret = os.getenv("JWT_SECRET_KEY")

    if not secret:
        raise RuntimeError(
            "JWT_SECRET_KEY não configurada. "
            "Defina uma variável de ambiente antes de rodar autenticação."
        )

    return secret


def get_password_hash(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return password_hash.verify(plain_password, hashed_password)
    except Exception:
        return False


def get_permissions_for_role(role: str) -> list[str]:
    return ROLE_PERMISSIONS.get(role, [])


def create_access_token(
    subject: str,
    extra_data: Optional[Dict[str, Any]] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    payload: Dict[str, Any] = {
        "sub": subject,
        "exp": expire,
    }

    if extra_data:
        payload.update(extra_data)

    return jwt.encode(payload, get_jwt_secret_key(), algorithm=ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, get_jwt_secret_key(), algorithms=[ALGORITHM])
    except JWTError as exc:
        raise ValueError("Token inválido ou expirado.") from exc
