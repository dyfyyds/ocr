# ============================================================
#  字典项模型
# ============================================================
from datetime import datetime

from sqlalchemy import BigInteger, String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DictItem(Base):
    __tablename__ = "dict_item"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    type_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    item_label: Mapped[str] = mapped_column(String(100), nullable=False)
    item_value: Mapped[str] = mapped_column(String(100), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    status: Mapped[int] = mapped_column(default=1, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
