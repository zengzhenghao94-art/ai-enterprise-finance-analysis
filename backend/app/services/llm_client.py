"""LLM API 调用封装 —— 统一入口，支持通义千问和 DeepSeek"""

import os
from openai import OpenAI


def _get_client() -> OpenAI:
    api_key = os.getenv("LLM_API_KEY", "").strip()
    if not api_key or api_key == "your-api-key-here":
        raise ValueError(
            "LLM_API_KEY 未配置。请在 backend/.env 中填入你的 API Key。"
        )
    base_url = os.getenv("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    return OpenAI(api_key=api_key, base_url=base_url, timeout=30.0)


def query_llm(prompt: str, system_prompt: str = None, model: str = None) -> str:
    """调用 LLM 获取回复文本

    Args:
        prompt: 用户消息
        system_prompt: 系统提示（可选）
        model: 模型名（可选，默认从 LLM_MODEL 环境变量读取）

    Returns:
        LLM 回复的文本内容
    """
    client = _get_client()
    model = model or os.getenv("LLM_MODEL", "qwen-plus")

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.3,
    )

    return response.choices[0].message.content or ""


def estimate_tokens(prompt: str, system_prompt: str = None) -> int:
    """粗略估算 token 消耗（按 1 汉字 ≈ 2 tokens 估算）"""
    total_chars = len(prompt)
    if system_prompt:
        total_chars += len(system_prompt)
    return total_chars * 2
