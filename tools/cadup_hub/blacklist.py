"""Heuristics for blocking artificial or spam-like CADUP numbers."""

from __future__ import annotations

from tools.cadup_hub.normalizacao import extrair_ddd_prefixo_mcdu, limpar_numero


PREFIXOS_BLACKLIST_EXATOS = {
    "0000",
    "1111",
    "2222",
    "3333",
    "4444",
    "5555",
    "6666",
    "7777",
    "8888",
    "9999",
}

FINAIS_BLACKLIST = {
    "0000",
    "1111",
    "2222",
    "3333",
    "4444",
    "5555",
    "6666",
    "7777",
    "8888",
    "9999",
    "1234",
    "4321",
}


def prefixo_artificial(prefixo: str | int, ddd: str | int | None = None) -> bool:
    prefix = limpar_numero(prefixo)
    ddd_text = limpar_numero(ddd or "")
    if prefix in PREFIXOS_BLACKLIST_EXATOS:
        return True
    return ddd_text == "11" and prefix.startswith("9500")


def final_artificial(mcdu: str | int) -> bool:
    return limpar_numero(mcdu).zfill(4)[-4:] in FINAIS_BLACKLIST


def numero_tem_padrao_spam(numero: str | int) -> bool:
    partes = extrair_ddd_prefixo_mcdu(numero)
    if partes is None:
        return True
    return prefixo_artificial(partes["prefixo"], partes["ddd"]) or final_artificial(partes["mcdu"])

