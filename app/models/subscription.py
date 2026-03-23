from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_platform: Mapped[str | None] = mapped_column(String(50), nullable=True)
    search_query: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cron_schedule: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    user: Mapped["User"] = relationship(back_populates="subscriptions")
    interactions: Mapped[list["UserPaperInteraction"]] = relationship(
        back_populates="subscription",
        passive_deletes=True,
    )
