# ============================================================
#  字典类型模型
# ============================================================
from typing import Optional

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class DictType(Base, TimestampMixin):
    __tablename__ = "dict_type"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    type_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    type_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[int] = mapped_column(default=1, server_default="1")
    remark: Mapped[Optional[str]] = mapped_column(String(500))
