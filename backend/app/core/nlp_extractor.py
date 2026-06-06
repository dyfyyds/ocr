# ============================================================
#  NLP 实体提取 - jieba + 正则提取关键字段
# ============================================================
import re
import logging

logger = logging.getLogger(__name__)


class NlpExtractor:
    """从 OCR 文本中提取结构化字段。"""

    # 金额模式：支持 "580,000.00元"、"人民币58万元"、"¥580000" 等
    AMOUNT_PATTERNS = [
        r"[¥￥]\s*([\d,]+\.?\d*)",
        r"([\d,]+\.?\d*)\s*元",
        r"人民币\s*([\d,]+\.?\d*)\s*万?元?",
        r"合同金额[：:]\s*([\d,]+\.?\d*)",
        r"总[金价]额[：:]\s*([\d,]+\.?\d*)",
        r"价款[：:]\s*([\d,]+\.?\d*)",
    ]

    # 合同编号模式
    CONTRACT_NO_PATTERNS = [
        r"合同编号[：:]\s*([A-Za-z0-9\-]+)",
        r"编号[：:]\s*([A-Za-z0-9\-]+)",
        r"HT[-\s]?(\d{4}[-\s]?\d+)",
        r"协议编号[：:]\s*([A-Za-z0-9\-]+)",
    ]

    # 日期模式
    DATE_PATTERNS = [
        r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日",
        r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})",
        r"签订日期[：:]\s*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2})",
    ]

    # 项目名称模式
    PROJECT_NAME_PATTERNS = [
        r"项目名称[：:]\s*(.+?)(?:\n|$|[，。])",
        r"项目[：:]\s*(.+?)(?:\n|$|[，。])",
        r"关于[《「](.+?)[》」]的?(?:合同|协议)",
        r"[《「](.+?)(?:合同|协议)[》」]",
    ]

    # 客户名称模式
    CUSTOMER_PATTERNS = [
        r"甲\s*方[：:]\s*(.+?)(?:\n|$|[（(])",
        r"委托方[：:]\s*(.+?)(?:\n|$)",
        r"发包方[：:]\s*(.+?)(?:\n|$)",
        r"采购人[：:]\s*(.+?)(?:\n|$)",
    ]

    def extract(self, text: str) -> dict:
        """
        从文本中提取关键字段。
        返回: {
            "project_name": "...",
            "contract_amount": "...",
            "contract_no": "...",
            "sign_date": "...",
            "customer_name": "...",
        }
        """
        return {
            "project_name": self._extract_project_name(text),
            "contract_amount": self._extract_amount(text),
            "contract_no": self._extract_contract_no(text),
            "sign_date": self._extract_date(text),
            "customer_name": self._extract_customer(text),
        }

    def _extract_amount(self, text: str) -> str:
        """提取金额。"""
        for pattern in self.AMOUNT_PATTERNS:
            match = re.search(pattern, text)
            if match:
                amount_str = match.group(1).replace(",", "")
                try:
                    amount = float(amount_str)
                    # 检查是否是"万"单位
                    if "万" in text[match.start():match.end() + 5]:
                        amount *= 10000
                    return f"{amount:.2f}"
                except ValueError:
                    continue
        return ""

    def _extract_contract_no(self, text: str) -> str:
        """提取合同编号。"""
        for pattern in self.CONTRACT_NO_PATTERNS:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        return ""

    def _extract_date(self, text: str) -> str:
        """提取签订日期。"""
        for pattern in self.DATE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                groups = match.groups()
                if len(groups) == 3:
                    y, m, d = groups
                    return f"{y}-{int(m):02d}-{int(d):02d}"
                elif len(groups) == 1:
                    return groups[0].replace("年", "-").replace("月", "-").replace("日", "")
        return ""

    def _extract_project_name(self, text: str) -> str:
        """提取项目名称。"""
        for pattern in self.PROJECT_NAME_PATTERNS:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        return ""

    def _extract_customer(self, text: str) -> str:
        """提取客户名称。"""
        for pattern in self.CUSTOMER_PATTERNS:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        return ""


# 单例
extractor = NlpExtractor()
