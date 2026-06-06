# ============================================================
#  合同文件模型
# ============================================================
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, String, Enum, Integer, JSON, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    file_type: Mapped[str] = mapped_column(Enum("word", "pdf"), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, default=0, server_default="0")
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    ocr_result: Mapped[Optional[dict]] = mapped_column(JSON)
    uploaded_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
