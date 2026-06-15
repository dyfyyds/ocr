# ============================================================
#  LLM 客户端 - OpenAI 兼容接口（httpx 直连）
# ============================================================
import httpx
import asyncio
import json
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """轻量 LLM 客户端，支持 OpenAI Chat Completions 兼容接口。"""

    def __init__(self):
        self._api_url = settings.LLM_API_URL
        self._api_key = settings.LLM_API_KEY
        self._model = settings.LLM_MODEL

    async def _do_chat(
        self,
        api_url: str,
        api_key: str,
        model: str,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
        timeout: int,
        retries: int,
    ) -> str:
        """底层请求逻辑，支持外部传入配置。"""
        if not api_key:
            raise ValueError("LLM API Key 未配置")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "top_p": 0.9,
            "max_tokens": max_tokens,
            "stream": False,
        }

        last_exc = None
        for attempt in range(retries):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    resp = await client.post(api_url, headers=headers, json=body)
                    resp.raise_for_status()
                    data = resp.json()
                    return data["choices"][0]["message"]["content"]
            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                if status == 429:
                    wait = min(10, 2 ** attempt)
                    logger.warning(f"LLM 请求被限流，{wait}s 后重试 (attempt {attempt + 1})")
                    await asyncio.sleep(wait)
                    last_exc = e
                    continue
                if status in (401, 403):
                    raise ValueError("LLM 服务认证失败，请检查 API Key 配置")
                if status == 404:
                    raise ValueError("LLM 服务接口不存在，请检查 API URL 配置")
                raise
            except (httpx.TimeoutException, httpx.NetworkError) as e:
                wait = min(10, 2 ** attempt)
                logger.warning(f"LLM 请求超时/网络错误，{wait}s 后重试 (attempt {attempt + 1})")
                await asyncio.sleep(wait)
                last_exc = e
                continue

        raise ConnectionError(f"LLM 服务不可用，已重试 {retries} 次: {last_exc}")

    async def chat(
        self,
        messages: list[dict],
        temperature: float = 0.1,
        max_tokens: int = 2048,
        timeout: int = 120,
        retries: int = 3,
    ) -> str:
        """
        非流式对话请求（使用启动时的 env 配置）。
        返回 LLM 回复的文本内容。
        """
        return await self._do_chat(
            self._api_url, self._api_key, self._model,
            messages, temperature, max_tokens, timeout, retries,
        )

    async def chat_with_config(
        self,
        config: dict,
        messages: list[dict],
        temperature: float = 0.1,
        max_tokens: int = 2048,
        timeout: int = 120,
        retries: int = 3,
    ) -> str:
        """
        非流式对话请求（使用外部传入的 DB 配置）。
        config: {"llm_api_url", "llm_api_key", "llm_model"}
        """
        return await self._do_chat(
            config.get("llm_api_url", ""),
            config.get("llm_api_key", ""),
            config.get("llm_model", "mimo-v2.5-pro"),
            messages, temperature, max_tokens, timeout, retries,
        )


# 单例
_llm_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
