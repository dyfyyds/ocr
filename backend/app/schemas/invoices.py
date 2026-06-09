# ============================================================
#  开票管理 Schema
# ============================================================
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class InvoiceCreate(BaseModel):
    amount: Decimal = Field(..., gt=0)
    tax_rate: Decimal | None = None
    tax_amount: Decimal | None = None
    invoice_unit: str | None = None
    invoice_type: str | None = None   # special / normal（图1）
    invoice_date: date
    invoice_no: str | None = None
    invoice_code: str | None = None
    buyer_name: str | None = None
    seller_name: str | None = None
    remark: str | None = None          # 图1


class InvoiceOut(BaseModel):
    id: int
    project_id: int
    invoice_no: str | None
    invoice_code: str | None
    invoice_type: str | None = None
    amount: Decimal
    tax_rate: Decimal | None
    tax_amount: Decimal | None
    invoice_unit: str | None
    invoice_date: date
    buyer_name: str | None
    seller_name: str | None
    remark: str | None = None
    file_path: str | None
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True
