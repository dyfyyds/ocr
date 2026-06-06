# ============================================================
#  项目支出模型
# ============================================================
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, String, Date, Numeric, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ProjectExpense(Base):
    __tablename__ = "project_expenses"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
