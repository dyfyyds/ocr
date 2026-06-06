# ============================================================
#  回款记录模型
# ============================================================
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, String, Date, Numeric, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    invoice_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    payment_method: Mapped[Optional[str]] = mapped_column(String(50))
    remark: Mapped[Optional[str]] = mapped_column(String(500))
    file_path: Mapped[Optional[str]] = mapped_column(String(500))
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
