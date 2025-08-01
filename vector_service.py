from typing import Any, Dict, List, Optional, Tuple

from utils.db_manager import DatabaseManager
from operations import WeaviateOperations
from embedding_service import EmbeddingService


class VectorService:
    """向量服务类，封装向量库相关操作"""

    def __init__(self):
        """初始化向量服务"""
        self.weaviate_ops = WeaviateOperations(DatabaseManager().get_weaviate())
        self.embedding_service = EmbeddingService()

    @staticmethod
    def _assemble_collection_name(kb_id: int) -> str:
        """
        组装collection名称

        Args:
            kb_id: 知识库ID

        Returns:
            str: collection名称
        """
        return f"Kb_{kb_id}"

    @staticmethod
    def _convert_array_to_string(arr: List[str]) -> str:
        """
        将字符串数组转换为逗号分隔的字符串

        Args:
            arr: 字符串数组

        Returns:
            str: 逗号分隔的字符串
        """
        return ", ".join(arr) if arr else ""

    @staticmethod
    def _convert_string_to_array(s: str) -> List[str]:
        """
        将逗号分隔的字符串转换为数组

        Args:
            s: 逗号分隔的字符串

        Returns:
            List[str]: 字符串数组
        """
        return [item.strip() for item in s.split(",")] if s else []

    def create_collection(self, kb_id: int) -> bool:
        """
        创建向量库集合

        Args:
            kb_id: 知识库ID

        Returns:
            bool: 创建成功返回True，否则返回False
        """
        collection_name = self._assemble_collection_name(kb_id)

        # 定义集合属性 - 更新为支持多粒度分块和父子关系
        properties = [
            {"name": "doc_id", "dataType": "text", "description": "文档ID"},
            {"name": "chunk_id", "dataType": "text", "description": "分块ID"},
            {
                "name": "chunk_type",
                "dataType": "text",
                "description": "分块类型：text/table_full/table_row",
            },
            {"name": "content", "dataType": "text", "description": "分块内容"},
            {"name": "description", "dataType": "text", "description": "LLM生成的描述"},
            {"name": "keywords", "dataType": "text", "description": "关键词列表（逗号分隔）"},
            {"name": "parent_id", "dataType": "text", "description": "父分块ID"},
            {"name": "context", "dataType": "text", "description": "上下文内容"},
            # 表格特有字段
            {"name": "sheet", "dataType": "text", "description": "Excel工作表名"},
            {"name": "table_id", "dataType": "text", "description": "表格ID"},
            {"name": "row", "dataType": "int", "description": "行号"},
            {"name": "header", "dataType": "text", "description": "表头（逗号分隔）"},
            {"name": "paragraph_index", "dataType": "int", "description": "段落索引"},
        ]

        return self.weaviate_ops.create_collection(
            name=collection_name,
            description="知识库集合",
            properties=properties,
            vectorizer="none",
        )

    def delete_collection(self, kb_id: int) -> bool:
        """
        删除向量库集合

        Args:
            kb_id: 知识库ID

        Returns:
            bool: 删除成功返回True，否则返回False
        """
        collection_name = self._assemble_collection_name(kb_id)
        return self.weaviate_ops.delete_collection(collection_name)

    def insert_data(
        self, vector: List[float], kb_id: int, chunk: Dict[str, Any]
    ) -> Optional[str]:
        """
        向集合中插入分块数据

        Args:
            vector: 向量
            kb_id: 知识库ID
            chunk: 分块数据字典，包含所有必要字段

        Returns:
            str: 插入成功返回对象ID，否则返回None
        """
        collection_name = self._assemble_collection_name(kb_id)

        if not self.weaviate_ops.collection_exists(collection_name):
            raise ValueError(f"Collection {collection_name} does not exist")

        # 从chunk中提取数据
        metadata = chunk.get("metadata", {})

        # 组装数据对象 - 将数组转换为字符串
        data_obj = {
            "doc_id": chunk.get("doc_id", metadata.get("doc_id", "")),
            "chunk_id": chunk.get("chunk_id", ""),
            "chunk_type": chunk.get("type", ""),
            "content": chunk.get("content", ""),
            "description": metadata.get("description", ""),
            "keywords": self._convert_array_to_string(metadata.get("keywords", [])),
            "parent_id": chunk.get("parent_id", ""),
            "context": chunk.get("context", ""),
            # 表格特有字段
            "sheet": metadata.get("sheet", ""),
            "table_id": metadata.get("table_id", ""),
            "row": metadata.get("row", 0),
            "header": self._convert_array_to_string(metadata.get("header", [])),
            "paragraph_index": metadata.get("paragraph_index", 0),
        }

        return self.weaviate_ops.insert_data(collection_name, data_obj, vector)

    # def batch_insert_data(self, kb_id: int, items: List[Dict[str, Any]]) -> Tuple[int, int]:
    #     """
    #     批量插入数据到集合
    #
    #     Args:
    #         kb_id: 知识库ID
    #         items: 待插入的数据项列表
    #
    #     Returns:
    #         Tuple[int, int]: (成功数量, 总数量)
    #     """
    #     if kb_id == 0:
    #         raise ValueError("Invalid kb_id")
    #
    #     collection_name = self._assemble_collection_name(kb_id)
    #
    #     # 转换数据项格式
    #     processed_items = []
    #     for item in items:
    #         processed_item = {
    #             "properties": {
    #                 "doc_id": item.get("doc_id", 0),
    #                 "chunk_id": item.get("chunk_id", 0),
    #                 "question": item.get("question", ""),
    #                 "answer": item.get("answer", ""),
    #                 "summary": item.get("summary", ""),
    #             }
    #         }
    #
    #         # 如果有向量，添加向量
    #         if "vector" in item:
    #             processed_item["vector"] = item["vector"]
    #
    #         processed_items.append(processed_item)
    #
    #     return self.weaviate_ops.batch_insert_data(collection_name, processed_items)

    def query_by_vector(
        self,
        kb_id: int,
        vector: List[float],
        limit: int = 10,
        distance_threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        通过向量查询最相似的对象

        Args:
            kb_id: 知识库ID
            vector: 查询向量
            limit: 返回结果数量限制
            distance_threshold: 可选的距离阈值，超过此阈值的结果将被过滤

        Returns:
            List[Dict[str, Any]]: 查询结果列表
        """
        collection_name = self._assemble_collection_name(kb_id)
        if not self.weaviate_ops.collection_exists(collection_name):
            raise ValueError(f"Collection {collection_name} does not exist")

        results = self.weaviate_ops.query_by_vector(
            collection_name=collection_name,
            vector=vector,
            limit=limit,
            distance_threshold=distance_threshold,
            properties=[
                "doc_id",
                "chunk_id",
                "chunk_type",
                "content",
                "description",
                "keywords",
                "parent_id",
                "context",
                "sheet",
                "table_id",
                "row",
                "header",
                "paragraph_index",
            ],
        )

        # 将字符串转换回数组格式
        for result in results:
            if "properties" in result:
                properties = result["properties"]
                if "keywords" in properties:
                    properties["keywords"] = self._convert_string_to_array(properties["keywords"])
                if "header" in properties:
                    properties["header"] = self._convert_string_to_array(properties["header"])

        return results

    def query_by_filter(
        self, kb_id: int, filter_query: Dict[str, Any], limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        通过过滤条件查询对象

        Args:
            kb_id: 知识库ID
            filter_query: 过滤条件
            limit: 返回结果数量限制

        Returns:
            List[Dict[str, Any]]: 查询结果列表
        """

        collection_name = self._assemble_collection_name(kb_id)
        if not self.weaviate_ops.collection_exists(collection_name):
            raise ValueError(f"Collection {collection_name} does not exist")

        results = self.weaviate_ops.query_by_filter(
            collection_name=collection_name,
            filter_query=filter_query,
            limit=limit,
            properties=[
                "doc_id",
                "chunk_id",
                "chunk_type",
                "content",
                "description",
                "keywords",
                "parent_id",
                "context",
                "sheet",
                "table_id",
                "row",
                "header",
                "paragraph_index",
            ],
        )

        # 将字符串转换回数组格式
        for result in results:
            if "properties" in result:
                properties = result["properties"]
                if "keywords" in properties:
                    properties["keywords"] = self._convert_string_to_array(properties["keywords"])
                if "header" in properties:
                    properties["header"] = self._convert_string_to_array(properties["header"])

        return results

    def delete_by_filter(self, kb_id: int, filter_query: Dict[str, Any]) -> int:
        """
        通过过滤条件删除对象

        Args:
            kb_id: 知识库ID
            filter_query: 过滤条件

        Returns:
            int: 删除的对象数量
        """
        collection_name = self._assemble_collection_name(kb_id)
        return self.weaviate_ops.delete_by_filter(collection_name, filter_query)

    def get_collection_info(self, kb_id: int) -> Optional[Dict[str, Any]]:
        """
        获取集合信息

        Args:
            kb_id: 知识库ID

        Returns:
            Dict[str, Any]: 集合信息
        """
        collection_name = self._assemble_collection_name(kb_id)
        return self.weaviate_ops.get_collection_info(collection_name)

    def collection_exists(self, kb_id: int) -> bool:
        """
        检查集合是否存在

        Args:
            kb_id: 知识库ID

        Returns:
            bool: 存在返回True，否则返回False
        """
        collection_name = self._assemble_collection_name(kb_id)
        return self.weaviate_ops.collection_exists(collection_name)

    def close(self):
        """关闭Weaviate连接"""
        self.weaviate_ops.close()

    async def query_by_hybrid(
        self,
        kb_id: int,
        question: str,
        limit: int = 10,
        similarity_threshold: Optional[float] = None,
        alpha: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """
        通过混合查询（文本和向量）获取最相关的对象
        
        Args:
            kb_id: 知识库ID
            question: 问题文本
            limit: 返回结果数量限制
            similarity_threshold: 可选的相似度阈值，低于此阈值的结果将被过滤
            alpha: 混合比例，0.7表示文本和向量各占一定比例
            
        Returns:
            List[Dict[str, Any]]: 查询结果列表
        """
        collection_name = self._assemble_collection_name(kb_id)
        if not self.weaviate_ops.collection_exists(collection_name):
            raise ValueError(f"Collection {collection_name} does not exist")

        # 生成问题向量 - 使用await而不是run_until_complete
        try:
            vector = await self.embedding_service.generate_question_embedding(question)
        except Exception as e:
            from utils.logger import logger
            logger.error(f"生成问题向量失败: {e}")
            return []

        if not vector:
            from utils.logger import logger
            logger.error("无法生成问题向量")
            return []

        # 调用operations的混合查询方法
        results = self.weaviate_ops.query_by_hybrid(
            collection_name=collection_name,
            query=question,
            query_vector=vector,
            limit=limit,
            similarity_threshold=similarity_threshold,
            properties=[
                "doc_id",
                "chunk_id", 
                "chunk_type",
                "content",
                "description",
                "keywords",
                "parent_id",
                "context",
                "sheet",
                "table_id",
                "row",
                "header",
                "paragraph_index",
            ],
        )

        # 将字符串转换回数组格式
        for result in results:
            if "properties" in result:
                properties = result["properties"]
                if "keywords" in properties:
                    properties["keywords"] = self._convert_string_to_array(properties["keywords"])
                if "header" in properties:
                    properties["header"] = self._convert_string_to_array(properties["header"])

        return results


class VectorGraphService:
    """向量服务类，封装向量库相关操作"""

    def __init__(self):
        """初始化向量服务"""
        self.weaviate_ops = WeaviateOperations(DatabaseManager().get_weaviate())

    @staticmethod
    def _assemble_collection_name(kb_id: int) -> str:
        """
        组装collection名称

        Args:
            kb_id: 知识库ID

        Returns:
            str: collection名称
        """
        return f"Graph_{kb_id}"

    def create_collection(self, kb_id: int) -> bool:
        """
        创建向量库集合

        Args:
            kb_id: 知识库ID

        Returns:
            bool: 创建成功返回True，否则返回False
        """
        collection_name = self._assemble_collection_name(kb_id)

        # 定义集合属性
        properties = [
            {"name": "kb_id", "dataType": "int", "description": "知识库ID"},
            {"name": "doc_id", "dataType": "int", "description": "文档ID"},
            {"name": "chunk_id", "dataType": "int", "description": "分块ID"},
            {"name": "relaton", "dataType": "text", "description": "关系"},
            {"name": "sources", "dataType": "text_array", "description": "来源"},
        ]

        return self.weaviate_ops.create_collection(
            name=collection_name,
            description="知识库关系集合",
            properties=properties,
            vectorizer="none",
        )

    def delete_collection(self, kb_id: int) -> bool:
        """
        删除向量库集合

        Args:
            kb_id: 知识库ID

        Returns:
            bool: 删除成功返回True，否则返回False
        """
        collection_name = self._assemble_collection_name(kb_id)
        return self.weaviate_ops.delete_collection(collection_name)

    def insert_data(
        self,
        vector: List[float],
        kb_id: int,
        doc_id: int,
        chunk_id: int,
        question: str = "",
        answer: str = "",
        summary: str = "",
        sources: List[str] = [],
    ) -> Optional[str]:
        """
        向集合中插入数据

        Args:
            vector: 向量
            kb_id: 知识库ID
            doc_id: 文档ID
            chunk_id: 分块ID
            question: 问题
            answer: 答案
            summary: 摘要
            sources: 来源

        Returns:
            str: 插入成功返回对象ID，否则返回None
        """
        collection_name = self._assemble_collection_name(kb_id)

        # 组装数据对象
        data_obj = {
            "kb_id": kb_id,
            "doc_id": doc_id,
            "chunk_id": chunk_id,
            "question": question,
            "answer": answer,
            "summary": summary,
            "sources": sources,
        }

        return self.weaviate_ops.insert_data(collection_name, data_obj, vector)

    def batch_insert_data(
        self, kb_id: int, items: List[Dict[str, Any]]
    ) -> Tuple[int, int]:
        """
        批量插入数据到集合

        Args:
            kb_id: 知识库ID
            items: 待插入的数据项列表，每项应包含content字段

        Returns:
            Tuple[int, int]: (成功数量, 总数量)
        """
        collection_name = self._assemble_collection_name(kb_id)

        # 转换数据项格式
        processed_items = []
        for item in items:
            processed_item = {
                "properties": {
                    "content": item.get("content", ""),
                    "kb_id": kb_id,
                    "doc_id": item.get("doc_id", 0),
                    "chunk_id": item.get("chunk_id", 0),
                    "question": item.get("question", ""),
                    "answer": item.get("answer", ""),
                    "summary": item.get("summary", ""),
                    "sources": item.get("sources", []),
                }
            }

            # 如果有向量，添加向量
            if "vector" in item:
                processed_item["vector"] = item["vector"]

            processed_items.append(processed_item)

        return self.weaviate_ops.batch_insert_data(collection_name, processed_items)

    def query_by_vector(
        self,
        kb_id: int,
        vector: List[float],
        limit: int = 10,
        distance_threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        通过向量查询最相似的对象

        Args:
            kb_id: 知识库ID
            vector: 查询向量
            limit: 返回结果数量限制
            distance_threshold: 可选的距离阈值，超过此阈值的结果将被过滤

        Returns:
            List[Dict[str, Any]]: 查询结果列表
        """
        collection_name = self._assemble_collection_name(kb_id)
        return self.weaviate_ops.query_by_vector(
            collection_name=collection_name,
            vector=vector,
            limit=limit,
            distance_threshold=distance_threshold,
            properties=["content", "kb_id", "doc_id", "chunk_id"],
        )

    def query_by_filter(
        self, kb_id: int, filter_query: Dict[str, Any], limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        通过过滤条件查询对象

        Args:
            kb_id: 知识库ID
            filter_query: 过滤条件
            limit: 返回结果数量限制

        Returns:
            List[Dict[str, Any]]: 查询结果列表
        """
        collection_name = self._assemble_collection_name(kb_id)
        return self.weaviate_ops.query_by_filter(
            collection_name=collection_name,
            filter_query=filter_query,
            limit=limit,
            properties=["content", "kb_id", "doc_id", "chunk_id"],
        )

    def delete_by_filter(self, kb_id: int, filter_query: Dict[str, Any]) -> int:
        """
        通过过滤条件删除对象

        Args:
            kb_id: 知识库ID
            filter_query: 过滤条件

        Returns:
            int: 删除的对象数量
        """
        collection_name = self._assemble_collection_name(kb_id)
        return self.weaviate_ops.delete_by_filter(collection_name, filter_query)

    def get_collection_info(self, kb_id: int) -> Optional[Dict[str, Any]]:
        """
        获取集合信息

        Args:
            kb_id: 知识库ID

        Returns:
            Dict[str, Any]: 集合信息
        """
        collection_name = self._assemble_collection_name(kb_id)
        return self.weaviate_ops.get_collection_info(collection_name)

    def collection_exists(self, kb_id: int) -> bool:
        """
        检查集合是否存在

        Args:
            kb_id: 知识库ID

        Returns:
            bool: 存在返回True，否则返回False
        """
        collection_name = self._assemble_collection_name(kb_id)
        return self.weaviate_ops.collection_exists(collection_name)

    def close(self):
        """关闭Weaviate连接"""
        self.weaviate_ops.close()
