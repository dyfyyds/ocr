# ============================================================
#  回款管理接口
# ============================================================
from decimal import Decimal
from datetime import date

from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.mysql import get_db
from app.models.project import Project
from app.models.payment import Payment
from app.models.invoice import Invoice
from app.schemas.payments import PaymentOut
from app.dependencies import get_current_user, require_role
from app.models.user import User
from app.utils.file_utils import (
    validate_file_type, validate_file_size, generate_safe_filename, get_upload_path,
)
from app.exceptions import NotFoundError, ValidationError
from app.services.finance import ensure_payment_allowed

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
    amount: Decimal = Form(...),
    payment_date: date = Form(...),
    payment_method: str | None = Form(None),
    invoice_id: int | None = Form(None),
    remark: str | None = Form(None),
    file: UploadFile = File(None),
    user: User = Depends(require_role("finance", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """回款登记，可选上传回款凭证（图片/PDF）。

    改为 multipart/form-data 以支持 PPT 要求的「回款上传凭证」，
    凭证落地后写入 payments.file_path（该列模型已存在）。
    """
    # 回款前置校验（服务层）：金额>0、项目已立项、（可选）关联发票存在
    await ensure_payment_allowed(db, project_id, amount, invoice_id)

    # 可选回款凭证落地
    file_path = None
    if file:
        validate_file_type(file.filename, "all")
        content = await file.read()
        validate_file_size(len(content))
        safe_name = generate_safe_filename(file.filename)
        file_path = get_upload_path("payments", safe_name)
        with open(file_path, "wb") as f:
            f.write(content)

    payment = Payment(
        project_id=project_id,
        invoice_id=invoice_id,
        amount=amount,
        payment_date=payment_date,
        payment_method=payment_method,
        remark=remark,
        file_path=file_path,
        created_by=user.id,
    )
    db.add(payment)
    await db.flush()
    await db.refresh(payment)
    return PaymentOut.model_validate(payment)
