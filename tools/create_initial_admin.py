import getpass
import os
import sys
from pathlib import Path

from sqlalchemy import select


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.db.session import SessionLocal  # noqa: E402
from app.core.security import get_password_hash  # noqa: E402
from app.models.user import User  # noqa: E402


def main() -> None:
    print("Criando usuário admin inicial do Gerax Hub")

    name = os.getenv("GERAX_ADMIN_NAME") or input("Nome do admin: ").strip()
    email = os.getenv("GERAX_ADMIN_EMAIL") or input("E-mail do admin: ").strip().lower()
    password = os.getenv("GERAX_ADMIN_PASSWORD") or getpass.getpass("Senha do admin: ")

    if not name or not email or not password:
        raise SystemExit("Nome, e-mail e senha são obrigatórios.")

    db = SessionLocal()

    try:
        existing_user = db.execute(
            select(User).where(User.email == email)
        ).scalar_one_or_none()

        if existing_user:
            raise SystemExit(f"Já existe usuário com o e-mail {email}")

        user = User(
            name=name,
            email=email,
            hashed_password=get_password_hash(password),
            user_type="employee",
            role="admin",
            is_active=True,
            customer_id=None,
        )

        db.add(user)
        db.commit()

        print("Admin criado com sucesso.")
        print(f"E-mail: {email}")
        print("Perfil: employee/admin")

    finally:
        db.close()


if __name__ == "__main__":
    main()
