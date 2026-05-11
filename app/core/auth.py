from typing import Callable, Iterable, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import decode_access_token, get_permissions_for_role
from app.models.user import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_access_token(token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sem identificação de usuário.",
        )

    user = db.execute(
        select(User).where(User.id == int(user_id))
    ).scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo.",
        )

    return user


def require_employee(current_user: User = Depends(get_current_user)) -> User:
    if current_user.user_type != "employee":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso permitido apenas para funcionários.",
        )

    return current_user


def require_client(current_user: User = Depends(get_current_user)) -> User:
    if current_user.user_type != "client":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso permitido apenas para clientes.",
        )

    return current_user


def require_roles(allowed_roles: Iterable[str]) -> Callable:
    allowed = set(allowed_roles)

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Perfil sem permissão para acessar este recurso.",
            )

        return current_user

    return dependency


def require_permissions(required_permissions: Iterable[str]) -> Callable:
    required = set(required_permissions)

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        user_permissions = set(get_permissions_for_role(current_user.role))

        if "*" in user_permissions:
            return current_user

        if not required.issubset(user_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuário sem permissão suficiente.",
            )

        return current_user

    return dependency


def get_customer_scope(
    current_user: User,
    requested_customer_id: Optional[int] = None,
) -> Optional[int]:
    """
    Regra central:
    - Funcionário pode consultar vários clientes conforme permissões.
    - Cliente só pode consultar o próprio customer_id.
    """

    if current_user.user_type == "employee":
        return requested_customer_id

    if current_user.user_type == "client":
        if current_user.customer_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuário cliente sem customer_id vinculado.",
            )

        if requested_customer_id is not None and requested_customer_id != current_user.customer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cliente não pode acessar dados de outro cliente.",
            )

        return current_user.customer_id

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Tipo de usuário inválido.",
    )
