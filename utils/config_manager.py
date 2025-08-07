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
                    # 处理环境变量替换
                    config = self._resolve_env_variables(config or {})
                    return config
            else:
                logger.warning(f"配置文件不存在: {self.config_path}，使用默认配置")
                return self._get_default_config()
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}，使用默认配置")
            return self._get_default_config()

    def _resolve_env_variables(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        递归解析配置中的环境变量
        
        Args:
            config: 配置字典
            
        Returns:
            Dict[str, Any]: 解析后的配置字典
        """
        import re
        
        def resolve_value(value):
            if isinstance(value, str):
                # 匹配 ${VAR_NAME} 格式的环境变量
                pattern = r'\$\{([^}]+)\}'
                matches = re.findall(pattern, value)
                for var_name in matches:
                    env_value = os.getenv(var_name)
                    if env_value is not None:
                        value = value.replace(f'${{{var_name}}}', env_value)
                return value
            elif isinstance(value, dict):
                return {k: resolve_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [resolve_value(item) for item in value]
            else:
                return value
        
        return resolve_value(config)

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

    def get_image_processing_config(self) -> Dict[str, Any]:
        """
        获取图片处理配置
        
        Returns:
            Dict[str, Any]: 图片处理配置字典
        """
        from utils.config import VISION_CONFIG
        
        config = self.get_config()
        image_config = config.get("image_processing", {})
        
        # 从VISION_CONFIG中获取配置，与语言模型和向量模型采用相同的方式
        return {
            "enabled": image_config.get("enabled", True),
            "storage_path": image_config.get("storage_path", "storage/images"),
            "vision_model": VISION_CONFIG["model"],
            "api_key": VISION_CONFIG["api_key"],
            "context_window": VISION_CONFIG["context_window"],
            "max_concurrent": VISION_CONFIG["max_concurrent"],
            "timeout": VISION_CONFIG["timeout"],
            "retry_count": VISION_CONFIG["retry_count"],
            "cache_enabled": VISION_CONFIG["cache_enabled"],
            "cache_ttl": VISION_CONFIG["cache_ttl"]
        }

    def reload_config(self) -> None:
        """重新加载配置文件"""
        self._config = None
        self.get_config()


# 全局配置管理器实例
_config_manager = ConfigManager()


def get_config() -> Dict[str, Any]:
    """
    获取配置信息的便捷函数
    
    Returns:
        Dict[str, Any]: 配置字典
    """
    return _config_manager.get_config()


def get_image_processing_config() -> Dict[str, Any]:
    """
    获取图片处理配置的便捷函数
    
    Returns:
        Dict[str, Any]: 图片处理配置字典
    """
    return _config_manager.get_image_processing_config()
