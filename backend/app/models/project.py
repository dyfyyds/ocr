# ============================================================
#  项目模型
# ============================================================
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, String, Enum, Date, DateTime, Text, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_name: Mapped[str] = mapped_column(String(200), nullable=False)
    contract_no: Mapped[Optional[str]] = mapped_column(String(100))
    contract_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    customer_name: Mapped[Optional[str]] = mapped_column(String(200))
    project_type: Mapped[Optional[str]] = mapped_column(String(50))
    pm_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    sign_date: Mapped[Optional[date]] = mapped_column(Date)
    expected_start_date: Mapped[Optional[date]] = mapped_column(Date)
    expected_end_date: Mapped[Optional[date]] = mapped_column(Date)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        Enum("draft", "pending_audit", "approved", "rejected", "closed"),
        default="draft", server_default="draft"
    )
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    audit_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    audit_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    audit_reason: Mapped[Optional[str]] = mapped_column(Text)
