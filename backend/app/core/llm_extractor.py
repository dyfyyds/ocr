# ============================================================
#  LLM 字段提取器 - 用大模型从合同文本中提取结构化字段
# ============================================================
import json
import logging
import re

from app.core.llm_client import get_llm_client

logger = logging.getLogger(__name__)

# 系统提示词
SYSTEM_PROMPT = """你是一个合同信息提取专家。从给定的合同文本中提取以下字段，以 JSON 格式返回：

{
  "project_name": "项目名称/工程名称",
  "contract_amount": "合同金额（纯数字，不含货币符号和逗号，保留两位小数）",
  "contract_no": "合同编号",
  "sign_date": "签订日期（格式：YYYY-MM-DD）",
  "customer_name": "甲方/客户名称"
}

规则：
1. 只提取文本中明确存在的信息，不要猜测
2. 找不到的字段返回空字符串 ""
3. 金额统一转为数字（如"伍万元整"→"50000.00"，"12.5万"→"125000.00"）
4. 日期统一为 YYYY-MM-DD 格式
5. 只返回 JSON，不要其他文字"""


class LLMExtractor:
    """用 LLM 从合同文本中提取结构化字段。"""

    async def extract(self, raw_text: str) -> dict:
        """
        调用 LLM 提取合同关键字段。
        返回: {"project_name", "contract_amount", "contract_no", "sign_date", "customer_name"}
        失败时返回空 dict。
        """
        if not raw_text or not raw_text.strip():
            return {}

        client = get_llm_client()
        # 截断过长文本，避免超 token 限制
        text = raw_text[:4000]

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"请从以下合同文本中提取信息：\n\n{text}"},
        ]

        try:
            content = await client.chat(messages, temperature=0.1, max_tokens=1024)
            return self._parse_response(content)
        except Exception as e:
            logger.error(f"LLM 字段提取失败: {e}")
            return {}

    def _parse_response(self, content: str) -> dict:
        """解析 LLM 返回的 JSON。容错处理 markdown 代码块。"""
        content = content.strip()

        # 去掉 markdown 代码块标记
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```$", "", content)

        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            # 尝试从文本中提取 JSON
            m = re.search(r"\{[^{}]+\}", content, re.DOTALL)
            if m:
                try:
                    data = json.loads(m.group())
                except json.JSONDecodeError:
                    logger.warning(f"无法解析 LLM 返回: {content[:200]}")
                    return {}
            else:
                logger.warning(f"LLM 返回中未找到 JSON: {content[:200]}")
                return {}

        # 规范化字段
        result = {}
        for key in ("project_name", "contract_amount", "contract_no", "sign_date", "customer_name"):
            val = data.get(key, "")
            if val is None:
                val = ""
            result[key] = str(val).strip()

        # 规范化金额
        amount = result.get("contract_amount", "")
        if amount:
            amount = amount.replace(",", "").replace("，", "").replace("¥", "").replace("￥", "")
            try:
                result["contract_amount"] = f"{float(amount):.2f}"
            except ValueError:
                pass  # 保留原值

        return result


    async def analyze_versions(self, versions: list[dict]) -> str:
        """
        用 LLM 分析多版本 OCR 结果的差异。
        versions: [{"version": 1, "raw_text": "...", "extracted": {...}}, ...]
        返回: 分析报告文本
        """
        if len(versions) < 2:
            return "需要至少两个版本才能进行对比分析。"

        client = get_llm_client()

        # 构造对比描述
        parts = []
        for v in versions:
            ext = v.get("extracted", {})
            parts.append(
                f"【版本 v{v['version']}】\n"
                f"项目名称: {ext.get('project_name', '未识别')}\n"
                f"合同金额: {ext.get('contract_amount', '未识别')}\n"
                f"合同编号: {ext.get('contract_no', '未识别')}\n"
                f"签订日期: {ext.get('sign_date', '未识别')}\n"
                f"客户名称: {ext.get('customer_name', '未识别')}\n"
                f"原始文本片段: {v.get('raw_text', '')[:1000]}\n"
            )

        versions_text = "\n---\n".join(parts)

        prompt = f"""请对比分析以下同一项目的多版本合同 OCR 识别结果，指出：
1. 各版本之间的关键字段差异（金额、编号、日期、名称等）
2. 哪些变化是格式差异（不影响实质），哪些是内容变更（需要关注）
3. 给出综合建议

{versions_text}"""

        messages = [
            {"role": "system", "content": "你是合同分析专家，请用中文回答，条理清晰。"},
            {"role": "user", "content": prompt},
        ]

        try:
            return await client.chat(messages, temperature=0.3, max_tokens=2048)
        except Exception as e:
            logger.error(f"LLM 版本分析失败: {e}")
            return f"版本分析失败: {str(e)}"


# 单例
llm_extractor = LLMExtractor()
