# ============================================================
#  ORM 基类 - 公共 Mixin
# ============================================================
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.mysql import Base


class TimestampMixin:
    """公共时间字段 Mixin。"""
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now(), onupdate=func.now()
    )
