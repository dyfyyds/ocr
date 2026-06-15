# ============================================================
#  开票记录模型
# ============================================================
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, String, Date, Numeric, JSON, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    invoice_no: Mapped[Optional[str]] = mapped_column(String(50))
    invoice_code: Mapped[Optional[str]] = mapped_column(String(50))
    # 发票类型（图1 表单）：special=增值税专用发票 / normal=普通发票
    invoice_type: Mapped[Optional[str]] = mapped_column(String(20))
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    tax_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    invoice_unit: Mapped[Optional[str]] = mapped_column(String(200))
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    buyer_name: Mapped[Optional[str]] = mapped_column(String(200))
    seller_name: Mapped[Optional[str]] = mapped_column(String(200))
    file_path: Mapped[Optional[str]] = mapped_column(String(500))
    delivery_voucher: Mapped[Optional[str]] = mapped_column(String(500))
    remark: Mapped[Optional[str]] = mapped_column(String(500))   # 图1 备注
    ocr_result: Mapped[Optional[dict]] = mapped_column(JSON)
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
