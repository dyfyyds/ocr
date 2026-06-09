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
    payer_unit: str | None = None       # 汇款单位（图2）
    bank_serial_no: str | None = None   # 银行流水号（图2）
    remark: str | None = None


class PaymentOut(BaseModel):
    id: int
    project_id: int
    invoice_id: int | None
    amount: Decimal
    payment_date: date
    payment_method: str | None
    payer_unit: str | None = None
    bank_serial_no: str | None = None
    remark: str | None
    file_path: str | None = None
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True
