from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.db.session import get_db
from app.core.security import (
    create_access_token,
    get_permissions_for_role,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import CurrentUser, TokenResponse, UserLogin


router = APIRouter(prefix="/auth", tags=["Auth"])


def build_current_user(user: User) -> CurrentUser:
    return CurrentUser(
        id=user.id,
        name=user.name,
        email=user.email,
        user_type=user.user_type,
        role=user.role,
        permissions=get_permissions_for_role(user.role),
        customer_id=user.customer_id,
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)) -> TokenResponse:
    email = payload.email.strip().lower()

    user = db.execute(
        select(User).where(User.email == email)
    ).scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo.",
        )

    access_token = create_access_token(
        subject=str(user.id),
        extra_data={
            "email": user.email,
            "user_type": user.user_type,
            "role": user.role,
        },
    )

    return TokenResponse(
        access_token=access_token,
        user=build_current_user(user),
    )


@router.get("/me", response_model=CurrentUser)
def me(current_user: User = Depends(get_current_user)) -> CurrentUser:
    return build_current_user(current_user)
