from typing import Any, Dict, List, Optional, Tuple, Union

from weaviate.classes.config import Configure, DataType, Property, Tokenization
import weaviate
from weaviate.collections.classes.filters import _Filters
from weaviate.classes.query import MetadataQuery

from connector import WeaviateConnector
from utils.logger import logger


class WeaviateOperations:
    """
    通用的Weaviate操作类，提供集合创建、查询、删除以及对象数据写入等功能。
    """

    def __init__(self, connector: Optional[WeaviateConnector] = None):
        """
        初始化Weaviate操作类

        Args:
            connector: 可选的Weaviate连接器实例，如果不提供则创建新实例
        """
        self.connector = connector or WeaviateConnector()
        if not self.connector.is_connected():
            self.connector.connect()

    def close(self):
        """关闭Weaviate连接"""
        if self.connector and self.connector.is_connected():
            self.connector.disconnect()

    def create_collection(
        self,
        name: str,
        description: str = "",
        properties: List[Dict[str, Any]] = None,
        vectorizer: str = "none",
    ) -> bool:
        """
        创建Weaviate集合

        Args:
            name: 集合名称
            description: 集合描述
            properties: 集合属性列表, 例如:
                [
                    {"name": "content", "dataType": "text", "description": "文本内容"},
                    {"name": "kb_id", "dataType": "int", "description": "知识库ID"}
                ]
            vectorizer: 向量化方法，默认为"none"表示手动提供向量

        Returns:
            bool: 创建成功返回True，否则返回False
        """
        try:
            # 确保连接
            if not self.connector.is_connected():
                self.connector.connect()

            client = self.connector._client

            # 检查集合是否已存在
            if self.collection_exists(name):
                logger.info(f"集合 '{name}' 已经存在")
                return True

            # 配置向量化器
            if vectorizer.lower() == "none":
                vectorizer_config = Configure.Vectorizer.none()
            else:
                # 这里可以根据需要扩展其他向量化器
                vectorizer_config = Configure.Vectorizer.none()

            # 转换属性格式
            weaviate_properties = []
            if properties:
                for prop in properties:
                    prop_name = prop["name"]
                    description = prop.get("description", "")
                    raw_type = prop.get("dataType", "text")

                    # 数据类型映射
                    if raw_type == "text":
                        data_type = DataType.TEXT
                        tokenization = Tokenization.GSE
                        module_config = {
                            "invertedIndexConfig": {
                                "stopwords": {
                                    "preset": "none"
                                }
                            }
                        }
                        weaviate_property = Property(
                            name=prop_name,
                            data_type=data_type,
                            description=description,
                            tokenization=tokenization,
                            module_config=module_config
                        )

                    elif raw_type == "int":
                        data_type = DataType.INT
                        weaviate_property = Property(
                            name=prop_name,
                            data_type=data_type,
                            description=description
                        )

                    elif raw_type == "number" or raw_type == "float":
                        data_type = DataType.NUMBER
                        weaviate_property = Property(
                            name=prop_name,
                            data_type=data_type,
                            description=description
                        )

                    elif raw_type == "bool":
                        data_type = DataType.BOOL
                        weaviate_property = Property(
                            name=prop_name,
                            data_type=data_type,
                            description=description
                        )

                    elif raw_type == "date":
                        data_type = DataType.DATE
                        weaviate_property = Property(
                            name=prop_name,
                            data_type=data_type,
                            description=description
                        )

                    elif raw_type == "uuid":
                        data_type = DataType.UUID
                        weaviate_property = Property(
                            name=prop_name,
                            data_type=data_type,
                            description=description
                        )

                    else:
                        # 默认使用TEXT类型
                        data_type = DataType.TEXT
                        weaviate_property = Property(
                            name=prop_name,
                            data_type=data_type,
                            description=description
                        )

                    weaviate_properties.append(weaviate_property)

            # 创建集合
            client.collections.create(
                name=name,
                description=description,
                vectorizer_config=vectorizer_config,
                properties=weaviate_properties,
            )

            logger.info(f"集合 '{name}' 创建成功")
            return True

        except Exception as e:
            logger.error(f"创建集合 '{name}' 失败: {e}")
            return False

    def _map_data_type(self, data_type: str) -> DataType:
        """
        将字符串类型映射到Weaviate数据类型

        Args:
            data_type: 数据类型字符串

        Returns:
            DataType: Weaviate数据类型
        """
        type_mapping = {
            "text": DataType.TEXT,
            "string": DataType.TEXT,
            "int": DataType.INT,
            "integer": DataType.INT,
            "number": DataType.NUMBER,
            "float": DataType.NUMBER,
            "bool": DataType.BOOL,
            "date": DataType.DATE,
            "uuid": DataType.UUID,
        }

        return type_mapping.get(data_type.lower(), DataType.TEXT)

    def delete_collection(self, name: str) -> bool:
        """
        删除Weaviate集合

        Args:
            name: 集合名称

        Returns:
            bool: 删除成功返回True，否则返回False
        """
        try:
            # 确保连接
            if not self.connector.is_connected():
                self.connector.connect()

            client = self.connector._client

            # 检查集合是否存在
            if not self.collection_exists(name):
                logger.info(f"集合 '{name}' 不存在")
                return False

            # 删除集合
            client.collections.delete(name)
            logger.info(f"集合 '{name}' 删除成功")
            return True

        except Exception as e:
            logger.error(f"删除集合 '{name}' 失败: {e}")
            return False

    def insert_data(
        self,
        collection_name: str,
        properties: Dict[str, Any],
        vector: Optional[List[float]] = None,
    ) -> Optional[str]:
        """
        向集合中插入数据

        Args:
            collection_name: 集合名称
            properties: 对象属性
            vector: 向量数据，如果为None则使用集合配置的向量化器

        Returns:
            str: 插入成功返回对象ID，否则返回None
        """
        try:
            # 确保连接
            if not self.connector.is_connected():
                self.connector.connect()

            client = self.connector._client

            # 获取集合
            collection = client.collections.get(collection_name)

            # 插入数据
            if vector is not None:
                result = collection.data.insert(
                    properties=properties,
                    vector=vector,
                )
            else:
                result = collection.data.insert(
                    properties=properties,
                )

            logger.debug(f"向集合 '{collection_name}' 插入数据成功, ID: {result} - {properties}")
            return result

        except Exception as e:
            logger.error(f"向集合 '{collection_name}' 插入数据失败: {e}")
            return None

    def batch_insert_data(
        self, collection_name: str, items: List[Dict[str, Any]]
    ) -> Tuple[int, int]:
        """
        批量插入数据到集合

        Args:
            collection_name: 集合名称
            items: 待插入的数据项列表，每项应包含properties和可选的vector与id
                  例如: [{"properties": {...}, "vector": [...]}, ...]

        Returns:
            Tuple[int, int]: (成功数量, 总数量)
        """
        try:
            # 确保连接
            if not self.connector.is_connected():
                self.connector.connect()

            client = self.connector._client

            # 获取集合
            collection = client.collections.get(collection_name)

            # 批量处理插入
            success_count = 0
            total_count = len(items)

            # 目前weaviate-client没有真正的批量插入API，只能循环处理
            # 如果将来weaviate-client提供了批量API，可以更新此处
            for item in items:
                try:
                    properties = item.get("properties", {})
                    vector = item.get("vector")

                    if vector is not None:
                        collection.data.insert(
                            properties=properties,
                            vector=vector,
                        )
                    else:
                        collection.data.insert(
                            properties=properties,
                        )

                    success_count += 1
                except Exception as e:
                    logger.error(f"批量插入项失败: {e}")
                    continue

            logger.info(f"批量插入完成: {success_count}/{total_count} 成功")
            return (success_count, total_count)

        except Exception as e:
            logger.error(f"批量插入到集合 '{collection_name}' 失败: {e}")
            return (0, len(items))

    def paginate_query(
        self,
        collection_name: str,
        limit: int = 100,
        after: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        分页遍历查询集合中的对象，返回向量和所有属性

        Args:
            collection_name: 集合名称
            limit: 每页返回的对象数量，默认100
            after: 上一页最后一个对象的ID，用于获取下一页数据

        Returns:
            Dict[str, Any]: 包含查询结果和分页信息的字典
                - objects: 对象列表，每个对象包含id、vector和properties
                - next_cursor: 下一页的游标ID，如果没有更多数据则为None
        """
        try:
            # 确保连接
            if not self.connector.is_connected():
                self.connector.connect()

            client = self.connector._client

            # 获取集合
            collection = client.collections.get(collection_name)

            # 先获取集合的属性信息，避免使用"*"通配符导致gRPC协议错误
            collection_config = collection.config.get()
            property_names = [prop.name for prop in collection_config.properties]

            # 执行分页查询
            query_result = collection.query.fetch_objects(
                limit=limit,
                after=after,
                include_vector=True,
                return_properties=property_names  # 使用具体的属性名列表替代"*"
            )

            if not query_result or not query_result.objects:
                return {
                    "objects": [],
                    "next_cursor": None
                }

            # 整理结果
            objects = []
            for obj in query_result.objects:
                result = {
                    "id": obj.uuid,
                    "vector": obj.vector,
                    "properties": obj.properties
                }
                objects.append(result)

            # 获取下一页游标
            next_cursor = query_result.objects[-1].uuid if len(query_result.objects) == limit else None

            return {
                "objects": objects,
                "next_cursor": next_cursor
            }

        except Exception as e:
            logger.error(f"分页查询集合 '{collection_name}' 失败: {e}")
            return {
                "objects": [],
                "next_cursor": None
            }

    def query_by_vector(
        self,
        collection_name: str,
        vector: List[float],
        limit: int = 10,
        properties: List[str] = None,
        distance_threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        通过向量查询最相似的对象

        Args:
            collection_name: 集合名称
            vector: 查询向量
            limit: 返回结果数量限制
            properties: 要返回的属性列表，为None时返回所有属性
            distance_threshold: 可选的距离阈值，超过此阈值的结果将被过滤

        Returns:
            List[Dict[str, Any]]: 查询结果列表
        """
        try:
            # 确保连接
            if not self.connector.is_connected():
                self.connector.connect()

            client = self.connector._client

            # 获取集合
            collection = client.collections.get(collection_name)

            # 执行向量查询
            query_result = collection.query.near_vector(
                near_vector=vector,
                limit=limit,
                return_metadata=["distance"],
                return_properties=properties,
            )

            if not query_result or not query_result.objects:
                return []

            # 整理结果
            results = []
            for obj in query_result.objects:
                distance = obj.metadata.distance

                # 应用距离阈值过滤
                if distance_threshold is not None and distance > distance_threshold:
                    continue

                # 构建结果对象
                result = {
                    "id": obj.uuid,
                    "score": distance,
                    "properties": obj.properties,
                }
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"向量查询集合 '{collection_name}' 失败: {e}")
            return []

    def query_by_hybrid(
        self,
        collection_name: str,
        query: str,
        query_vector: List[float],
        limit: int = 10,
        properties: List[str] = None,
        similarity_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        通过混合查询（文本和向量）获取最相关的对象

        Args:
            collection_name: 集合名称
            query: 查询文本
            query_vector: 查询向量
            limit: 返回结果数量限制
            properties: 要返回的属性列表，为None时返回所有属性
            similarity_threshold: 可选的相似度阈值，低于此阈值的结果将被过滤

        Returns:
            List[Dict[str, Any]]: 查询结果列表
        """
        try:
            # 确保连接
            if not self.connector.is_connected():
                self.connector.connect()

            client = self.connector._client

            # 获取集合
            collection = client.collections.get(collection_name)

            # 执行混合查询
            query_result = collection.query.hybrid(
                query=query,
                vector=query_vector,
                limit=limit,
                alpha=0.7,  # 混合比例，0.7表示文本和向量各占一定比例
                return_properties=properties,
                return_metadata=MetadataQuery(score=True),
            )

            if not query_result or not query_result.objects:
                return []

            # 整理结果
            results = []
            for obj in query_result.objects:
                similarity_score = obj.metadata.score
                if not similarity_score:
                    similarity_score = 0.0  # 如果没有相似度信息，默认设置为0.0

                # 应用相似度阈值过滤
                if similarity_threshold is not None and similarity_score < similarity_threshold:
                    continue

                # 构建结果对象
                result = {
                    "id": obj.uuid,
                    "score": similarity_score,
                    "properties": obj.properties
                }
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"混合查询集合 '{collection_name}' 失败: {e}")
            return []

    def query_by_filter(
        self,
        collection_name: str,
        filter_query: Union[Dict[str, Any], Optional[_Filters]],
        limit: int = 100,
        properties: List[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        通过过滤条件查询对象

        Args:
            collection_name: 集合名称
            filter_query: 过滤条件，例如：{"path": ["kb_id"], "operator": "Equal", "valueInt": 1}
            limit: 返回结果数量限制
            properties: 要返回的属性列表，为None时返回所有属性

        Returns:
            List[Dict[str, Any]]: 查询结果列表
        """
        try:
            # 确保连接
            if not self.connector.is_connected():
                self.connector.connect()

            client = self.connector._client

            # 获取集合
            collection = client.collections.get(collection_name)

            # 执行过滤查询
            query_result = collection.query.fetch_objects(
                filters=filter_query, limit=limit, return_properties=properties
            )

            if not query_result or not query_result.objects:
                return []

            # 整理结果
            results = []
            for obj in query_result.objects:
                result = {"id": obj.uuid, "properties": obj.properties}
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"过滤查询集合 '{collection_name}' 失败: {e}")
            return []

    def delete_by_filter(
        self, collection_name: str, filter_query: Union[Dict[str, Any], Optional[_Filters]]
    ) -> int:
        """
        通过过滤条件删除对象

        Args:
            collection_name: 集合名称
            filter_query: 过滤条件，例如：{"path": ["kb_id"], "operator": "Equal", "valueInt": 1}

        Returns:
            int: 删除的对象数量
        """
        try:
            # 确保连接
            if not self.connector.is_connected():
                self.connector.connect()

            client = self.connector._client

            # 获取集合
            collection = client.collections.get(collection_name)

            # 使用批量删除API
            result = collection.data.delete_many(
                # same where operator as in the GraphQL API
                where=filter_query,
                verbose=True
            )
            logger.info(f"从集合 '{collection_name}' 删除对象成功, 删除: {result}")
            return result

        except Exception as e:
            logger.error(f"从集合 '{collection_name}' 删除对象失败: {e}")
            return 0

    def get_collection_info(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """
        获取集合信息

        Args:
            collection_name: 集合名称

        Returns:
            Dict[str, Any]: 集合信息，包括名称、描述、属性等
        """
        try:
            # 确保连接
            if not self.connector.is_connected():
                self.connector.connect()

            client = self.connector._client

            # 获取集合
            collection = client.collections.get(collection_name)

            # 获取集合配置（包含属性信息）
            config = collection.config.get()

            # 提取属性信息
            properties = []
            for prop in config.properties:
                properties.append({
                    "name": prop.name,
                    "dataType": prop.data_type,
                    "description": prop.description
                })

            # 构建集合信息
            info = {
                "name": collection.name,
                "description": config.description,
                "vectorizer": config.vectorizer,
                "vector_index_type": config.vector_index_config,
                "properties": properties,
                "count": collection.aggregate.over_all()
            }

            return info

        except Exception as e:
            logger.error(f"获取集合 '{collection_name}' 信息失败: {e}")
            return None

    def list_collections(self) -> List[str]:
        """
        列出所有集合

        Returns:
            List[str]: 集合名称列表
        """
        try:
            # 确保连接
            if not self.connector.is_connected():
                self.connector.connect()

            client = self.connector._client

            # 获取所有集合名称
            collections = client.collections.list_all()
            return list(collections.keys())

        except Exception as e:
            logger.error(f"列出集合失败: {e}")
            return []

    def collection_exists(self, collection_name: str) -> bool:
        """
        检查集合是否存在

        Args:
            collection_name: 集合名称

        Returns:
            bool: 存在返回True，否则返回False
        """
        try:
            # 确保连接
            if not self.connector.is_connected():
                self.connector.connect()

            client = self.connector._client

            # 尝试获取集合
            try:
                return collection_name in client.collections.list_all()
            except Exception as e:
                logger.exception(f"无法获取集合: {e}")

        except Exception as e:
            logger.error(f"检查集合 '{collection_name}' 是否存在失败: {e}")
        return False

    def count_collection_objects(self, collection_name: str) -> int:
        """
        统计集合中对象的总数量

        Args:
            collection_name: 集合名称

        Returns:
            int: 集合中对象的总数量，失败时返回-1
        """
        try:
            # 确保连接
            if not self.connector.is_connected():
                self.connector.connect()

            client = self.connector._client

            # 获取集合
            collection = client.collections.get(collection_name)

            # 使用聚合功能获取总数
            aggregate_result = collection.aggregate.over_all()

            # 提取计数结果
            if aggregate_result and hasattr(aggregate_result, 'total_count') and aggregate_result.total_count is not None:
                count = aggregate_result.total_count
                logger.debug(f"集合 '{collection_name}' 包含 {count} 个对象")
                return count
            else:
                logger.debug(f"集合 '{collection_name}' 包含 0 个对象")
                return 0

        except Exception as e:
            logger.error(f"统计集合 '{collection_name}' 对象数量失败: {e}")
            return -1
