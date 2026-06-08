# ============================================================
#  独立 OCR 识别接口 - 不绑定项目，直接上传文件识别
# ============================================================
from fastapi import APIRouter, Depends, UploadFile, File

from app.dependencies import get_current_user
from app.models.user import User
from app.utils.file_utils import validate_file_type, validate_file_size
from app.core.contract_parser import parse_word_contract, parse_pdf_contract
from app.core.ocr_engine import ocr_from_image_bytes
from app.core.nlp_extractor import extractor
from app.exceptions import ValidationError

router = APIRouter()

# 图片类型集合
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}


@router.post("/recognize")
async def recognize_file(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    """
    独立 OCR 识别：上传文件（Word/PDF/图片），返回识别结果。
    不写入数据库，不绑定项目。
    """
    # 校验文件类型（允许所有支持的类型）
    ext = validate_file_type(file.filename, "all")
    content = await file.read()
    validate_file_size(len(content))

    try:
        if ext == ".docx":
            # Word 文件：保存临时文件后用 python-docx 解析
            import tempfile, os
            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            try:
                result = parse_word_contract(tmp_path)
            finally:
                os.unlink(tmp_path)

        elif ext == ".pdf":
            # PDF 文件：保存临时文件后用 pdfplumber + PaddleOCR 解析
            import tempfile, os
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            try:
                result = parse_pdf_contract(tmp_path)
            finally:
                os.unlink(tmp_path)

        elif ext in IMAGE_EXTENSIONS:
            # 图片文件：直接用 PaddleOCR 识别
            ocr_items = ocr_from_image_bytes(content)
            full_text = "\n".join([item["text"] for item in ocr_items])

            # 同时尝试合同字段提取和发票字段提取
            contract_extracted = extractor.extract(full_text)
            invoice_extracted = _extract_invoice_fields(full_text)

            # 合并提取结果（合同字段优先，发票字段补充）
            merged = {**invoice_extracted, **contract_extracted}

            result = {
                "raw_text": full_text[:2000],
                "extracted": merged,
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
