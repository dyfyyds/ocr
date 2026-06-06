# ============================================================
#  回款管理接口
# ============================================================
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.mysql import get_db
from app.models.project import Project
from app.models.payment import Payment
from app.models.invoice import Invoice
from app.schemas.payments import PaymentCreate, PaymentOut
from app.dependencies import get_current_user, require_role
from app.models.user import User
from app.exceptions import NotFoundError, ValidationError

router = APIRouter()


@router.get("/{project_id}/payments")
async def list_payments(
    project_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取项目回款列表。"""
    result = await db.execute(
        select(Payment).where(Payment.project_id == project_id).order_by(Payment.payment_date.desc())
    )
    payments = result.scalars().all()
    total = sum(float(p.amount) for p in payments)
    return {"items": [PaymentOut.model_validate(p) for p in payments], "total": total}


@router.post("/{project_id}/payments", response_model=PaymentOut)
async def create_payment(
    project_id: int,
    body: PaymentCreate,
    user: User = Depends(require_role("finance", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """回款登记。"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise NotFoundError("项目不存在")
    if project.status != "approved":
        raise ValidationError("只有已立项的项目可以登记回款")

    # 验证发票存在
    if body.invoice_id:
        inv = (await db.execute(select(Invoice).where(Invoice.id == body.invoice_id))).scalar_one_or_none()
        if not inv:
            raise NotFoundError("关联的发票不存在")

    payment = Payment(
        project_id=project_id,
        invoice_id=body.invoice_id,
        amount=body.amount,
        payment_date=body.payment_date,
        payment_method=body.payment_method,
        remark=body.remark,
        created_by=user.id,
    )
    db.add(payment)
    await db.flush()
    await db.refresh(payment)
    return PaymentOut.model_validate(payment)
