# ============================================================
#  NLP 实体提取 - jieba + 正则提取关键字段
# ============================================================
import re
import logging

logger = logging.getLogger(__name__)


class NlpExtractor:
    """从 OCR 文本中提取结构化字段。"""

    # 金额模式：支持多种常见合同写法
    AMOUNT_PATTERNS = [
        r"[¥￥]\s*([\d,]+\.?\d*)",
        r"人民币\s*([\d,]+\.?\d*)\s*万?元?",
        r"合同金额[：:]\s*([\d,]+\.?\d*)",
        r"合同总[金价][额格][：:]\s*([\d,]+\.?\d*)",
        r"总[金价]额[：:]\s*([\d,]+\.?\d*)",
        r"项目金额[：:]\s*([\d,]+\.?\d*)",
        r"价款[：:]\s*([\d,]+\.?\d*)",
        r"工程造价[：:]\s*([\d,]+\.?\d*)",
        r"服务费[：:]\s*([\d,]+\.?\d*)",
        r"成交金额[：:]\s*([\d,]+\.?\d*)",
        r"中标价[：:]\s*([\d,]+\.?\d*)",
        r"([\d,]+\.?\d*)\s*元",
    ]

    # 合同编号模式
    CONTRACT_NO_PATTERNS = [
        r"合同编号[：:]\s*([A-Za-z0-9\-/]+)",
        r"合同号[：:]\s*([A-Za-z0-9\-/]+)",
        r"合同/立项编码[：:]\s*([A-Za-z0-9\-/]+)",
        r"协议编号[：:]\s*([A-Za-z0-9\-/]+)",
        r"编号[：:]\s*([A-Za-z0-9\-/]+)",
        r"No[.：:]\s*([A-Za-z0-9\-/]+)",
        r"(HT[-\s]?\d{4}[-\s/]\d+)",
        r"(ZC[-\s]?\d{4}[-\s/]\d+)",
        r"(XY[-\s]?\d{4}[-\s/]\d+)",
    ]

    # 日期模式
    DATE_PATTERNS = [
        r"签订日期[：:]\s*(\d{4}[-/年.]\d{1,2}[-/月.]\d{1,2})",
        r"签订日期\s+(\d{4}年\d{1,2}月\d{1,2}日)",
        r"签约日期[：:]\s*(\d{4}[-/年.]\d{1,2}[-/月.]\d{1,2})",
        r"签署日期[：:]\s*(\d{4}[-/年.]\d{1,2}[-/月.]\d{1,2})",
        r"签订时间[：:]\s*(\d{4}[-/年.]\d{1,2}[-/月.]\d{1,2})",
        r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日",
        r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})",
    ]

    # 项目名称模式（支持中文引号""和书名号《》）
    PROJECT_NAME_PATTERNS = [
        r"项目名称[：:]\s*(.+?)(?:\n|$|[，。；])",
        r"工程名称[：:]\s*(.+?)(?:\n|$|[，。；])",
        r"项目名[：:]\s*(.+?)(?:\n|$|[，。；])",
        r"合同名称[：:]\s*(.+?)(?:\n|$|[，。；])",
        r"项目[：:]\s*(.+?)(?:\n|$|[，。；])",
        r"关于[《](.+?)[》]的?(?:合同|协议|项目)",
        r"[《](.+?)(?:合同|协议|项目)[》]",
        r'拟建设[“”"](.+?)[“”"]',
        r'[“”"](.+?)(?:项目|工程|系统|平台)[“”"]',
    ]

    # 客户名称模式（甲方后面可能有括号说明，如"甲方（委托方）："）
    CUSTOMER_PATTERNS = [
        r"甲\s*方[（(][^）)]*[）)][：:]\s*(.+?)(?:\n|$)",
        r"甲\s*方[：:]\s*(.+?)(?:\n|$)",
        r"委托方[：:]\s*(.+?)(?:\n|$)",
        r"发包方[：:]\s*(.+?)(?:\n|$)",
        r"采购人[：:]\s*(.+?)(?:\n|$)",
        r"招标人[：:]\s*(.+?)(?:\n|$)",
        r"客户名称[：:]\s*(.+?)(?:\n|$)",
        r"业主[：:]\s*(.+?)(?:\n|$)",
        r"甲方单位[：:]\s*(.+?)(?:\n|$)",
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
                amount_str = match.group(1).replace(",", "").replace("，", "")
                try:
                    amount = float(amount_str)
                    # 检查匹配附近是否有"万"单位
                    context = text[max(0, match.start() - 5):match.end() + 10]
                    if "万" in context:
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
                    date_str = groups[0]
                    # 统一分隔符为 "-"
                    date_str = date_str.replace("年", "-").replace("月", "-").replace("日", "")
                    date_str = date_str.replace("/", "-").replace(".", "-")
                    # 补零
                    parts = date_str.split("-")
                    if len(parts) == 3:
                        return f"{parts[0]}-{int(parts[1]):02d}-{int(parts[2]):02d}"
                    return date_str
        return ""

    def _extract_project_name(self, text: str) -> str:
        """提取项目名称。"""
        for pattern in self.PROJECT_NAME_PATTERNS:
            match = re.search(pattern, text)
            if match:
                name = match.group(1).strip()
                # 清理末尾的标点和多余空格
                name = name.rstrip('，。；、')
                if len(name) > 1:
                    return name
        return ""

    def _extract_customer(self, text: str) -> str:
        """提取客户名称。"""
        for pattern in self.CUSTOMER_PATTERNS:
            match = re.search(pattern, text)
            if match:
                name = match.group(1).strip()
                # 清理末尾的括号内容（如"（盖章）"）和标点
                name = re.sub(r'[（(].*?[）)]$', '', name).strip()
                name = name.rstrip('，。；、')
                if len(name) > 1:
                    return name
        return ""


# 单例
extractor = NlpExtractor()
