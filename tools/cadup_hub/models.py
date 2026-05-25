"""Internal CADUP domain models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CadupRange:
    operadora: str
    cnpj: str | None
    cn: str
    prefixo: str
    mcdu_ini: int
    mcdu_fim: int
    cidade: str | None
    uf: str | None
    tipo: str | None
    rn1: str | None

    @property
    def capacidade(self) -> int:
        return max(0, int(self.mcdu_fim) - int(self.mcdu_ini) + 1)

    def contem_mcdu(self, mcdu: str | int) -> bool:
        value = int(mcdu)
        return int(self.mcdu_ini) <= value <= int(self.mcdu_fim)

    @property
    def chave_prefixo(self) -> str:
        return f"{self.cn}{self.prefixo}"

    @classmethod
    def from_row(cls, row: dict) -> "CadupRange":
        return cls(
            operadora=str(row.get("operadora") or ""),
            cnpj=row.get("cnpj"),
            cn=str(row.get("cn") or ""),
            prefixo=str(row.get("prefixo") or ""),
            mcdu_ini=int(row.get("mcdu_ini") or 0),
            mcdu_fim=int(row.get("mcdu_fim") or 0),
            cidade=row.get("cidade"),
            uf=row.get("uf"),
            tipo=row.get("tipo"),
            rn1=row.get("rn1"),
        )

