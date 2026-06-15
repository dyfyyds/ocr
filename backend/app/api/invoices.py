# ============================================================
#  开票管理接口 - 发票上传 + OCR 识别
# ============================================================
import asyncio
from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from decimal import Decimal
from datetime import date

from app.db.mysql import get_db
from app.models.project import Project
from app.models.invoice import Invoice
from app.schemas.invoices import InvoiceOut
from app.dependencies import get_current_user, require_role
from app.models.user import User
from app.utils.file_utils import validate_file_type, validate_file_size, generate_safe_filename, get_upload_path
from app.exceptions import NotFoundError, ValidationError
from app.core.contract_parser import parse_invoice_image
from app.services.finance import ensure_invoiceable

router = APIRouter()


@router.get("/{project_id}/invoices")
async def list_invoices(
    project_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取项目开票列表。"""
    result = await db.execute(
        select(Invoice).where(Invoice.project_id == project_id).order_by(Invoice.invoice_date.desc())
    )
    invoices = result.scalars().all()
    total = sum(float(inv.amount) for inv in invoices)
    return {"items": [InvoiceOut.model_validate(inv) for inv in invoices], "total": total}


@router.post("/{project_id}/invoices", response_model=InvoiceOut)
async def create_invoice(
    project_id: int,
    amount: Decimal = Form(...),
    tax_rate: Decimal = Form(None),
    tax_amount: Decimal = Form(None),
    invoice_date: date = Form(...),
    invoice_unit: str = Form(None),
    invoice_type: str | None = Form(None),    # 图1 发票类型
    invoice_no: str = Form(None),
    invoice_code: str = Form(None),
    buyer_name: str = Form(None),
    seller_name: str = Form(None),
    remark: str | None = Form(None),          # 图1 备注
    file: UploadFile = File(None),
    user: User = Depends(require_role("finance")),
    db: AsyncSession = Depends(get_db),
):
    """开票登记，上传发票图片自动 OCR 识别。"""
    # 开票前置校验（服务层）：项目存在且已立项
    await ensure_invoiceable(db, project_id)

    file_path = None
    ocr_result = None

    if file:
        validate_file_type(file.filename, "image")
        content = await file.read()
        validate_file_size(len(content))

        safe_name = generate_safe_filename(file.filename)
        file_path = get_upload_path("invoices", safe_name)
        with open(file_path, "wb") as f:
            f.write(content)

        # 优化：如果前端已通过 /ocr/recognize 预识别填充了关键字段，跳过重复 OCR
        user_filled = bool(invoice_no and invoice_code)
        if not user_filled:
            # OCR 自动填充（当用户未手动填写时）—— 放到线程池避免阻塞事件循环
            try:
                loop = asyncio.get_running_loop()
                ocr_result = await loop.run_in_executor(None, parse_invoice_image, file_path)
                extracted = ocr_result.get("extracted", {})

                if not invoice_no and extracted.get("invoice_no"):
                    invoice_no = extracted["invoice_no"]
                if not invoice_code and extracted.get("invoice_code"):
                    invoice_code = extracted["invoice_code"]
                if not tax_rate and extracted.get("tax_rate"):
                    try:
                        tax_rate = Decimal(extracted["tax_rate"])
                    except Exception:
                        pass
                if not tax_amount and extracted.get("tax_amount"):
                    try:
                        tax_amount = Decimal(extracted["tax_amount"])
                    except Exception:
                        pass
            except Exception as e:
                ocr_result = {"error": str(e)}

    invoice = Invoice(
        project_id=project_id,
        amount=amount,
        tax_rate=tax_rate,
        tax_amount=tax_amount,
        invoice_date=invoice_date,
        invoice_unit=invoice_unit,
        invoice_type=invoice_type,
        invoice_no=invoice_no,
        invoice_code=invoice_code,
        buyer_name=buyer_name,
        seller_name=seller_name,
        remark=remark,
        file_path=file_path,
        ocr_result=ocr_result,
        created_by=user.id,
    )
    db.add(invoice)
    await db.flush()
    await db.refresh(invoice)
    return InvoiceOut.model_validate(invoice)


@router.delete("/{project_id}/invoices/{invoice_id}")
async def delete_invoice(
    project_id: int,
    invoice_id: int,
    user: User = Depends(require_role("finance")),
    db: AsyncSession = Depends(get_db),
):
    """删除开票记录。"""
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id, Invoice.project_id == project_id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise NotFoundError("发票不存在")
    
    await db.delete(invoice)
    await db.commit()
    return {"message": "发票已成功删除"}

