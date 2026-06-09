# ============================================================
#  工作台 Schema
# ============================================================
from pydantic import BaseModel


class StatsOut(BaseModel):
    project_total: int = 0
    approved_total: int = 0
    closed_total: int = 0
    pending_audit: int = 0
    pending_close_audit: int = 0
    contract_total: float = 0
    invoice_total: float = 0
    payment_total: float = 0
    receivable: float = 0


class TrendItem(BaseModel):
    month: str
    invoice_amount: float = 0
    payment_amount: float = 0


class StatusDist(BaseModel):
    status: str
    count: int
