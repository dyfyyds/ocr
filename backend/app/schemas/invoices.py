# ============================================================
#  开票管理 Schema
# ============================================================
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class InvoiceCreate(BaseModel):
    amount: Decimal = Field(..., gt=0)
    invoice_unit: str | None = None
    invoice_date: date
    invoice_no: str | None = None
    invoice_code: str | None = None
    buyer_name: str | None = None
    seller_name: str | None = None


class InvoiceOut(BaseModel):
    id: int
    project_id: int
    invoice_no: str | None
    invoice_code: str | None
    amount: Decimal
    invoice_unit: str | None
    invoice_date: date
    buyer_name: str | None
    seller_name: str | None
    file_path: str | None
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True
