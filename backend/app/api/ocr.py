# ============================================================
#  独立 OCR 识别接口 - 不绑定项目，正则 + LLM 综合提取
# ============================================================
import logging
import tempfile
import os

from fastapi import APIRouter, Depends, UploadFile, File

from app.dependencies import get_current_user
from app.models.user import User
from app.utils.file_utils import validate_file_type, validate_file_size
from app.core.contract_parser import (
    parse_word_contract_with_llm, parse_pdf_contract_with_llm,
    _merge_extracted, CONTRACT_FIELDS,
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
):
    """
    独立 OCR 识别：上传文件（Word/PDF/图片），正则 + LLM 综合提取。
    不写入数据库，不绑定项目。
    """
    ext = validate_file_type(file.filename, "all")
    content = await file.read()
    validate_file_size(len(content))

    try:
        if ext == ".docx":
            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            try:
                result = await parse_word_contract_with_llm(tmp_path)
            finally:
                os.unlink(tmp_path)

        elif ext == ".pdf":
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            try:
                result = await parse_pdf_contract_with_llm(tmp_path)
            finally:
                os.unlink(tmp_path)

        elif ext in IMAGE_EXTENSIONS:
            ocr_items = ocr_from_image_bytes(content)
            full_text = "\n".join([item["text"] for item in ocr_items])

            # 正则提取（合同 + 发票）
            contract_extracted = extractor.extract(full_text)
            invoice_extracted = _extract_invoice_fields(full_text)

            # LLM 提取
            llm_result = {}
            try:
                from app.core.llm_extractor import llm_extractor
                llm_result = await llm_extractor.extract(full_text)
            except Exception as e:
                logger.warning(f"图片 LLM 提取失败: {e}")

            # 合并：LLM 优先，正则兜底
            merged_regex = {**invoice_extracted, **contract_extracted}
            merged, source_map = _merge_extracted(merged_regex, llm_result)

            result = {
                "raw_text": full_text[:2000],
                "extracted": merged,
                "extracted_by": source_map,
                "regex_extracted": merged_regex,
                "llm_extracted": llm_result,
                "ocr_items": ocr_items,
                "source": "paddleocr",
            }
        else:
            raise ValidationError(f"不支持的文件类型: {ext}")

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


def _extract_invoice_fields(text: str) -> dict:
    """从发票文本中提取关键字段。"""
    import re

    fields = {}

    m = re.search(r"发票号码[：:]\s*(\d+)", text)
    if m:
        fields["invoice_no"] = m.group(1)

    m = re.search(r"发票代码[：:]\s*(\d+)", text)
    if m:
        fields["invoice_code"] = m.group(1)

    m = re.search(r"[¥￥]\s*([\d,]+\.?\d*)", text)
    if m:
        fields["amount"] = m.group(1).replace(",", "")

    m = re.search(r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", text)
    if m:
        fields["invoice_date"] = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"

    m = re.search(r"购买方[：:]\s*(.+?)(?:\n|$)", text)
    if m:
        fields["buyer_name"] = m.group(1).strip()

    m = re.search(r"销售方[：:]\s*(.+?)(?:\n|$)", text)
    if m:
        fields["seller_name"] = m.group(1).strip()

    return fields
