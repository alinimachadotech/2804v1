"""Parsers e normalizadores da API NextRouter."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any, Callable


MONEY_ZERO = Decimal("0")


def parse_money(value: Any, default: Decimal | None = MONEY_ZERO) -> Decimal:
    """Converte valores monetarios da NextRouter para Decimal.

    Aceita formatos como "177,90", "177.90", "1.177,90" e "1,177.90".
    Nunca usa float para calcular dinheiro.
    """
    if value is None:
        if default is None:
            raise ValueError("Valor monetario ausente")
        return default

    if isinstance(value, Decimal):
        return value

    if isinstance(value, int):
        return Decimal(value)

    if isinstance(value, float):
        return Decimal(str(value))

    text = str(value).strip()
    if not text:
        if default is None:
            raise ValueError("Valor monetario vazio")
        return default

    is_negative = text.startswith("(") and text.endswith(")")
    text = text.strip("()")
    text = re.sub(r"[^\d,.\-]", "", text)

    if not text or text in {"-", ",", "."}:
        if default is None:
            raise ValueError(f"Valor monetario invalido: {value!r}")
        return default

    last_comma = text.rfind(",")
    last_dot = text.rfind(".")

    if last_comma >= 0 and last_dot >= 0:
        if last_comma > last_dot:
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif last_comma >= 0:
        text = text.replace(".", "").replace(",", ".")

    if is_negative and not text.startswith("-"):
        text = f"-{text}"

    try:
        return Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"Valor monetario invalido: {value!r}") from exc


def format_money(value: Any) -> str:
    """Formata um valor monetario para envio sem passar por float."""
    return str(parse_money(value, default=None))


def first_payload_item(payload: Any) -> dict[str, Any]:
    """Extrai o primeiro item util de respostas comuns da NextRouter."""
    if isinstance(payload, list):
        return payload[0] if payload and isinstance(payload[0], dict) else {}

    if not isinstance(payload, dict):
        return {}

    for key in ("data", "result", "results", "rows", "items"):
        value = payload.get(key)
        if isinstance(value, list):
            return value[0] if value and isinstance(value[0], dict) else {}
        if isinstance(value, dict):
            return value

    return payload


def payload_items(payload: Any) -> list[dict[str, Any]]:
    """Extrai listas de dicionarios de payloads variados."""
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]

    if not isinstance(payload, dict):
        return []

    for key in ("data", "result", "results", "rows", "items"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        if isinstance(value, dict):
            return [value]

    return [payload]


def payload_data_key(payload: Any) -> str | None:
    """Identifica a chave de colecao usada no payload original."""
    if not isinstance(payload, dict):
        return None

    for key in ("data", "result", "results", "rows", "items"):
        value = payload.get(key)
        if isinstance(value, (list, dict)):
            return key

    return None


def pick(data: dict[str, Any], *keys: str) -> Any:
    """Retorna o primeiro campo existente e nao vazio."""
    for key in keys:
        value = data.get(key)
        if value not in (None, ""):
            return value
    return None


def normalize_customer_balance(payload: Any, customer_id: Any | None = None) -> dict[str, Any]:
    """Normaliza saldo de cliente para contrato interno."""
    item = first_payload_item(payload)
    raw_customer_id = customer_id or pick(item, "customer_id", "id_customer", "id_cliente", "id")
    raw_usable_balance = pick(item, "usable_balance")
    raw_customer_balance = pick(item, "customer_balance")
    raw_customer_limit = pick(item, "customer_limit")
    raw_balance = pick(
        item,
        "usable_balance",
        "customer_balance",
        "balance",
        "saldo",
        "credit",
        "credito",
        "amount",
        "valor",
    )

    usable_balance = (
        parse_money(raw_usable_balance, default=None)
        if raw_usable_balance is not None
        else None
    )
    customer_balance = (
        parse_money(raw_customer_balance, default=None)
        if raw_customer_balance is not None
        else None
    )
    customer_limit = (
        parse_money(raw_customer_limit, default=None)
        if raw_customer_limit is not None
        else None
    )

    return {
        "customer_id": str(raw_customer_id) if raw_customer_id is not None else None,
        "balance": parse_money(raw_balance),
        "usable_balance": usable_balance,
        "customer_balance": customer_balance,
        "customer_limit": customer_limit,
        "tipo_tar": pick(item, "tipo_tar"),
    }


def normalize_customer(payload: Any) -> dict[str, Any]:
    """Normaliza dados basicos de cliente."""
    item = first_payload_item(payload)
    raw_customer_id = pick(item, "customer_id", "id_customer", "id_cliente", "id")
    return {
        "customer_id": raw_customer_id,
        "name": pick(
            item,
            "nome_fantasia",
            "razao_social",
            "name",
            "nome",
            "cliente",
            "customer_id",
            "id_customer",
            "id_cliente",
            "id",
        )
        or raw_customer_id,
        "status": pick(item, "status", "situacao", "active", "ativo"),
        "raw": item,
    }


def normalize_credit_history(payload: Any) -> list[dict[str, Any]]:
    """Normaliza historico de credito, convertendo valores para Decimal."""
    normalized: list[dict[str, Any]] = []
    for item in payload_items(payload):
        entry = dict(item)
        value = pick(entry, "amount", "valor", "credit", "credito")
        if value is not None:
            entry["amount"] = parse_money(value)
        normalized.append(entry)
    return normalized


def normalize_money_collection(
    payload: Any,
    money_keys: tuple[str, ...] = ("amount", "valor", "balance", "saldo", "profit", "lucro", "cost", "custo"),
) -> list[dict[str, Any]]:
    """Normaliza colecoes convertendo campos monetarios conhecidos."""
    normalized: list[dict[str, Any]] = []
    for item in payload_items(payload):
        entry = dict(item)
        for key in money_keys:
            if key in entry and entry[key] not in (None, ""):
                entry[key] = parse_money(entry[key])
        normalized.append(entry)
    return normalized


def normalize_report_payload(payload: Any) -> dict[str, Any]:
    """Preserva totais/cabecalhos de relatorios e normaliza a colecao em data."""
    data = normalize_money_collection(payload)

    if not isinstance(payload, dict):
        return {"data": data}

    collection_key = payload_data_key(payload)
    report = {
        str(key): value
        for key, value in payload.items()
        if key != collection_key
    }
    report["data"] = data
    return report


def normalize_passthrough(payload: Any) -> Any:
    """Mantem payload original quando nao ha contrato interno especifico."""
    return payload


Normalizer = Callable[[Any], Any]
