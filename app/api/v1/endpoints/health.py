from fastapi import APIRouter, HTTPException, status

from app.core.settings import settings
from app.db.session import ping_database


router = APIRouter(prefix="/api/v1", tags=["Health"])
legacy_router = APIRouter(include_in_schema=False)


def health_payload() -> dict:
    return {
        "status": "ok",
        "service": "gerax-manager-api",
        "version": settings.app_version,
        "environment": settings.app_env,
    }


@legacy_router.get("/")
def home():
    return {"message": "Funcionando"}


@legacy_router.get("/ping")
def ping():
    return {"message": "pong"}


@legacy_router.get("/health")
def legacy_health():
    return health_payload()


@router.get("/health")
def health():
    return health_payload()


@router.get("/ready")
def ready():
    db_ok, db_message = ping_database()

    if not db_ok:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "database": "error",
                "reason": db_message,
            },
        )

    return {
        "status": "ready",
        "service": "gerax-manager-api",
        "database": "ok",
    }
