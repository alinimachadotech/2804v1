from sqlalchemy import Boolean, Column, DateTime, Integer, String, func
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)

    hashed_password = Column(String(255), nullable=False)

    # employee ou client
    user_type = Column(String(30), nullable=False, index=True)

    # admin, noc, financeiro, suporte, client_admin, client_viewer
    role = Column(String(50), nullable=False, index=True)

    is_active = Column(Boolean, nullable=False, default=True)

    # Somente para usuÃ¡rio do tipo client.
    # Para funcionÃ¡rio, fica NULL.
    customer_id = Column(Integer, nullable=True, index=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
