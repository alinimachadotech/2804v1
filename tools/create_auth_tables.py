import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.db.base import Base  # noqa: E402
from app.db.session import engine  # noqa: E402
from app.models.user import User  # noqa: F401, E402


def main() -> None:
    print("Criando tabelas de autenticação, se ainda não existirem...")
    Base.metadata.create_all(bind=engine)
    print("Tabelas de autenticação verificadas/criadas com sucesso.")


if __name__ == "__main__":
    main()
