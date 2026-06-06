# ============================================================
#  结项记录模型
# ============================================================
from datetime import date, datetime
from typing import Optional

from sqlalchemy import BigInteger, String, Enum, Date, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ProjectClose(Base):
    __tablename__ = "project_close"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    close_date: Mapped[date] = mapped_column(Date, nullable=False)
    close_reason: Mapped[Optional[str]] = mapped_column(Text)
    acceptance_report_path: Mapped[Optional[str]] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(
        Enum("pending", "approved", "rejected"),
        default="pending", server_default="pending"
    )
    reviewer_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    review_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    review_reason: Mapped[Optional[str]] = mapped_column(Text)
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
