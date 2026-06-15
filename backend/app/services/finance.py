# ============================================================
#  财务服务层 — 开票/回款的前置校验与应收聚合
#  （采纳 OCR-IPMS 服务层模式；本系统为 async SQLAlchemy）
# ============================================================
from decimal import Decimal

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.enums import INVOICEABLE_STATUSES
from app.exceptions import NotFoundError, ValidationError


async def get_project_or_404(db: AsyncSession, project_id: int) -> Project:
    """取项目，不存在则 404。"""
    project = (await db.execute(
        select(Project).where(Project.id == project_id)
    )).scalar_one_or_none()
    if not project:
        raise NotFoundError("项目不存在")
    return project


async def ensure_invoiceable(db: AsyncSession, project_id: int) -> Project:
    """开票前置校验：项目存在且为「已立项」。"""
    project = await get_project_or_404(db, project_id)
    if project.status not in INVOICEABLE_STATUSES:
        raise ValidationError("只有已立项的项目可以开票")
    return project


async def ensure_payment_allowed(
    db: AsyncSession, project_id: int, amount: Decimal, invoice_id: int | None = None
) -> Project:
    """回款前置校验：金额 > 0、项目已立项、（可选）关联发票存在。"""
    if amount <= 0:
        raise ValidationError("回款金额必须大于 0")
    project = await get_project_or_404(db, project_id)
    if project.status not in INVOICEABLE_STATUSES:
        raise ValidationError("只有已立项的项目可以登记回款")
    if invoice_id:
        inv = (await db.execute(
            select(Invoice).where(Invoice.id == invoice_id)
        )).scalar_one_or_none()
        if not inv:
            raise NotFoundError("关联的发票不存在")
    return project


async def calc_receivable(db: AsyncSession, project_id: int | None = None) -> dict:
    """开票/回款/应收聚合。project_id 为 None 时按全局统计（供工作台）。"""
    inv_q = select(func.coalesce(func.sum(Invoice.amount), 0))
    pay_q = select(func.coalesce(func.sum(Payment.amount), 0))
    if project_id is not None:
        inv_q = inv_q.where(Invoice.project_id == project_id)
        pay_q = pay_q.where(Payment.project_id == project_id)
    invoiced = float((await db.execute(inv_q)).scalar() or 0)
    paid = float((await db.execute(pay_q)).scalar() or 0)
    return {"invoiced": invoiced, "paid": paid, "receivable": invoiced - paid}
