# embedding_service.py
"""
向量化服务，负责为分块生成向量嵌入
"""

import asyncio
from typing import List, Dict, Any, Optional
from utils.logger import logger
from utils.zhipu_client import zhipu_embedding_async
from utils.config import EMBEDDING_CONFIG


class EmbeddingService:
    """向量化服务类，负责为分块生成向量嵌入"""

    def __init__(self):
        """初始化向量化服务"""
        pass

    async def generate_embedding(self, chunk: Dict[str, Any]) -> Optional[List[float]]:
        """
        为单个分块生成向量嵌入

        Args:
            chunk: 分块数据字典

        Returns:
            List[float]: 向量嵌入，失败时返回None
        """
        try:
            # 构建向量化输入文本
            embedding_text = self._build_embedding_text(chunk)

            # 调用智普API生成向量
            vector = await zhipu_embedding_async(
                text=embedding_text,
                api_key=EMBEDDING_CONFIG["api_key"],
                model=EMBEDDING_CONFIG["model"],
            )

            return vector

        except Exception as e:
            logger.error(f"生成向量嵌入失败: {str(e)}")
            return None

    async def generate_embeddings_batch(
        self, chunks: List[Dict[str, Any]]
    ) -> List[Optional[List[float]]]:
        """
        批量为分块生成向量嵌入

        Args:
            chunks: 分块数据列表

        Returns:
            List[Optional[List[float]]]: 向量嵌入列表，失败时为None
        """
        tasks = [self.generate_embedding(chunk) for chunk in chunks]
        return await asyncio.gather(*tasks, return_exceptions=True)

    def _build_embedding_text(self, chunk: Dict[str, Any]) -> str:
        """
        构建用于向量化的文本

        Args:
            chunk: 分块数据字典

        Returns:
            str: 用于向量化的文本
        """
        chunk_type = chunk.get("type", "")
        metadata = chunk.get("metadata", {})
        description = metadata.get("description", "")
        keywords = metadata.get("keywords", [])

        if chunk_type in ["table_full", "table_row"]:
            # 表格类型：只使用描述+关键词
            embedding_parts = []
            if description:
                embedding_parts.append(description)
            if keywords:
                embedding_parts.append(", ".join(keywords))

            if not embedding_parts:
                # 如果没有描述和关键词，则使用原始内容
                content = chunk.get("content", "")
                embedding_parts.append(content)

            embedding_text = "\n".join(embedding_parts)
        else:
            # 文本类型：使用原始内容+描述+关键词
            content = chunk.get("content", "")
            embedding_parts = [content]

            if description:
                embedding_parts.append(description)

            if keywords:
                embedding_parts.append(", ".join(keywords))

            embedding_text = "\n".join(embedding_parts)

        return embedding_text

    def get_embedding_text_for_chunk(self, chunk: Dict[str, Any]) -> str:
        """
        获取分块的向量化文本（用于调试和验证）

        Args:
            chunk: 分块数据字典

        Returns:
            str: 向量化文本
        """
        return self._build_embedding_text(chunk)

    async def generate_question_embedding(self, question: str) -> Optional[List[float]]:
        """
        为问题文本生成向量嵌入

        Args:
            question: 问题文本

        Returns:
            List[float]: 向量嵌入，失败时返回None
        """
        try:
            if not question or not question.strip():
                logger.warning("问题文本为空，无法生成向量")
                return None

            # 直接调用智普API生成向量
            vector = await zhipu_embedding_async(
                text=question.strip(),
                api_key=EMBEDDING_CONFIG["api_key"],
                model=EMBEDDING_CONFIG["model"],
            )

            return vector

        except Exception as e:
            logger.error(f"生成问题向量嵌入失败: {str(e)}")
            return None

    async def generate_question_embeddings_batch(
        self, questions: List[str]
    ) -> List[Optional[List[float]]]:
        """
        批量为问题文本生成向量嵌入

        Args:
            questions: 问题文本列表

        Returns:
            List[Optional[List[float]]]: 向量嵌入列表，失败时为None
        """
        tasks = [self.generate_question_embedding(question) for question in questions]
        return await asyncio.gather(*tasks, return_exceptions=True)


# 便捷函数
async def generate_embedding_for_chunk(chunk: Dict[str, Any]) -> Optional[List[float]]:
    """
    为单个分块生成向量嵌入的便捷函数

    Args:
        chunk: 分块数据字典

    Returns:
        List[float]: 向量嵌入，失败时返回None
    """
    service = EmbeddingService()
    return await service.generate_embedding(chunk)


async def generate_embeddings_for_chunks(
    chunks: List[Dict[str, Any]],
) -> List[Optional[List[float]]]:
    """
    批量为分块生成向量嵌入的便捷函数

    Args:
        chunks: 分块数据列表

    Returns:
        List[Optional[List[float]]]: 向量嵌入列表，失败时为None
    """
    service = EmbeddingService()
    return await service.generate_embeddings_batch(chunks)


async def generate_embedding_for_question(question: str) -> Optional[List[float]]:
    """
    为单个问题生成向量嵌入的便捷函数

    Args:
        question: 问题文本

    Returns:
        List[float]: 向量嵌入，失败时返回None
    """
    service = EmbeddingService()
    return await service.generate_question_embedding(question)


async def generate_embeddings_for_questions(
    questions: List[str],
) -> List[Optional[List[float]]]:
    """
    批量为问题生成向量嵌入的便捷函数

    Args:
        questions: 问题文本列表

    Returns:
        List[Optional[List[float]]]: 向量嵌入列表，失败时为None
    """
    service = EmbeddingService()
    return await service.generate_question_embeddings_batch(questions)
