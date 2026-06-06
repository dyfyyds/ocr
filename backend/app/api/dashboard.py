# ============================================================
#  工作台接口
# ============================================================
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.mysql import get_db
from app.models.project import Project
from app.models.project_close import ProjectClose
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.activity_log import ActivityLog
from app.schemas.dashboard import StatsOut, StatusDist
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/stats", response_model=StatsOut)
async def get_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """工作台概览统计。"""
    project_total = (await db.execute(select(func.count(Project.id)))).scalar() or 0
    approved_total = (await db.execute(
        select(func.count(Project.id)).where(Project.status == "approved")
    )).scalar() or 0
    closed_total = (await db.execute(
        select(func.count(Project.id)).where(Project.status == "closed")
    )).scalar() or 0
    pending_audit = (await db.execute(
        select(func.count(Project.id)).where(Project.status == "pending_audit")
    )).scalar() or 0

    # 待结项审核数
    from sqlalchemy import and_
    pending_close_audit = (await db.execute(
        select(func.count(ProjectClose.id)).where(ProjectClose.status == "pending")
    )).scalar() or 0

    invoice_total = (await db.execute(select(func.sum(Invoice.amount)))).scalar() or 0
    payment_total = (await db.execute(select(func.sum(Payment.amount)))).scalar() or 0

    return StatsOut(
        project_total=project_total,
        approved_total=approved_total,
        closed_total=closed_total,
        pending_audit=pending_audit,
        pending_close_audit=pending_close_audit,
        invoice_total=float(invoice_total),
        payment_total=float(payment_total),
        receivable=float(invoice_total) - float(payment_total),
    )


@router.get("/trend")
async def get_trend(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """近 6 个月开票/回款趋势。"""
    from datetime import datetime, timedelta

    now = datetime.now()
    items = []
    for i in range(5, -1, -1):
        # 计算月份
        month_date = now - timedelta(days=30 * i)
        year = month_date.year
        month = month_date.month
        month_str = f"{year}-{month:02d}"

        # 开票金额
        inv_sum = (await db.execute(
            select(func.sum(Invoice.amount)).where(
                func.year(Invoice.invoice_date) == year,
                func.month(Invoice.invoice_date) == month,
            )
        )).scalar() or 0

        # 回款金额
        pay_sum = (await db.execute(
            select(func.sum(Payment.amount)).where(
                func.year(Payment.payment_date) == year,
                func.month(Payment.payment_date) == month,
            )
        )).scalar() or 0

        items.append({
            "month": month_str,
            "invoice_amount": float(inv_sum),
            "payment_amount": float(pay_sum),
        })

    return {"items": items}


@router.get("/status-distribution")
async def get_status_distribution(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """项目状态分布。"""
    result = await db.execute(
        select(Project.status, func.count(Project.id)).group_by(Project.status)
    )
    rows = result.all()
    return {"items": [StatusDist(status=r[0], count=r[1]) for r in rows]}


@router.get("/recent-logs")
async def get_recent_logs(
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """最近活动日志。"""
    result = await db.execute(
        select(ActivityLog).order_by(ActivityLog.created_at.desc()).limit(limit)
    )
    logs = result.scalars().all()
    return {"items": [
        {
            "id": log.id,
            "action": log.action,
            "detail": log.detail,
            "user_id": log.user_id,
            "project_id": log.project_id,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]}
