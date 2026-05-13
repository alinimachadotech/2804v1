"""Conversao segura de erros de servicos para HTTP."""

from fastapi import HTTPException

from app.core.settings import settings
from app.integrations.nextrouter.exceptions import (
    NextRouterAuthError,
    NextRouterBadRequestError,
    NextRouterError,
    NextRouterNotFoundError,
    NextRouterPayloadTooLargeError,
    NextRouterRateLimitError,
    NextRouterServerError,
    NextRouterTimeoutError,
    NextRouterValidationError,
)
from app.services.balance_service import RouterNotFoundError


def _is_local_env() -> bool:
    return str(settings.app_env).strip().lower() in {"local", "dev", "development"}


def _nextrouter_detail(default_message: str, exc: Exception):
    diagnostics = getattr(exc, "diagnostics", None) or {}
    if not _is_local_env() or not diagnostics:
        return default_message

    return {
        "message": default_message,
        "upstream_status_code": diagnostics.get("status_code"),
        "upstream_body_preview": diagnostics.get("body_preview"),
        "endpoint": diagnostics.get("endpoint"),
        "path": diagnostics.get("path"),
    }


def handle_service_error(exc: Exception):
    if isinstance(exc, RouterNotFoundError):
        raise HTTPException(status_code=404, detail="Router nao encontrado")
    if isinstance(exc, NextRouterBadRequestError):
        raise HTTPException(status_code=400, detail="Requisicao invalida para NextRouter")
    if isinstance(exc, NextRouterAuthError):
        raise HTTPException(status_code=403, detail="Falha de autenticacao com NextRouter")
    if isinstance(exc, NextRouterNotFoundError):
        raise HTTPException(status_code=404, detail="Recurso nao encontrado no NextRouter")
    if isinstance(exc, NextRouterPayloadTooLargeError):
        raise HTTPException(status_code=413, detail="Payload grande demais para NextRouter")
    if isinstance(exc, NextRouterValidationError):
        raise HTTPException(status_code=422, detail="NextRouter recusou a validacao")
    if isinstance(exc, NextRouterRateLimitError):
        raise HTTPException(status_code=429, detail="Rate limit do NextRouter excedido")
    if isinstance(exc, NextRouterTimeoutError):
        raise HTTPException(status_code=504, detail="Timeout ao comunicar com NextRouter")
    if isinstance(exc, NextRouterServerError):
        raise HTTPException(
            status_code=502,
            detail=_nextrouter_detail("Erro 5xx do NextRouter", exc),
        )
    if isinstance(exc, NextRouterError):
        raise HTTPException(
            status_code=502,
            detail=_nextrouter_detail("Erro ao comunicar com NextRouter", exc),
        )
    raise exc
