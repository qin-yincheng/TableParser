"""
问答服务模块，提供基于RAG的智能问答功能
"""

import asyncio
from typing import List, Dict, Optional, Union
from query_service import QueryService
from utils.zhipu_client import zhipu_complete_async
from utils.logger import logger


class QAService:
    """问答服务类，提供RAG问答功能"""

    def __init__(self):
        """初始化问答服务"""
        self.query_service = QueryService()
        self.max_context_length = 4000  # 上下文最大长度
        self.max_results = 8  # 最大检索结果数

    async def answer_question(
        self, question: str, kb_id: int
    ) -> Dict[str, Union[bool, str, List[Dict]]]:
        """
        回答用户问题

        Args:
            question: 用户问题
            kb_id: 知识库ID

        Returns:
            Dict: 问答结果
        """
        try:
            # 参数验证
            if not self._validate_question(question):
                return {"success": False, "error": "问题格式无效"}

            # 1. 语义检索
            retrieval_results = await self._semantic_retrieval(question, kb_id)
            if not retrieval_results:
                return {"success": False, "error": "未找到相关文档"}

            # 2. 答案融合
            merged_results = self._merge_results(retrieval_results)

            # 3. 构建答案上下文
            context = self._build_context(merged_results)

            # 4. 生成答案
            answer = await self._generate_answer(question, context)
            if not answer:
                return {"success": False, "error": "答案生成失败"}

            # 构建返回结果
            return self._build_response(question, answer, merged_results)

        except Exception as e:
            logger.error(f"问答服务失败: {str(e)}")
            return {"success": False, "error": f"问答失败: {str(e)}"}

    async def _semantic_retrieval(
        self, question: str, kb_id: int
    ) -> List[Dict[str, Union[str, float, Dict]]]:
        """
        语义检索

        Args:
            question: 用户问题
            kb_id: 知识库ID

        Returns:
            List[Dict]: 检索结果列表
        """
        try:
            result = await self.query_service.query_by_semantic(
                question=question, kb_id=kb_id, limit=self.max_results
            )

            if not result.get("success"):
                return []

            return result.get("results", [])

        except Exception as e:
            logger.error(f"语义检索失败: {str(e)}")
            return []

    def _merge_results(
        self, results: List[Dict[str, Union[str, float, Dict]]]
    ) -> List[Dict[str, Union[str, float, Dict]]]:
        """
        融合检索结果

        Args:
            results: 检索结果列表

        Returns:
            List[Dict]: 融合后的结果列表
        """
        try:
            # 去重
            unique_results = self._deduplicate_results(results)

            # 按相似度排序（距离越小越好）
            sorted_results = sorted(
                unique_results, key=lambda x: x.get("similarity_score", float("inf"))
            )

            return sorted_results[: self.max_results]

        except Exception as e:
            logger.error(f"结果融合失败: {str(e)}")
            return results

    def _build_context(self, results: List[Dict[str, Union[str, float, Dict]]]) -> str:
        """
        构建答案上下文

        Args:
            results: 检索结果列表

        Returns:
            str: 格式化的上下文
        """
        try:
            context_parts = []
            current_length = 0

            for result in results:
                content = result.get("content", "")
                content_length = len(content)

                if current_length + content_length > self.max_context_length:
                    break

                context_part = self._format_result(result)
                context_parts.append(context_part)
                current_length += content_length

            return "\n\n".join(context_parts)

        except Exception as e:
            logger.error(f"构建上下文失败: {str(e)}")
            return ""

    async def _generate_answer(self, question: str, context: str) -> Optional[str]:
        """
        生成答案

        Args:
            question: 用户问题
            context: 上下文内容

        Returns:
            str: 生成的答案
        """
        try:
            system_prompt = (
                "你是一个专业的文档问答助手，能够基于提供的文档内容准确回答用户问题。"
                "请遵循以下原则：\n"
                "1. 只基于提供的文档内容回答问题\n"
                "2. 如果文档中没有相关信息，请明确说明\n"
                "3. 保持答案的准确性和完整性\n"
                "4. 使用清晰、易懂的语言"
            )

            user_prompt = (
                f"用户问题：{question}\n\n"
                f"相关文档内容：\n{context}\n\n"
                "请基于上述文档内容回答用户问题。如果文档中没有相关信息，请说明无法找到相关信息。"
            )

            answer = await zhipu_complete_async(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=1000,
            )

            return answer.strip() if answer else None

        except Exception as e:
            logger.error(f"答案生成失败: {str(e)}")
            return None

    def _validate_question(self, question: str) -> bool:
        """
        验证问题格式

        Args:
            question: 用户问题

        Returns:
            bool: 验证结果
        """
        return bool(question and question.strip() and len(question.strip()) > 0)

    def _deduplicate_results(
        self, results: List[Dict[str, Union[str, float, Dict]]]
    ) -> List[Dict[str, Union[str, float, Dict]]]:
        """
        去重检索结果

        Args:
            results: 检索结果列表

        Returns:
            List[Dict]: 去重后的结果列表
        """
        seen_contents = set()
        unique_results = []

        for result in results:
            content = result.get("content", "")
            content_hash = hash(content[:100])  # 使用前100字符作为去重依据

            if content_hash not in seen_contents:
                seen_contents.add(content_hash)
                unique_results.append(result)

        return unique_results

    def _format_result(self, result: Dict[str, Union[str, float, Dict]]) -> str:
        """
        格式化单个检索结果

        Args:
            result: 检索结果

        Returns:
            str: 格式化后的结果
        """
        content = result.get("content", "")
        source_info = result.get("source_info", {})
        metadata = result.get("metadata", {})

        # 构建来源信息
        source_desc = f"[来源: {source_info.get('file_name', '未知文件')}"

        chunk_type = result.get("chunk_type", "text")
        if chunk_type == "table_full":
            source_desc += f", 表格: {source_info.get('table_title', '未知表格')}"
        elif chunk_type == "table_row":
            source_desc += f", 表格行: {source_info.get('row_index', '未知行')}"
        else:
            source_desc += f", 段落: {source_info.get('paragraph_index', '未知段落')}"

        source_desc += "]"

        # 构建描述信息
        description = metadata.get("description", "")
        keywords = metadata.get("keywords", [])

        description_part = ""
        if description:
            description_part += f"描述: {description}\n"

        if keywords:
            keywords_str = (
                ", ".join(keywords) if isinstance(keywords, list) else str(keywords)
            )
            description_part += f"关键词: {keywords_str}\n"

        # 拼接：来源 + 描述 + 原始内容
        result_parts = [source_desc]

        if description_part:
            result_parts.append(description_part.strip())

        result_parts.append(content)

        return "\n".join(result_parts)

    def _build_response(
        self,
        question: str,
        answer: str,
        results: List[Dict[str, Union[str, float, Dict]]],
    ) -> Dict[str, Union[bool, str, List[Dict]]]:
        """
        构建返回结果

        Args:
            question: 用户问题
            answer: 生成的答案
            results: 检索结果列表

        Returns:
            Dict: 返回结果
        """
        return {
            "success": True,
            "question": question,
            "answer": answer,
            "sources": [
                {
                    "content": (
                        result.get("content", "")[:200] + "..."
                        if len(result.get("content", "")) > 200
                        else result.get("content", "")
                    ),
                    "chunk_type": result.get("chunk_type", "text"),
                    "similarity_score": result.get("similarity_score", 0.0),
                    "source_info": result.get("source_info", {}),
                }
                for result in results[:3]  # 只返回前3个来源
            ],
            "metadata": {"total_sources": len(results)},
        }

    def close(self):
        """关闭服务，释放资源"""
        if hasattr(self, "query_service"):
            self.query_service.close()
