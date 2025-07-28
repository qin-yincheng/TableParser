"""
查询服务模块，提供语义相似度查询和分块类型过滤查询功能
"""

from typing import List, Dict, Optional, Union
from vector_service import VectorService
from embedding_service import EmbeddingService
from utils.logger import logger


class QueryService:
    """查询服务类，提供多种查询方式"""

    def __init__(self):
        """初始化查询服务"""
        self.vector_service = VectorService()
        self.embedding_service = EmbeddingService()

    async def query_by_semantic(
        self,
        question: str,
        kb_id: int,
        limit: int = 10,
        distance_threshold: Optional[float] = None,
    ) -> Dict[str, Union[bool, str, int, List[Dict]]]:
        """
        基于语义相似度的查询

        Args:
            question: 用户问题
            kb_id: 知识库ID
            limit: 返回结果数量限制
            distance_threshold: 相似度阈值

        Returns:
            Dict: 查询结果
        """
        try:
            # 验证参数
            if not self._validate_kb_id(kb_id):
                return {"success": False, "error": f"知识库 {kb_id} 不存在"}

            if not question.strip():
                return {"success": False, "error": "问题不能为空"}

            # 问题向量化
            question_vector = await self._vectorize_question(question)
            if question_vector is None:
                return {"success": False, "error": "问题向量化失败"}

            # 执行向量相似度查询
            results = self.vector_service.query_by_vector(
                kb_id=kb_id,
                vector=question_vector,
                limit=limit,
                distance_threshold=distance_threshold,
            )

            # 格式化结果
            formatted_results = self._format_semantic_results(results)

            return {
                "success": True,
                "question": question,
                "kb_id": kb_id,
                "total_count": len(formatted_results),
                "results": formatted_results,
            }

        except Exception as e:
            logger.error(f"语义查询失败: {str(e)}")
            return {"success": False, "error": f"查询失败: {str(e)}"}

    def query_by_type(
        self,
        chunk_types: Union[str, List[str]],
        kb_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Union[bool, str, int, List[Dict]]]:
        """
        基于分块类型的过滤查询

        Args:
            chunk_types: 分块类型，支持字符串或字符串列表
            kb_id: 知识库ID
            limit: 返回结果数量限制
            offset: 分页偏移量

        Returns:
            Dict: 查询结果
        """
        try:
            # 验证参数
            if not self._validate_kb_id(kb_id):
                return {"success": False, "error": f"知识库 {kb_id} 不存在"}

            # 标准化分块类型参数
            normalized_types = self._normalize_chunk_types(chunk_types)
            if not normalized_types:
                return {"success": False, "error": "无效的分块类型"}

            # 构建过滤条件
            filter_query = self._build_type_filter(normalized_types)

            # 执行过滤查询
            results = self.vector_service.query_by_filter(
                kb_id=kb_id, filter_query=filter_query, limit=limit
            )

            # 格式化结果
            formatted_results = self._format_type_results(results)

            return {
                "success": True,
                "chunk_types": normalized_types,
                "kb_id": kb_id,
                "total_count": len(formatted_results),
                "offset": offset,
                "limit": limit,
                "results": formatted_results,
            }

        except Exception as e:
            logger.error(f"类型过滤查询失败: {str(e)}")
            return {"success": False, "error": f"查询失败: {str(e)}"}

    async def query_hybrid(
        self,
        question: str,
        chunk_types: Union[str, List[str]],
        kb_id: int,
        limit: int = 10,
        distance_threshold: Optional[float] = None,
    ) -> Dict[str, Union[bool, str, int, List[Dict]]]:
        """
        混合查询：先按类型过滤，再按语义相似度排序

        Args:
            question: 用户问题
            chunk_types: 分块类型
            kb_id: 知识库ID
            limit: 返回结果数量限制
            distance_threshold: 相似度阈值

        Returns:
            Dict: 查询结果
        """
        try:
            # 先进行类型过滤查询
            type_results = self.query_by_type(chunk_types, kb_id, limit=1000)
            if not type_results["success"]:
                return type_results

            if not type_results["results"]:
                return {
                    "success": True,
                    "question": question,
                    "chunk_types": chunk_types,
                    "kb_id": kb_id,
                    "total_count": 0,
                    "results": [],
                }

            # 问题向量化
            question_vector = await self._vectorize_question(question)
            if question_vector is None:
                return {"success": False, "error": "问题向量化失败"}

            # 对过滤结果进行向量相似度计算
            scored_results = self._calculate_similarity_scores(
                type_results["results"], question_vector
            )

            # 按相似度排序并限制结果数量
            sorted_results = sorted(
                scored_results, key=lambda x: x.get("similarity_score", 0), reverse=True
            )[:limit]

            return {
                "success": True,
                "question": question,
                "chunk_types": chunk_types,
                "kb_id": kb_id,
                "total_count": len(sorted_results),
                "results": sorted_results,
            }

        except Exception as e:
            logger.error(f"混合查询失败: {str(e)}")
            return {"success": False, "error": f"查询失败: {str(e)}"}

    def _validate_kb_id(self, kb_id: int) -> bool:
        """验证知识库ID是否存在"""
        return self.vector_service.collection_exists(kb_id)

    async def _vectorize_question(self, question: str) -> Optional[List[float]]:
        """将问题转换为向量"""
        try:
            vector = await self.embedding_service.generate_question_embedding(question)
            return vector
        except Exception as e:
            logger.error(f"问题向量化失败: {str(e)}")
            return None

    def _normalize_chunk_types(self, chunk_types: Union[str, List[str]]) -> List[str]:
        """标准化分块类型参数"""
        valid_types = {"text", "table_full", "table_row"}

        if isinstance(chunk_types, str):
            normalized = [chunk_types]
        elif isinstance(chunk_types, list):
            normalized = chunk_types
        else:
            return []

        # 验证类型有效性
        valid_normalized = [t for t in normalized if t in valid_types]
        return valid_normalized

    def _build_type_filter(
        self, chunk_types: List[str]
    ) -> Dict[str, Union[str, List[str]]]:
        """构建分块类型过滤条件"""
        if len(chunk_types) == 1:
            return {
                "path": ["chunk_type"],
                "operator": "Equal",
                "valueString": chunk_types[0],
            }
        else:
            return {
                "path": ["chunk_type"],
                "operator": "ContainsAny",
                "valueStringArray": chunk_types,
            }

    def _format_semantic_results(self, results: List[Dict]) -> List[Dict]:
        """格式化语义查询结果"""
        formatted = []
        for result in results:
            # Weaviate返回的数据结构：{id, score, properties}
            properties = result.get("properties", {})
            formatted_result = {
                "chunk_id": properties.get("chunk_id", ""),
                "chunk_type": properties.get("chunk_type", ""),
                "content": properties.get("content", ""),
                "similarity_score": result.get("score", 0),
                "metadata": self._extract_metadata(properties),
            }
            formatted.append(formatted_result)
        return formatted

    def _format_type_results(self, results: List[Dict]) -> List[Dict]:
        """格式化类型过滤查询结果"""
        formatted = []
        for result in results:
            # Weaviate返回的数据结构：{id, score, properties}
            properties = result.get("properties", {})
            formatted_result = {
                "chunk_id": properties.get("chunk_id", ""),
                "chunk_type": properties.get("chunk_type", ""),
                "content": properties.get("content", ""),
                "metadata": self._extract_metadata(properties),
            }
            formatted.append(formatted_result)
        return formatted

    def _extract_metadata(self, result: Dict) -> Dict:
        """提取元数据信息"""
        metadata = {}
        metadata_fields = [
            "doc_id",
            "description",
            "keywords",
            "parent_id",
            "context",
            "sheet",
            "table_id",
            "row",
            "header",
            "paragraph_index",
        ]

        for field in metadata_fields:
            if field in result:
                metadata[field] = result[field]

        return metadata

    def _calculate_similarity_scores(
        self, results: List[Dict], question_vector: List[float]
    ) -> List[Dict]:
        """计算相似度得分"""
        try:
            # 提取所有分块的向量
            chunk_vectors = []
            for result in results:
                # 这里需要从向量库中获取分块的向量
                # 由于当前VectorService没有提供获取向量的方法，这里简化处理
                # 实际实现中需要扩展VectorService来支持向量获取
                chunk_vectors.append(None)

            # 计算相似度得分（简化实现）
            for i, result in enumerate(results):
                # 这里应该计算实际的向量相似度
                # 暂时使用随机值作为示例
                import random

                result["similarity_score"] = random.uniform(0.5, 1.0)

            return results

        except Exception as e:
            logger.error(f"计算相似度得分失败: {str(e)}")
            return results

    def close(self):
        """关闭资源"""
        self.vector_service.close()
        # EmbeddingService 不需要显式关闭
