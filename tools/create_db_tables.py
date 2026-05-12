from sqlalchemy import inspect

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db.base import Base
from app.db.session import engine

# Importar os models registra as tabelas no metadata do SQLAlchemy.
import app.models  # noqa: F401


def main() -> None:
    print("[GERAX] Criando tabelas do banco, se ainda nÃ£o existirem...")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    tables = inspector.get_table_names()

    print("[GERAX] Tabelas encontradas:")
    for table_name in tables:
        print(f" - {table_name}")

    if not tables:
        raise SystemExit("[GERAX] Nenhuma tabela encontrada apÃ³s create_all.")


if __name__ == "__main__":
    main()

