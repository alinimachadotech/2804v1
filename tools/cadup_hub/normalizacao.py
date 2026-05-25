"""Brazilian phone number normalization for CADUP lookups."""

from __future__ import annotations

import re


def limpar_numero(numero: str | int) -> str:
    return re.sub(r"\D+", "", str(numero or ""))


def normalizar_numero_brasil(numero: str | int) -> str | None:
    digits = limpar_numero(numero)
    if digits.startswith("55") and len(digits) in {12, 13}:
        digits = digits[2:]
    if len(digits) not in {10, 11}:
        return None
    return digits


def extrair_ddd_prefixo_mcdu(numero: str | int) -> dict[str, str] | None:
    nacional = normalizar_numero_brasil(numero)
    if nacional is None:
        return None

    return {
        "ddd": nacional[:2],
        "prefixo": nacional[2:-4],
        "mcdu": nacional[-4:],
        "numero": nacional,
    }

