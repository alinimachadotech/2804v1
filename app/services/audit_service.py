"""Auditoria opcional para acoes de negocio."""

from __future__ import annotations

import logging
from typing import Any


logger = logging.getLogger(__name__)

SENSITIVE_KEY_PARTS = ("token", "key", "password", "senha", "secret")


def sanitize_payload(value: Any) -> Any:
    """Remove campos sensiveis antes de retornar ou auditar dados."""
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key).lower()
            if any(part in key_text for part in SENSITIVE_KEY_PARTS):
                continue
            sanitized[str(key)] = sanitize_payload(item)
        return sanitized

    if isinstance(value, list):
        return [sanitize_payload(item) for item in value]

    return value


def _get_audit_model():
    try:
        from app.models import audit as audit_models
    except Exception:
        return None

    for model_name in ("AuditLog", "AuditEvent", "Audit"):
        model = getattr(audit_models, model_name, None)
        if model is not None and hasattr(model, "__table__"):
            return model

    return None


def record_audit_action(
    *,
    action: str,
    router_name: str,
    customer_id: str,
    before: Any | None = None,
    after: Any | None = None,
    metadata: dict[str, Any] | None = None,
    db: Any | None = None,
) -> bool:
    """Registra auditoria se houver modelo e sessao disponiveis."""
    model = _get_audit_model()
    if db is None or model is None:
        return False

    values = {
        "action": action,
        "router_name": router_name,
        "customer_id": str(customer_id),
        "before": sanitize_payload(before),
        "after": sanitize_payload(after),
        "metadata": sanitize_payload(metadata or {}),
    }

    columns = set(model.__table__.columns.keys())
    payload = {key: value for key, value in values.items() if key in columns}

    if not payload:
        return False

    try:
        db.add(model(**payload))
        db.commit()
        return True
    except Exception:
        logger.warning("Falha ao registrar auditoria", exc_info=True)
        try:
            db.rollback()
        except Exception:
            pass
        return False
