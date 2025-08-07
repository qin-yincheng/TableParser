import os
import re
import json
import logging
import asyncio
import base64
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
    messages: Optional[List[Dict]] = None,
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
    
    # 如果提供了messages，直接使用；否则构建messages
    if messages:
        final_messages = messages
    else:
        final_messages = []
        if not system_prompt:
            system_prompt = "You are a helpful assistant."
        final_messages.append({"role": "system", "content": system_prompt})
        if history_messages:
            final_messages.extend(history_messages)
        final_messages.append({"role": "user", "content": prompt})
    
    logger.debug(f"ZhipuAI request with {len(final_messages)} messages")
    response = client.chat.completions.create(
        model=model,
        messages=final_messages,
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


class VisionModelClient:
    """智普视觉模型客户端"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ZHIPUAI_API_KEY")
        if not self.api_key:
            raise ValueError("ZHIPUAI_API_KEY 未设置")
    
    async def analyze_image(self, image_path: str, prompt: str) -> Dict:
        """分析图片内容"""
        try:
            # 读取图片文件
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # 构建消息 - 使用智普AI GLM-4V-Plus的正确格式
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64.b64encode(image_data).decode('utf-8')}"
                            }
                        }
                    ]
                }
            ]
            
            # 调用智普API
            response = await zhipu_complete_async(
                prompt="",  # 空prompt，使用messages
                api_key=self.api_key,
                model="glm-4v-plus",
                messages=messages,
                temperature=0.1,
                timeout=60,
                max_tokens=1000
            )
            
            # 解析响应
            result = parse_json_response(response)
            logger.info(f"图片分析完成: {image_path}")
            return result
            
        except Exception as e:
            logger.error(f"图片分析失败: {image_path}, 错误: {str(e)}")
            return self.get_fallback_result()
    
    def get_fallback_result(self) -> Dict:
        """获取回退结果"""
        return {
            "description": "图片分析失败，无法获取详细信息",
            "keywords": ["图片", "分析失败"],
            "image_type": "unknown",
            "context_relation": "无法确定与文档的关系",
            "key_information": []
        }
