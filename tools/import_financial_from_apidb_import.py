from __future__ import annotations

import argparse
from urllib.parse import parse_qsl, quote_plus, urlencode, urlparse, urlunparse

from sqlalchemy import create_engine, text

from app.core.settings import settings


ALLOWED_TABLES = (
    "todos_assinantes",
    "todos_assinantes_hist",
    "relatorio_assinantes_diario",
    "relatorio_assinantes_semanal",
    "relatorio_assinantes_quinzenal",
    "relatorio_assinantes_mensal",
    "relatorio_assinantes_por_periodo",
    "relatorio_rotas_diario",
    "historico_saldos_diario",
    "margem_lucro_operacional",
    "sipcodes_agregado",
    "variacoes_assinantes",
    "vw_priorize_hist",
)
SOURCE_DATABASE_NAME = "apidb_import"


def build_source_database_url(target_url: str, source_database: str) -> str:
    parsed = urlparse(target_url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    path = f"/{source_database}"
    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            path,
            parsed.params,
            urlencode(query, doseq=True),
            parsed.fragment,
        )
    )


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Importar dados financeiros de apidb_import para gerax_manager de forma segura."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Exibir contagens e operações sem alterar o banco de destino.",
    )
    parser.add_argument(
        "--truncate-target",
        action="store_true",
        help="Limpar tabelas de destino antes de importar (requer confirmacao explicita).",
    )
    parser.add_argument(
        "--confirm-truncate",
        action="store_true",
        help="Confirmar explicitamente o truncamento das tabelas de destino.",
    )
    return parser.parse_args(argv)


def get_engine(database_url: str):
    return create_engine(database_url, pool_pre_ping=True, future=True)


def get_table_count(connection, qualified_table: str) -> int:
    result = connection.execute(text(f"SELECT COUNT(*) AS count FROM {qualified_table}"))
    return int(result.scalar_one())


def truncate_table(connection, qualified_table: str) -> None:
    connection.execute(text(f"TRUNCATE TABLE {qualified_table}"))


def copy_table_data(source_connection, target_connection, source_db: str, table: str) -> int:
    qualified_source = f"`{source_db}`.`{table}`"
    select_statement = text(f"SELECT * FROM {qualified_source}")
    result = source_connection.execute(select_statement)
    rows = [dict(row._mapping) for row in result]

    if not rows:
        return 0

    columns = rows[0].keys()
    column_list = ", ".join(f"`{column}`" for column in columns)
    param_list = ", ".join(f":{column}" for column in columns)
    insert_statement = text(
        f"INSERT INTO `{table}` ({column_list}) VALUES ({param_list})"
    )
    target_connection.execute(insert_statement, rows)
    return len(rows)


def confirm_truncate(required: bool) -> bool:
    if not required:
        return True
    answer = input(
        "O parametro --truncate-target foi usado. Confirmar truncamento das tabelas de destino? [s/N]: "
    ).strip().lower()
    return answer in ("s", "sim")


def main(argv=None) -> int:
    options = parse_args(argv)
    source_url = build_source_database_url(settings.database_url, SOURCE_DATABASE_NAME)
    target_url = settings.database_url

    if options.truncate_target and not options.confirm_truncate:
        print(
            "Para truncar as tabelas de destino, execute com --truncate-target e --confirm-truncate."
        )
        return 1

    source_engine = get_engine(source_url)
    target_engine = get_engine(target_url)

    with source_engine.connect() as source_connection, target_engine.connect() as target_connection:
        if options.dry_run:
            print("Modo dry-run ativado. Nenhuma alteracao sera aplicada no banco de destino.")

        for table in ALLOWED_TABLES:
            source_qualified = f"`{SOURCE_DATABASE_NAME}`.`{table}`"
            target_qualified = f"`{table}`"

            source_count = get_table_count(source_connection, source_qualified)
            target_count = get_table_count(target_connection, target_qualified)
            print(
                f"Tabela {table}: origem={source_count} destino={target_count}"
            )

            if source_count == 0:
                print(f"Nenhum registro para copiar em {table}. Pulando.")
                continue

            if options.truncate_target:
                if options.dry_run:
                    print(f"[dry-run] Truncaria {table} no destino.")
                else:
                    truncate_table(target_connection, target_qualified)
                    print(f"Truncado {table} no destino.")

            if options.dry_run:
                print(f"[dry-run] Copiaria {source_count} registros para {table}.")
                continue

            inserted = copy_table_data(source_connection, target_connection, SOURCE_DATABASE_NAME, table)
            target_connection.commit()
            print(f"Importados {inserted} registros para {table}.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
