"""Repository functions for CADUP MariaDB tables."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tools.cadup_hub.db import get_connection
from tools.cadup_hub.models import CadupRange
from tools.cadup_hub.normalizacao import extrair_ddd_prefixo_mcdu


class CadupRepository:
    def __init__(self, connection_factory: Callable[[], Any] = get_connection):
        self.connection_factory = connection_factory

    def _fetch_all(self, sql: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        connection = self.connection_factory()
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
                return list(cursor.fetchall())
        finally:
            connection.close()

    def buscar_ranges(
        self,
        empresa: str | None = None,
        ddd: str | int | None = None,
        tipo: str | None = None,
        uf: str | None = None,
        cidade: str | None = None,
    ) -> list[CadupRange]:
        filters = []
        params: dict[str, Any] = {}

        if empresa:
            filters.append("operadora = %(empresa)s")
            params["empresa"] = empresa
        if ddd:
            filters.append("cn = %(ddd)s")
            params["ddd"] = str(ddd)
        if tipo:
            filters.append("tipo = %(tipo)s")
            params["tipo"] = tipo
        if uf:
            filters.append("uf = %(uf)s")
            params["uf"] = uf
        if cidade:
            filters.append("cidade = %(cidade)s")
            params["cidade"] = cidade

        filters.append("ativo = 1")
        where = f"WHERE {' AND '.join(filters)}" if filters else ""
        rows = self._fetch_all(
            f"""
            SELECT operadora, cnpj, cn, prefixo, mcdu_ini, mcdu_fim, cidade, uf, tipo, rn1
            FROM cadup_v3
            {where}
            ORDER BY operadora, cn, prefixo, mcdu_ini
            """,
            params,
        )
        return [CadupRange.from_row(row) for row in rows]

    def consultar_numero(self, numero: str | int) -> CadupRange | None:
        partes = extrair_ddd_prefixo_mcdu(numero)
        if partes is None:
            return None

        rows = self._fetch_all(
            """
            SELECT operadora, cnpj, cn, prefixo, mcdu_ini, mcdu_fim, cidade, uf, tipo, rn1
            FROM cadup_v3
            WHERE cn = %(ddd)s
              AND prefixo = %(prefixo)s
              AND %(mcdu)s BETWEEN mcdu_ini AND mcdu_fim
            ORDER BY mcdu_ini
            LIMIT 1
            """,
            {
                "ddd": partes["ddd"],
                "prefixo": partes["prefixo"],
                "mcdu": int(partes["mcdu"]),
            },
        )
        if not rows:
            return None
        return CadupRange.from_row(rows[0])

    def ranking_empresas(
        self,
        tipo: str | None = None,
        ddd: str | int | None = None,
    ) -> list[dict[str, Any]]:
        filters = []
        params: dict[str, Any] = {}
        if tipo:
            filters.append("tipo = %(tipo)s")
            params["tipo"] = tipo
        if ddd:
            filters.append("cn = %(ddd)s")
            params["ddd"] = str(ddd)

        where = f"WHERE {' AND '.join(filters)}" if filters else ""
        return self._fetch_all(
            f"""
            SELECT
                operadora,
                COUNT(*) AS ranges,
                SUM(GREATEST(0, mcdu_fim - mcdu_ini + 1)) AS capacidade
            FROM cadup_v3
            {where}
            GROUP BY operadora
            ORDER BY capacidade DESC, operadora ASC
            """,
            params,
        )

    def capacidade_por_empresa(
        self,
        empresa: str,
        tipo: str | None = None,
    ) -> dict[str, Any]:
        filters = ["operadora = %(empresa)s"]
        params: dict[str, Any] = {"empresa": empresa}
        if tipo:
            filters.append("tipo = %(tipo)s")
            params["tipo"] = tipo

        rows = self._fetch_all(
            f"""
            SELECT
                operadora,
                COUNT(*) AS ranges,
                SUM(GREATEST(0, mcdu_fim - mcdu_ini + 1)) AS capacidade
            FROM cadup_v3
            WHERE {' AND '.join(filters)}
            GROUP BY operadora
            """,
            params,
        )
        return rows[0] if rows else {"operadora": empresa, "ranges": 0, "capacidade": 0}

    def criar_lote(
        self,
        *,
        nome: str,
        filtros: dict[str, Any],
        quantidade_solicitada: int,
        created_by: str | None = None,
    ) -> int:
        connection = self.connection_factory()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO cadup_lotes (
                        nome, empresa, tipo, ddd, quantidade_solicitada,
                        quantidade_gerada, status, filtros_json, created_by
                    )
                    VALUES (
                        %(nome)s, %(empresa)s, %(tipo)s, %(ddd)s, %(quantidade_solicitada)s,
                        0, 'em_processamento', %(filtros_json)s, %(created_by)s
                    )
                    """,
                    {
                        "nome": nome,
                        "empresa": filtros.get("empresa"),
                        "tipo": filtros.get("tipo"),
                        "ddd": filtros.get("ddd"),
                        "quantidade_solicitada": quantidade_solicitada,
                        "filtros_json": filtros.get("filtros_json", "{}"),
                        "created_by": created_by,
                    },
                )
                lote_id = int(cursor.lastrowid)
            connection.commit()
            return lote_id
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def atualizar_lote(self, lote_id: int, *, status: str, quantidade_gerada: int) -> None:
        connection = self.connection_factory()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE cadup_lotes
                    SET status = %(status)s,
                        quantidade_gerada = %(quantidade_gerada)s,
                        finished_at = CASE
                            WHEN %(status)s IN ('concluido', 'erro') THEN CURRENT_TIMESTAMP
                            ELSE finished_at
                        END
                    WHERE id = %(lote_id)s
                    """,
                    {
                        "lote_id": lote_id,
                        "status": status,
                        "quantidade_gerada": quantidade_gerada,
                    },
                )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def numero_ja_gerado(self, numero: str) -> bool:
        rows = self._fetch_all(
            "SELECT id FROM cadup_numeros_gerados WHERE numero = %(numero)s LIMIT 1",
            {"numero": numero},
        )
        return bool(rows)

    def numero_em_blocklist(self, numero: str, ddd: str, prefixo: str, mcdu: str) -> bool:
        rows = self._fetch_all(
            """
            SELECT id
            FROM cadup_blocklist
            WHERE active = 1
              AND (
                    numero = %(numero)s
                    OR (ddd = %(ddd)s AND prefixo = %(prefixo)s AND (mcdu IS NULL OR mcdu = %(mcdu)s))
                    OR (ddd = %(ddd)s AND prefixo IS NULL AND mcdu = %(mcdu)s)
                  )
            LIMIT 1
            """,
            {"numero": numero, "ddd": ddd, "prefixo": prefixo, "mcdu": mcdu},
        )
        return bool(rows)

    def salvar_numeros_gerados(self, lote_id: int, numeros: list[dict[str, Any]]) -> None:
        if not numeros:
            return

        connection = self.connection_factory()
        try:
            with connection.cursor() as cursor:
                for item in numeros:
                    cursor.execute(
                        """
                        INSERT INTO cadup_numeros_gerados (
                            lote_id, numero, ddd, prefixo, mcdu, operadora,
                            tipo, cidade, uf, origem
                        )
                        VALUES (
                            %(lote_id)s, %(numero)s, %(ddd)s, %(prefixo)s, %(mcdu)s,
                            %(operadora)s, %(tipo)s, %(cidade)s, %(uf)s, %(origem)s
                        )
                        """,
                        {
                            "lote_id": lote_id,
                            "numero": item["numero"],
                            "ddd": item["ddd"],
                            "prefixo": item["prefixo"],
                            "mcdu": item["mcdu"],
                            "operadora": item.get("operadora"),
                            "tipo": item.get("tipo"),
                            "cidade": item.get("cidade"),
                            "uf": item.get("uf"),
                            "origem": item.get("origem", "geracao_controlada"),
                        },
                    )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def registrar_audit_log(
        self,
        *,
        action: str,
        entity: str,
        entity_id: str | None = None,
        metadata_json: str | None = None,
        actor: str | None = None,
    ) -> None:
        connection = self.connection_factory()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO cadup_audit_log (action, entity, entity_id, actor, metadata_json)
                    VALUES (%(action)s, %(entity)s, %(entity_id)s, %(actor)s, %(metadata_json)s)
                    """,
                    {
                        "action": action,
                        "entity": entity,
                        "entity_id": entity_id,
                        "actor": actor,
                        "metadata_json": metadata_json,
                    },
                )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def consultar_lote(self, lote_id: int) -> dict[str, Any] | None:
        rows = self._fetch_all(
            """
            SELECT id, nome, empresa, tipo, ddd, quantidade_solicitada,
                   quantidade_gerada, status, filtros_json, created_by,
                   created_at, finished_at
            FROM cadup_lotes
            WHERE id = %(lote_id)s
            LIMIT 1
            """,
            {"lote_id": lote_id},
        )
        return rows[0] if rows else None


_default_repository = CadupRepository()


def buscar_ranges(*args, **kwargs):
    return _default_repository.buscar_ranges(*args, **kwargs)


def consultar_numero(*args, **kwargs):
    return _default_repository.consultar_numero(*args, **kwargs)


def ranking_empresas(*args, **kwargs):
    return _default_repository.ranking_empresas(*args, **kwargs)


def capacidade_por_empresa(*args, **kwargs):
    return _default_repository.capacidade_por_empresa(*args, **kwargs)


def consultar_lote(*args, **kwargs):
    return _default_repository.consultar_lote(*args, **kwargs)
