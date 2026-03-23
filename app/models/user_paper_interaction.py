from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class UserPaperInteraction(Base):
    __tablename__ = "user_paper_interactions"
    __table_args__ = (
        UniqueConstraint("user_id", "paper_id", name="uq_user_paper_interaction"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    paper_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
    )
    subscription_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("subscriptions.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="unread")
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    user: Mapped["User"] = relationship(back_populates="interactions")
    paper: Mapped["Paper"] = relationship(back_populates="interactions")
    subscription: Mapped["Subscription | None"] = relationship(
        back_populates="interactions",
    )
