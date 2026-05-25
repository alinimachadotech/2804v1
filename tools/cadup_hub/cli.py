"""Command line interface for CADUP Hub v2."""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from typing import Any

from tools.cadup_hub.service import CadupGenerationError, CadupService, GeracaoCadupRequest


def _json_default(value: Any):
    if dataclasses.is_dataclass(value):
        return dataclasses.asdict(value)
    return str(value)


def _print_json(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cadup-hub", description="CADUP Hub v2 internal CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    consultar = subparsers.add_parser("consultar-numero", help="Consulta um numero na base CADUP")
    consultar.add_argument("numero")

    capacidade = subparsers.add_parser("capacidade", help="Consulta capacidade por empresa")
    capacidade.add_argument("--empresa", required=True)
    capacidade.add_argument("--tipo")

    ranking = subparsers.add_parser("ranking", help="Lista ranking de empresas por capacidade")
    ranking.add_argument("--tipo")
    ranking.add_argument("--ddd")

    gerar = subparsers.add_parser("gerar", help="Gera lista CADUP controlada e auditavel")
    gerar.add_argument("--nome-lote", required=True)
    gerar.add_argument("--empresa")
    gerar.add_argument("--ddd")
    gerar.add_argument("--tipo", choices=["F", "M", "A"])
    gerar.add_argument("--uf")
    gerar.add_argument("--cidade")
    gerar.add_argument("--quantidade", required=True, type=int)
    gerar.add_argument("--limite-por-faixa", type=int, default=10)
    gerar.add_argument("--saida", required=True)
    gerar.add_argument("--com-55", action="store_true")
    gerar.add_argument("--cabecalho", default="destino")
    gerar.add_argument("--sem-blacklist", action="store_true")
    gerar.add_argument("--modo", choices=["aleatorio", "sequencial"], default="aleatorio")
    gerar.add_argument("--bloquear-prefixos")
    gerar.add_argument("--seed", type=int)

    lote = subparsers.add_parser("consultar-lote", help="Consulta metadados de um lote CADUP")
    lote.add_argument("lote_id", type=int)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    service = CadupService()

    try:
        if args.command == "consultar-numero":
            _print_json(service.consultar_numero(args.numero))
        elif args.command == "capacidade":
            _print_json(service.capacidade_por_empresa(args.empresa, tipo=args.tipo))
        elif args.command == "ranking":
            _print_json(service.ranking_empresas(tipo=args.tipo, ddd=args.ddd))
        elif args.command == "gerar":
            _print_json(
                service.gerar_lista(
                    GeracaoCadupRequest(
                        nome_lote=args.nome_lote,
                        empresa=args.empresa,
                        ddd=args.ddd,
                        tipo=args.tipo,
                        uf=args.uf,
                        cidade=args.cidade,
                        quantidade=args.quantidade,
                        limite_por_faixa=args.limite_por_faixa,
                        saida=args.saida,
                        com_55=args.com_55,
                        cabecalho=args.cabecalho,
                        sem_blacklist=args.sem_blacklist,
                        modo=args.modo,
                        bloquear_prefixos=args.bloquear_prefixos,
                        seed=args.seed,
                    )
                )
            )
        elif args.command == "consultar-lote":
            result = service.consultar_lote(args.lote_id)
            if result is None:
                print("Lote nao encontrado.", file=sys.stderr)
                return 1
            _print_json(result)
        return 0
    except CadupGenerationError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except Exception:
        print(
            "Nao foi possivel consultar o banco CADUP. "
            "Verifique DB_HOST, DB_PORT, DB_USER, DB_PASSWORD e DB_NAME.",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
