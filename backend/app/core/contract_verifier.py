# ============================================================
#  合同校验引擎 - 比对 OCR 提取值与录入值
# ============================================================
import re
from datetime import datetime


class ContractVerifier:
    """合同校验：逐字段模糊比对。"""

    VERIFY_FIELDS = ["project_name", "contract_amount", "contract_no", "sign_date"]

    def verify(self, ocr_data: dict, input_data: dict) -> list[dict]:
        """
        比对 OCR 提取值与录入值，返回差异列表。
        返回: [{"field_name": ..., "ocr_value": ..., "input_value": ..., "diff_type": ...}, ...]
        """
        diffs = []
        for field in self.VERIFY_FIELDS:
            ocr_val = str(ocr_data.get(field, "") or "").strip()
            input_val = str(input_data.get(field, "") or "").strip()

            if not ocr_val and not input_val:
                continue

            if not self._fuzzy_equal(ocr_val, input_val, field):
                diff_type = self._classify_diff(ocr_val, input_val, field)
                diffs.append({
                    "field_name": field,
                    "ocr_value": ocr_val,
                    "input_value": input_val,
                    "diff_type": diff_type,
                })

        return diffs

    def _fuzzy_equal(self, a: str, b: str, field: str) -> bool:
        """模糊比对。"""
        if not a or not b:
            return a == b

        if field == "contract_amount":
            return self._amount_equal(a, b)
        elif field == "sign_date":
            return self._date_equal(a, b)
        else:
            return self._text_equal(a, b)

    def _amount_equal(self, a: str, b: str) -> bool:
        """金额比对：忽略格式差异。"""
        try:
            va = float(re.sub(r"[,，¥￥\s]", "", a))
            vb = float(re.sub(r"[,，¥￥\s]", "", b))
            return abs(va - vb) < 0.01
        except ValueError:
            return a == b

    def _date_equal(self, a: str, b: str) -> bool:
        """日期比对：统一格式后比较。"""
        na = self._normalize_date(a)
        nb = self._normalize_date(b)
        return na == nb if na and nb else a == b

    def _normalize_date(self, s: str) -> str | None:
        """统一日期格式为 YYYY-MM-DD。"""
        # 2026年6月5日 -> 2026-06-05
        m = re.search(r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", s)
        if m:
            return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
        # 2026-06-05
        m = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", s)
        if m:
            return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
        return None

    def _text_equal(self, a: str, b: str) -> bool:
        """文本比对：忽略空格和标点。"""
        def normalize(s):
            return re.sub(r"[\s　，。、；：""''（）《》【】]", "", s)
        return normalize(a) == normalize(b)

    def _classify_diff(self, ocr_val: str, input_val: str, field: str) -> str:
        """分类差异类型。"""
        if not ocr_val:
            return "missing"
        if not input_val:
            return "missing"
        if field == "contract_amount":
            return "format"
        return "mismatch"


# 单例
verifier = ContractVerifier()
