"""CADUP Hub service layer."""

from __future__ import annotations

import csv
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from tools.cadup_hub.blacklist import numero_tem_padrao_spam, prefixo_artificial
from tools.cadup_hub.models import CadupRange
from tools.cadup_hub.normalizacao import extrair_ddd_prefixo_mcdu
from tools.cadup_hub.repository import CadupRepository


class CadupRepositoryProtocol(Protocol):
    def buscar_ranges(
        self,
        empresa: str | None = None,
        ddd: str | int | None = None,
        tipo: str | None = None,
        uf: str | None = None,
        cidade: str | None = None,
    ) -> list[CadupRange]: ...
    def consultar_numero(self, numero: str | int) -> CadupRange | None: ...
    def capacidade_por_empresa(self, empresa: str, tipo: str | None = None) -> dict[str, Any]: ...
    def ranking_empresas(self, tipo: str | None = None, ddd: str | int | None = None) -> list[dict[str, Any]]: ...
    def criar_lote(
        self,
        *,
        nome: str,
        filtros: dict[str, Any],
        quantidade_solicitada: int,
        created_by: str | None = None,
    ) -> int: ...
    def atualizar_lote(self, lote_id: int, *, status: str, quantidade_gerada: int) -> None: ...
    def numero_ja_gerado(self, numero: str) -> bool: ...
    def numero_em_blocklist(self, numero: str, ddd: str, prefixo: str, mcdu: str) -> bool: ...
    def salvar_numeros_gerados(self, lote_id: int, numeros: list[dict[str, Any]]) -> None: ...
    def registrar_audit_log(
        self,
        *,
        action: str,
        entity: str,
        entity_id: str | None = None,
        metadata_json: str | None = None,
        actor: str | None = None,
    ) -> None: ...
    def consultar_lote(self, lote_id: int) -> dict[str, Any] | None: ...


@dataclass(frozen=True)
class GeracaoCadupRequest:
    nome_lote: str
    quantidade: int
    saida: str
    empresa: str | None = None
    ddd: str | None = None
    tipo: str | None = None
    uf: str | None = None
    cidade: str | None = None
    limite_por_faixa: int = 10
    com_55: bool = False
    cabecalho: str = "destino"
    sem_blacklist: bool = False
    modo: str = "aleatorio"
    bloquear_prefixos: str | None = None
    seed: int | None = None


class CadupGenerationError(ValueError):
    pass


class CadupService:
    def __init__(self, repository: CadupRepositoryProtocol | None = None):
        self.repository = repository or CadupRepository()

    def consultar_numero(self, numero: str | int) -> dict[str, Any]:
        partes = extrair_ddd_prefixo_mcdu(numero)
        if partes is None:
            return {"valido": False, "motivo": "Numero deve ter 10 ou 11 digitos nacionais"}

        range_encontrado = self.repository.consultar_numero(numero)
        return {
            "valido": True,
            "numero": partes["numero"],
            "ddd": partes["ddd"],
            "prefixo": partes["prefixo"],
            "mcdu": partes["mcdu"],
            "blacklist": numero_tem_padrao_spam(numero),
            "range": range_encontrado,
        }

    def capacidade_por_empresa(self, empresa: str, tipo: str | None = None) -> dict[str, Any]:
        return self.repository.capacidade_por_empresa(empresa, tipo=tipo)

    def ranking_empresas(self, tipo: str | None = None, ddd: str | int | None = None) -> list[dict[str, Any]]:
        return self.repository.ranking_empresas(tipo=tipo, ddd=ddd)

    def consultar_lote(self, lote_id: int) -> dict[str, Any] | None:
        return self.repository.consultar_lote(lote_id)

    def gerar_lista(self, request: GeracaoCadupRequest) -> dict[str, Any]:
        self._validar_request_geracao(request)
        filtros = {
            "empresa": request.empresa,
            "ddd": request.ddd,
            "tipo": request.tipo,
            "uf": request.uf,
            "cidade": request.cidade,
            "limite_por_faixa": request.limite_por_faixa,
            "com_55": request.com_55,
            "sem_blacklist": request.sem_blacklist,
            "modo": request.modo,
            "bloquear_prefixos": request.bloquear_prefixos,
        }
        filtros_json = json.dumps(filtros, ensure_ascii=False, sort_keys=True)
        lote_id = self.repository.criar_lote(
            nome=request.nome_lote,
            filtros={**filtros, "filtros_json": filtros_json},
            quantidade_solicitada=request.quantidade,
        )

        numeros: list[dict[str, Any]] = []
        try:
            ranges = self.repository.buscar_ranges(
                empresa=request.empresa,
                ddd=request.ddd,
                tipo=request.tipo,
                uf=request.uf,
                cidade=request.cidade,
            )
            if not ranges:
                raise CadupGenerationError("Nenhuma faixa CADUP ativa encontrada para os filtros informados.")

            numeros = self._selecionar_numeros(ranges, request)
            if len(numeros) < request.quantidade:
                raise CadupGenerationError(
                    "Quantidade solicitada maior que a capacidade util disponivel "
                    f"apos filtros e bloqueios. Disponivel: {len(numeros)}."
                )

            self.repository.salvar_numeros_gerados(lote_id, numeros)
            self._escrever_csv(request.saida, request.cabecalho, [item["numero"] for item in numeros])
            self.repository.atualizar_lote(lote_id, status="concluido", quantidade_gerada=len(numeros))
            self.repository.registrar_audit_log(
                action="cadup_gerar_lista",
                entity="cadup_lotes",
                entity_id=str(lote_id),
                metadata_json=json.dumps(
                    {"quantidade_gerada": len(numeros), "saida": request.saida, "filtros": filtros},
                    ensure_ascii=False,
                    sort_keys=True,
                ),
            )
            return {
                "lote_id": lote_id,
                "status": "concluido",
                "quantidade_gerada": len(numeros),
                "saida": request.saida,
            }
        except Exception:
            self.repository.atualizar_lote(lote_id, status="erro", quantidade_gerada=len(numeros))
            self.repository.registrar_audit_log(
                action="cadup_gerar_lista_erro",
                entity="cadup_lotes",
                entity_id=str(lote_id),
                metadata_json=json.dumps({"quantidade_gerada": len(numeros)}, sort_keys=True),
            )
            raise

    def _validar_request_geracao(self, request: GeracaoCadupRequest) -> None:
        if request.quantidade <= 0:
            raise CadupGenerationError("Quantidade deve ser maior que zero.")
        if request.limite_por_faixa <= 0:
            raise CadupGenerationError("limite_por_faixa deve ser maior que zero.")
        if request.tipo and request.tipo not in {"F", "M", "A"}:
            raise CadupGenerationError("tipo deve ser F, M ou A.")
        if request.modo not in {"aleatorio", "sequencial"}:
            raise CadupGenerationError("modo deve ser aleatorio ou sequencial.")
        if not request.cabecalho.strip():
            raise CadupGenerationError("cabecalho nao pode ser vazio.")

    def _selecionar_numeros(
        self,
        ranges: list[CadupRange],
        request: GeracaoCadupRequest,
    ) -> list[dict[str, Any]]:
        rng = random.Random(request.seed)
        bloqueios_manuais = _parse_bloquear_prefixos(request.bloquear_prefixos)
        gerados: list[dict[str, Any]] = []
        vistos: set[str] = set()

        ordered_ranges = list(ranges)
        if request.modo == "aleatorio":
            rng.shuffle(ordered_ranges)

        for range_item in ordered_ranges:
            if _prefixo_bloqueado(range_item.cn, range_item.prefixo, bloqueios_manuais):
                continue

            mcdu_values = list(range(int(range_item.mcdu_ini), int(range_item.mcdu_fim) + 1))
            if request.modo == "aleatorio":
                rng.shuffle(mcdu_values)

            usados_na_faixa = 0
            for mcdu in mcdu_values:
                if usados_na_faixa >= request.limite_por_faixa:
                    break
                numero_item = self._montar_numero(range_item, mcdu, request.com_55)
                numero = numero_item["numero"]
                if numero in vistos:
                    continue
                if not request.sem_blacklist and numero_tem_padrao_spam(numero):
                    continue
                if not request.sem_blacklist and prefixo_artificial(range_item.prefixo, range_item.cn):
                    continue
                numero_nacional = numero_item["numero_nacional"]
                numero_com_55 = f"55{numero_nacional}"
                if self.repository.numero_ja_gerado(numero) or self.repository.numero_ja_gerado(numero_nacional) or self.repository.numero_ja_gerado(numero_com_55):
                    continue
                if self.repository.numero_em_blocklist(
                    numero,
                    numero_item["ddd"],
                    numero_item["prefixo"],
                    numero_item["mcdu"],
                ) or self.repository.numero_em_blocklist(
                    numero_nacional,
                    numero_item["ddd"],
                    numero_item["prefixo"],
                    numero_item["mcdu"],
                ) or self.repository.numero_em_blocklist(
                    numero_com_55,
                    numero_item["ddd"],
                    numero_item["prefixo"],
                    numero_item["mcdu"],
                ):
                    continue

                vistos.add(numero)
                gerados.append(numero_item)
                usados_na_faixa += 1
                if len(gerados) >= request.quantidade:
                    return gerados

        return gerados

    def _montar_numero(self, range_item: CadupRange, mcdu: int, com_55: bool) -> dict[str, Any]:
        mcdu_text = str(mcdu).zfill(4)
        numero_nacional = f"{range_item.cn}{range_item.prefixo}{mcdu_text}"
        numero = f"55{numero_nacional}" if com_55 else numero_nacional
        return {
            "numero": numero,
            "ddd": range_item.cn,
            "prefixo": range_item.prefixo,
            "mcdu": mcdu_text,
            "operadora": range_item.operadora,
            "tipo": range_item.tipo,
            "cidade": range_item.cidade,
            "uf": range_item.uf,
            "origem": "geracao_controlada",
            "numero_nacional": numero_nacional,
        }

    def _escrever_csv(self, saida: str, cabecalho: str, numeros: list[str]) -> None:
        path = Path(saida)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([cabecalho])
            for numero in numeros:
                writer.writerow([numero])


def _parse_bloquear_prefixos(raw: str | None) -> dict[str, tuple[str, ...]]:
    if not raw:
        return {}
    result: dict[str, tuple[str, ...]] = {}
    for group in raw.split(";"):
        if not group.strip() or "=" not in group:
            continue
        ddd, prefixes = group.split("=", 1)
        items = tuple(item.strip() for item in prefixes.split(",") if item.strip())
        if ddd.strip() and items:
            result[ddd.strip()] = items
    return result


def _prefixo_bloqueado(ddd: str, prefixo: str, bloqueios: dict[str, tuple[str, ...]]) -> bool:
    return any(str(prefixo).startswith(blocked) for blocked in bloqueios.get(str(ddd), ()))
