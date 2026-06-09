# ============================================================
#  合同解析器 - Word/PDF 文本提取 + 正则 + LLM 综合提取
# ============================================================
import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.nlp_extractor import extractor

logger = logging.getLogger(__name__)

# 合同关键字段列表
CONTRACT_FIELDS = ("project_name", "contract_amount", "contract_no", "sign_date", "customer_name")


def _extract_text_from_docx(file_path: str) -> str:
    """从 Word 文件提取纯文本。"""
    import docx

    doc = docx.Document(file_path)
    parts = []
    for p in doc.paragraphs:
        if p.text.strip():
            parts.append(p.text.strip())
    for table in doc.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if cells:
                if len(cells) == 2 and len(cells[0]) <= 15 and '：' not in cells[0] and ':' not in cells[0]:
                    parts.append(f"{cells[0]}：{cells[1]}")
                else:
                    parts.append(' '.join(cells))
    return "\n".join(parts)


def _merge_extracted(regex_result: dict, llm_result: dict) -> tuple[dict, dict]:
    """
    合并正则提取和 LLM 提取结果。
    策略：LLM 优先，正则兜底。
    返回: (merged, extracted_by)
    """
    merged = {}
    source_map = {}
    for field in CONTRACT_FIELDS:
        llm_val = str(llm_result.get(field, "") or "").strip()
        regex_val = str(regex_result.get(field, "") or "").strip()
        if llm_val:
            merged[field] = llm_val
            source_map[field] = "llm"
        elif regex_val:
            merged[field] = regex_val
            source_map[field] = "regex"
        else:
            merged[field] = ""
            source_map[field] = ""
    return merged, source_map


def parse_word_contract(file_path: str) -> dict:
    """
    解析 Word 合同文件（同步，仅正则提取）。
    返回: {"raw_text": "...", "extracted": {...}}
    """
    full_text = _extract_text_from_docx(file_path)
    extracted = extractor.extract(full_text)

    return {
        "raw_text": full_text[:2000],
        "extracted": extracted,
        "source": "python-docx",
    }


async def _try_llm_extract(full_text: str, db: Optional[AsyncSession] = None) -> dict:
    """
    尝试 LLM 提取。若 db 存在则检查 llm_enabled 开关。
    返回 LLM 提取结果 dict，失败或关闭时返回空 dict。
    """
    if db is not None:
        from app.utils.config_helper import get_config_value
        enabled = await get_config_value(db, "llm_enabled", "false")
        if enabled.lower() != "true":
            logger.info("LLM 提取已关闭（llm_enabled=false），跳过")
            return {}

    try:
        from app.core.llm_extractor import llm_extractor
        return await llm_extractor.extract(full_text)
    except Exception as e:
        logger.warning(f"LLM 提取失败，降级为纯正则: {e}")
        return {}


async def parse_word_contract_with_llm(file_path: str, db: Optional[AsyncSession] = None) -> dict:
    """
    解析 Word 合同文件（异步，正则 + LLM 综合提取）。
    db: 可选数据库会话，传入时检查 llm_enabled 开关。
    返回: {"raw_text": "...", "extracted": {...}, "extracted_by": {...}, "llm_extracted": {...}}
    """
    full_text = _extract_text_from_docx(file_path)
    regex_result = extractor.extract(full_text)

    llm_result = await _try_llm_extract(full_text, db)

    merged, source_map = _merge_extracted(regex_result, llm_result)

    return {
        "raw_text": full_text[:2000],
        "extracted": merged,
        "extracted_by": source_map,
        "regex_extracted": regex_result,
        "llm_extracted": llm_result,
        "source": "python-docx",
    }


def parse_pdf_contract(file_path: str) -> dict:
    """
    解析 PDF 合同文件（同步，仅正则提取）。
    返回: {"raw_text": "...", "extracted": {...}, "ocr_items": [...]}
    """
    from app.core.ocr_engine import ocr_from_pdf_bytes

    with open(file_path, "rb") as f:
        pdf_bytes = f.read()

    ocr_items = ocr_from_pdf_bytes(pdf_bytes)
    full_text = "\n".join([item["text"] for item in ocr_items])
    extracted = extractor.extract(full_text)

    return {
        "raw_text": full_text[:2000],
        "extracted": extracted,
        "ocr_items": ocr_items,
        "source": "paddleocr",
    }


async def parse_pdf_contract_with_llm(file_path: str, db: Optional[AsyncSession] = None) -> dict:
    """
    解析 PDF 合同文件（异步，正则 + LLM 综合提取）。
    db: 可选数据库会话，传入时检查 llm_enabled 开关。
    返回: {"raw_text": "...", "extracted": {...}, "extracted_by": {...}, "llm_extracted": {...}, "ocr_items": [...]}
    """
    from app.core.ocr_engine import ocr_from_pdf_bytes

    with open(file_path, "rb") as f:
        pdf_bytes = f.read()

    ocr_items = ocr_from_pdf_bytes(pdf_bytes)
    full_text = "\n".join([item["text"] for item in ocr_items])
    regex_result = extractor.extract(full_text)

    llm_result = await _try_llm_extract(full_text, db)

    merged, source_map = _merge_extracted(regex_result, llm_result)

    return {
        "raw_text": full_text[:2000],
        "extracted": merged,
        "extracted_by": source_map,
        "regex_extracted": regex_result,
        "llm_extracted": llm_result,
        "ocr_items": ocr_items,
        "source": "paddleocr",
    }


def parse_invoice_image(file_path: str) -> dict:
    """
    解析发票图片，OCR 识别并提取关键字段。
    返回: {"raw_text": "...", "extracted": {...}, "ocr_items": [...]}
    """
    from app.core.ocr_engine import ocr_from_image_bytes

    with open(file_path, "rb") as f:
        image_bytes = f.read()

    ocr_items = ocr_from_image_bytes(image_bytes)

    full_text = "\n".join([item["text"] for item in ocr_items])

    # 发票专用提取
    extracted = _extract_invoice_fields(full_text)

    return {
        "raw_text": full_text[:2000],
        "extracted": extracted,
        "ocr_items": ocr_items,
        "source": "paddleocr",
    }


def _extract_invoice_fields(text: str) -> dict:
    """从发票文本中提取关键字段。"""
    import re

    fields = {}

    # 发票号码
    m = re.search(r"发票号码[：:]\s*(\d+)", text)
    if m:
        fields["invoice_no"] = m.group(1)

    # 发票代码
    m = re.search(r"发票代码[：:]\s*(\d+)", text)
    if m:
        fields["invoice_code"] = m.group(1)

    # 金额
    m = re.search(r"[¥￥]\s*([\d,]+\.?\d*)", text)
    if m:
        fields["amount"] = m.group(1).replace(",", "")

    # 开票日期
    m = re.search(r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", text)
    if m:
        fields["invoice_date"] = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"

    # 购买方
    m = re.search(r"购买方[：:]\s*(.+?)(?:\n|$)", text)
    if m:
        fields["buyer_name"] = m.group(1).strip()

    # 销售方
    m = re.search(r"销售方[：:]\s*(.+?)(?:\n|$)", text)
    if m:
        fields["seller_name"] = m.group(1).strip()

    return fields
