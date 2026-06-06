# ============================================================
#  合同解析器 - Word/PDF 文本提取 + NLP 实体提取
# ============================================================
import logging

from app.core.nlp_extractor import extractor

logger = logging.getLogger(__name__)


def parse_word_contract(file_path: str) -> dict:
    """
    解析 Word 合同文件，提取文本并进行 NLP 实体提取。
    返回: {"raw_text": "...", "extracted": {...}}
    """
    import docx

    doc = docx.Document(file_path)
    full_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

    extracted = extractor.extract(full_text)

    return {
        "raw_text": full_text[:2000],  # 截断避免过大
        "extracted": extracted,
        "source": "python-docx",
    }


def parse_pdf_contract(file_path: str) -> dict:
    """
    解析 PDF 合同文件。
    优先用 pdfplumber 提取文本，扫描件则调用 OCR。
    返回: {"raw_text": "...", "extracted": {...}, "ocr_items": [...]}
    """
    from app.core.ocr_engine import ocr_from_pdf_bytes

    with open(file_path, "rb") as f:
        pdf_bytes = f.read()

    ocr_items = ocr_from_pdf_bytes(pdf_bytes)

    # 拼接所有识别文本
    full_text = "\n".join([item["text"] for item in ocr_items])

    extracted = extractor.extract(full_text)

    return {
        "raw_text": full_text[:2000],
        "extracted": extracted,
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
