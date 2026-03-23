from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Paper(Base):
    __tablename__ = "papers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    external_id: Mapped[str | None] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    authors: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    abstract_original: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    pdf_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_parsed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    summary: Mapped["PaperSummary | None"] = relationship(
        back_populates="paper",
        uselist=False,
        passive_deletes=True,
    )
    interactions: Mapped[list["UserPaperInteraction"]] = relationship(
        back_populates="paper",
        passive_deletes=True,
    )
