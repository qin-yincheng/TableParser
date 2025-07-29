import os
import yaml
from typing import Dict, Any, Optional
from utils.logger import logger


class ConfigManager:
    """配置管理器，用于读取和管理配置文件"""

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self._config = None

    def get_config(self) -> Dict[str, Any]:
        """
        获取配置信息

        Returns:
            Dict[str, Any]: 配置字典
        """
        if self._config is None:
            self._config = self._load_config()
        return self._config

    def _load_config(self) -> Dict[str, Any]:
        """
        加载配置文件

        Returns:
            Dict[str, Any]: 配置字典
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                    logger.info(f"成功加载配置文件: {self.config_path}")
                    return config or {}
            else:
                logger.warning(f"配置文件不存在: {self.config_path}，使用默认配置")
                return self._get_default_config()
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}，使用默认配置")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """
        获取默认配置

        Returns:
            Dict[str, Any]: 默认配置字典
        """
        return {
            "database": {
                "weaviate": {
                    "host": "localhost",
                    "port": 8089,
                    "grpc_host": "localhost",
                    "grpc_port": 50055,
                    "scheme": "http",
                    "api_key": None,
                    "timeout": [5, 30],
                }
            }
        }

    def get_weaviate_config(self) -> Dict[str, Any]:
        """
        获取Weaviate配置

        Returns:
            Dict[str, Any]: Weaviate配置字典
        """
        config = self.get_config()
        return config.get("database", {}).get("weaviate", {})

    def get_fragmentation_config(self) -> Dict[str, Any]:
        """
        获取分片配置

        Returns:
            Dict[str, Any]: 分片配置字典
        """
        config = self.get_config()
        return config.get("fragmentation", {})

    def reload_config(self) -> None:
        """重新加载配置文件"""
        self._config = None
        self.get_config()
