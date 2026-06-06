# ============================================================
#  用户模型
# ============================================================
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, String, Enum, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    real_name: Mapped[Optional[str]] = mapped_column(String(50))
    email: Mapped[Optional[str]] = mapped_column(String(100))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    role: Mapped[str] = mapped_column(Enum("admin", "business", "finance", "pm"), nullable=False)
    avatar: Mapped[Optional[str]] = mapped_column(String(255))
    status: Mapped[int] = mapped_column(default=1, server_default="1")
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime)
