# ============================================================
#  合同校验差异模型
# ============================================================
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, String, Enum, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ContractDiff(Base):
    __tablename__ = "contract_diff"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    field_name: Mapped[str] = mapped_column(String(50), nullable=False)
    ocr_value: Mapped[Optional[str]] = mapped_column(String(500))
    input_value: Mapped[Optional[str]] = mapped_column(String(500))
    diff_type: Mapped[Optional[str]] = mapped_column(Enum("mismatch", "format", "missing"))
    confirmed: Mapped[int] = mapped_column(default=0, server_default="0")
    confirm_reason: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
