# ============================================================
#  回款管理 Schema
# ============================================================
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class PaymentCreate(BaseModel):
    invoice_id: int | None = None
    amount: Decimal = Field(..., gt=0)
    payment_date: date
    payment_method: str | None = None
    remark: str | None = None


class PaymentOut(BaseModel):
    id: int
    project_id: int
    invoice_id: int | None
    amount: Decimal
    payment_date: date
    payment_method: str | None
    remark: str | None
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True
