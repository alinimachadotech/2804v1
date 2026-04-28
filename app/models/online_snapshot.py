from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class OnlineRouterSnapshot(Base):
    __tablename__ = "online_router_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    sync_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("sync_runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    router_id: Mapped[int | None] = mapped_column(
        ForeignKey("routers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    router_name: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)

    total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ringing: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    talking: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
