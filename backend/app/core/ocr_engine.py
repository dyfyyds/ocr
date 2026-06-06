# ============================================================
#  OCR 引擎封装 - PaddleOCR 本地识别
# ============================================================
import logging
import numpy as np
import cv2

logger = logging.getLogger(__name__)

# 延迟加载，避免启动时就初始化
_ocr_instance = None


def get_ocr():
    """获取 PaddleOCR 单例（首次调用时初始化）。"""
    global _ocr_instance
    if _ocr_instance is None:
        logger.info("正在初始化 PaddleOCR 引擎...")
        from paddleocr import PaddleOCR
        _ocr_instance = PaddleOCR(lang="ch")
        logger.info("PaddleOCR 引擎初始化完成")
    return _ocr_instance


def ocr_from_image_bytes(image_bytes: bytes) -> list[dict]:
    """
    从图片字节流进行 OCR 识别。
    返回: [{"text": "识别文本", "confidence": 0.97, "box": [[x1,y1], ...]}, ...]
    """
    ocr = get_ocr()

    # bytes -> numpy array
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("无法解码图片")

    result = ocr.predict(img)

    items = []
    if result and len(result) > 0:
        page = result[0]
        if "rec_texts" in page:
            for i, text in enumerate(page["rec_texts"]):
                score = page["rec_scores"][i] if i < len(page["rec_scores"]) else 0
                box = page["rec_polys"][i].tolist() if i < len(page["rec_polys"]) else []
                items.append({
                    "text": text,
                    "confidence": round(float(score), 4),
                    "box": box,
                })

    return items


def ocr_from_pdf_bytes(pdf_bytes: bytes) -> list[dict]:
    """
    从 PDF 字节流进行 OCR 识别。
    先尝试 pdfplumber 提取文本，若为空则转图片后 OCR。
    """
    import pdfplumber
    from io import BytesIO

    # 先尝试直接提取文本
    texts = []
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text and text.strip():
                texts.append(text.strip())

    # 如果直接提取到文本，返回结构化结果
    if texts:
        items = []
        for i, text in enumerate(texts):
            items.append({
                "text": text,
                "confidence": 1.0,
                "box": [],
                "source": "pdfplumber",
            })
        return items

    # PDF 无文本层（扫描件），转图片后 OCR
    items = []
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for page_num, page in enumerate(pdf.pages):
            img = page.to_image(resolution=200).original
            img_bytes = cv2.imencode(".png", np.array(img))[1].tobytes()
            page_items = ocr_from_image_bytes(img_bytes)
            for item in page_items:
                item["page"] = page_num + 1
            items.extend(page_items)

    return items
