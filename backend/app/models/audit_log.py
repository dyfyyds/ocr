# ============================================================
#  审核记录模型
# ============================================================
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Enum, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    action: Mapped[str] = mapped_column(Enum("project_audit", "close_audit"), nullable=False)
    result: Mapped[str] = mapped_column(Enum("approved", "rejected"), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text)
    reviewer_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
