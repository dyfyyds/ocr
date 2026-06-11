# ============================================================
#  独立 OCR 识别接口 - 不绑定项目，正则 + LLM 综合提取
# ============================================================
import logging
import tempfile
import os

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user
from app.models.user import User
from app.db.mysql import get_db
from app.utils.file_utils import validate_file_type, validate_file_size
from app.core.contract_parser import (
    parse_word_contract_with_llm, parse_pdf_contract_with_llm,
    _merge_extracted, _try_llm_extract, CONTRACT_FIELDS,
    INVOICE_FIELDS, PAYMENT_FIELDS,
    _extract_invoice_fields, _extract_payment_fields,
)
from app.core.ocr_engine import ocr_from_image_bytes
from app.core.nlp_extractor import extractor
from app.exceptions import ValidationError

logger = logging.getLogger(__name__)

router = APIRouter()

# 图片类型集合
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}


@router.post("/recognize")
async def recognize_file(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    独立 OCR 识别：上传文件（Word/PDF/图片），正则 + LLM 综合提取。
    不写入数据库，不绑定项目。受 llm_enabled 开关控制。
    """
    ext = validate_file_type(file.filename, "all")
    content = await file.read()
    validate_file_size(len(content))

    try:
        # 1) 按文件类型取全文（不再按类型分叉提取逻辑：合同/发票/汇款统一三路提取）
        ocr_items = []
        if ext == ".docx":
            from app.core.contract_parser import _extract_text_from_docx
            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            try:
                full_text = _extract_text_from_docx(tmp_path)
            finally:
                os.unlink(tmp_path)
            source = "python-docx"
        elif ext == ".pdf":
            from app.core.ocr_engine import ocr_from_pdf_bytes
            ocr_items = ocr_from_pdf_bytes(content)
            full_text = "\n".join([item["text"] for item in ocr_items])
            source = "paddleocr"
        elif ext in IMAGE_EXTENSIONS:
            ocr_items = ocr_from_image_bytes(content)
            full_text = "\n".join([item["text"] for item in ocr_items])
            source = "paddleocr"
        else:
            raise ValidationError(f"不支持的文件类型: {ext}")

        # 2) 三路规则提取：合同 + 发票 + 汇款（无论 PDF/图片/Word 都跑全套）
        contract_extracted = extractor.extract(full_text)
        invoice_extracted = _extract_invoice_fields(full_text)
        payment_extracted = _extract_payment_fields(full_text)

        # 3) LLM 提取（受 llm_enabled 开关控制；面向合同字段）
        llm_result = await _try_llm_extract(full_text, db)

        # 合并：合同 + 发票字段一并纳入 extracted；汇款字段单独返回供汇款表单使用
        merged_regex = {**payment_extracted, **invoice_extracted, **contract_extracted}
        merge_fields = tuple(dict.fromkeys(CONTRACT_FIELDS + INVOICE_FIELDS))
        merged, source_map = _merge_extracted(merged_regex, llm_result, fields=merge_fields)
        payment_merged = {f: str(payment_extracted.get(f, "") or "").strip() for f in PAYMENT_FIELDS}

        result = {
            "raw_text": full_text[:2000],
            "extracted": merged,
            "payment_extracted": payment_merged,
            "extracted_by": source_map,
            "regex_extracted": merged_regex,
            "llm_extracted": llm_result,
            "ocr_items": ocr_items,
            "source": source,
        }

    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"文件解析失败: {str(e)}")

    return {
        "message": "识别完成",
        "file_type": ext,
        "file_name": file.filename,
        **result,
    }
