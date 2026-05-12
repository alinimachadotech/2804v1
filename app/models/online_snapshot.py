from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class OnlineSnapshot(Base):
    """Snapshot agregado de chamadas online de todos os routers."""
    
    __tablename__ = "online_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ringing: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    talking: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    clients_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    routes_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    servers_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    routers_ok: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    routers_failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relacionamentos
    router_snapshots: Mapped[list["OnlineRouterSnapshot"]] = relationship(
        "OnlineRouterSnapshot",
        back_populates="snapshot",
        cascade="all, delete-orphan",
    )
    top_clients: Mapped[list["OnlineTopClientsSnapshot"]] = relationship(
        "OnlineTopClientsSnapshot",
        back_populates="snapshot",
        cascade="all, delete-orphan",
    )
    top_routes: Mapped[list["OnlineTopRoutesSnapshot"]] = relationship(
        "OnlineTopRoutesSnapshot",
        back_populates="snapshot",
        cascade="all, delete-orphan",
    )


class OnlineRouterSnapshot(Base):
    """Snapshot de um router específico em um momento determinado."""
    
    __tablename__ = "online_router_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    snapshot_id: Mapped[int] = mapped_column(
        ForeignKey("online_snapshots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    router_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ringing: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    talking: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    error_type: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relacionamento com snapshot pai
    snapshot: Mapped["OnlineSnapshot"] = relationship(
        "OnlineSnapshot",
        back_populates="router_snapshots",
    )


class OnlineTopClientsSnapshot(Base):
    """Top 20 clientes em um snapshot."""
    
    __tablename__ = "online_top_clients_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    snapshot_id: Mapped[int] = mapped_column(
        ForeignKey("online_snapshots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    client_name: Mapped[str] = mapped_column(String(255), nullable=False)
    total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ringing: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    talking: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    position: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relacionamento com snapshot pai
    snapshot: Mapped["OnlineSnapshot"] = relationship(
        "OnlineSnapshot",
        back_populates="top_clients",
    )


class OnlineTopRoutesSnapshot(Base):
    """Top 20 rotas em um snapshot."""
    
    __tablename__ = "online_top_routes_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    snapshot_id: Mapped[int] = mapped_column(
        ForeignKey("online_snapshots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    route_name: Mapped[str] = mapped_column(String(255), nullable=False)
    total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ringing: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    talking: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    position: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relacionamento com snapshot pai
    snapshot: Mapped["OnlineSnapshot"] = relationship(
        "OnlineSnapshot",
        back_populates="top_routes",
    )
