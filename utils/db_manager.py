from typing import Optional
from connector import WeaviateConnector
from utils.logger import logger


class DatabaseManager:
    """数据库管理器，用于管理不同类型的数据库连接"""

    def __init__(self):
        """初始化数据库管理器"""
        self._weaviate_connector = None

    def get_weaviate(self) -> WeaviateConnector:
        """
        获取Weaviate连接器

        Returns:
            WeaviateConnector: Weaviate连接器实例
        """
        if self._weaviate_connector is None:
            self._weaviate_connector = WeaviateConnector()
        return self._weaviate_connector

    def close_all(self) -> None:
        """关闭所有数据库连接"""
        try:
            if self._weaviate_connector and self._weaviate_connector.is_connected():
                self._weaviate_connector.disconnect()
                logger.info("Weaviate连接已关闭")
        except Exception as e:
            logger.error(f"关闭Weaviate连接失败: {e}")
        finally:
            self._weaviate_connector = None
