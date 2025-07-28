import os
import re
import json
import logging
from typing import List, Dict, Optional, Union
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from utils.config import LLM_CONFIG

try:
    from zhipuai import ZhipuAI
except ImportError:
    raise ImportError("Please install zhipuai before using zhipu_client.")

from openai import APIConnectionError, RateLimitError, APITimeoutError

logger = logging.getLogger("zhipu_client")


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(
        (RateLimitError, APIConnectionError, APITimeoutError)
    ),
)
async def zhipu_complete_async(
    prompt: str,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    system_prompt: Optional[str] = None,
    history_messages: Optional[List[Dict[str, str]]] = None,
    temperature: Optional[float] = None,
    timeout: Optional[int] = None,
    max_tokens: Optional[int] = None,
    **kwargs,
) -> str:
    """异步调用智普API，返回模型输出字符串。"""
    if api_key is None:
        api_key = LLM_CONFIG["api_key"]
    if model is None:
        model = LLM_CONFIG["model"]
    if temperature is None:
        temperature = LLM_CONFIG["temperature"]
    if timeout is None:
        timeout = LLM_CONFIG["timeout"]
    if max_tokens is None:
        max_tokens = LLM_CONFIG["max_tokens"]
    client = ZhipuAI(api_key=api_key)
    messages = []
    if not system_prompt:
        system_prompt = "You are a helpful assistant."
    messages.append({"role": "system", "content": system_prompt})
    if history_messages:
        messages.extend(history_messages)
    messages.append({"role": "user", "content": prompt})
    logger.debug(f"ZhipuAI prompt: {prompt}")
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        timeout=timeout,
        max_tokens=max_tokens,
        **kwargs,
    )
    return response.choices[0].message.content


def parse_json_response(response: str) -> Dict[str, Union[str, List[str]]]:
    """健壮解析模型输出为JSON，失败时返回空结构。"""
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", response)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        logger.warning(f"Failed to parse JSON from response: {response}")
        return {"description": "", "keywords": []}


def get_prompt_for_chunk(chunk_type: str, content: str) -> str:
    """根据分块类型生成合适的Prompt。"""
    if chunk_type == "table_full":
        return f'请分析下表内容，输出如下JSON结构：\n{{\n  "description": "一句话描述表格主题和主要内容",\n  "keywords": ["关键词1", "关键词2", "关键词3"]\n}}\n表格内容如下：\n{content}'
    elif chunk_type == "table_row":
        return f'请分析下表格的这一行，输出如下JSON结构：\n{{\n  "description": "一句话描述该行数据的含义",\n  "keywords": ["关键词1", "关键词2"]\n}}\n表格行内容如下：\n{content}'
    else:
        return f'请分析下述文本，输出如下JSON结构：\n{{\n  "description": "一句话总结文本内容",\n  "keywords": ["关键词1", "关键词2"]\n}}\n文本内容如下：\n{content}'


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(
        (RateLimitError, APIConnectionError, APITimeoutError)
    ),
)
async def zhipu_embedding_async(
    text: str,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    **kwargs,
) -> List[float]:
    """异步调用智普嵌入API，返回向量嵌入。"""
    from utils.config import EMBEDDING_CONFIG

    if api_key is None:
        api_key = EMBEDDING_CONFIG["api_key"]
    if model is None:
        model = EMBEDDING_CONFIG["model"]

    client = ZhipuAI(api_key=api_key)
    logger.debug(f"ZhipuAI embedding request for text length: {len(text)}")

    response = client.embeddings.create(
        model=model,
        input=text,
        **kwargs,
    )

    # 返回嵌入向量
    return response.data[0].embedding
