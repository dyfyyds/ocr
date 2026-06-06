# ============================================================
#  项目支出 Schema
# ============================================================
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class ExpenseCreate(BaseModel):
    description: str = Field(..., min_length=1, max_length=200)
    amount: Decimal = Field(..., gt=0)
    expense_date: date


class ExpenseOut(BaseModel):
    id: int
    project_id: int
    description: str
    amount: Decimal
    expense_date: date
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True
