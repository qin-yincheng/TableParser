from typing import Any, Dict, List, Optional

import weaviate
from weaviate.auth import Auth, AuthApiKey

from utils.config_manager import ConfigManager
from utils.db_base import DBConnector
from utils.logger import logger


class WeaviateConnector(DBConnector):
    """Weaviate向量数据库连接器"""

    def __init__(self):
        self._client = None
        self._config_manager = ConfigManager()

    def __enter__(self):
        """上下文管理器入口"""
        if not self.is_connected():
            self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出，确保资源清理"""
        self.disconnect()

    def connect(self, **kwargs):
        """
        连接Weaviate数据库

        Args:
            **kwargs: 连接参数，包括host, port, scheme等
        """
        try:
            # 从配置文件获取默认值
            config = self._config_manager.get_config()
            weaviate_defaults = config.get("database", {}).get("weaviate", {})

            # 使用配置文件中的值作为默认值，如果没有则使用传入的参数，最后使用硬编码默认值
            http_host = kwargs.get(
                "http_host", weaviate_defaults.get("host", "localhost")
            )
            http_port = kwargs.get(
                "http_port", weaviate_defaults.get("port", 8089)
            )  # 修改为Docker映射端口
            grpc_host = kwargs.get(
                "grpc_host", weaviate_defaults.get("grpc_host", "localhost")
            )
            grpc_port = kwargs.get(
                "grpc_port", weaviate_defaults.get("grpc_port", 50055)
            )  # 修改为Docker映射端口
            scheme = kwargs.get("scheme", weaviate_defaults.get("scheme", "http"))
            api_key = kwargs.get("api_key", weaviate_defaults.get("api_key", None))
            timeout = kwargs.get("timeout", weaviate_defaults.get("timeout", (5, 30)))

            # 构建URL
            url = f"{scheme}://{http_host}:{http_port}"
            logger.debug(
                f"host: {http_host}, port: {http_port}, scheme: {scheme}, api_key: {api_key}, timeout: {timeout}"
            )

            # 初始化客户端 - 使用v4 API
            if api_key:
                auth = AuthApiKey(api_key)
                self._client = weaviate.connect_to_custom(
                    skip_init_checks=True,
                    http_host=http_host,
                    http_port=http_port,
                    http_secure=(scheme == "https"),  # 根据scheme决定是否使用HTTPS
                    grpc_host=grpc_host,
                    grpc_port=grpc_port,  # 使用相同的端口，通常gRPC端口可能不同
                    grpc_secure=(scheme == "https"),  # 根据scheme决定是否使用安全连接
                    auth_credentials=auth,
                )
            else:
                # 对于本地Docker部署，使用connect_to_local方法
                self._client = weaviate.connect_to_local(
                    host=http_host, port=http_port, grpc_port=grpc_port, headers={}
                )

            # 测试连接 - 使用更可靠的方法
            try:
                # 尝试获取元数据来验证连接
                meta = self._client.get_meta()
                logger.info(
                    f"Weaviate连接成功: {url}, 版本: {meta.get('version', 'unknown')}"
                )
            except Exception as e:
                logger.warning(f"is_ready()检查失败，尝试直接连接: {e}")
                # 如果is_ready()失败，尝试直接调用API
                try:
                    # 直接测试连接
                    response = self._client._connection.get("/v1/meta")
                    if response.status_code == 200:
                        logger.info(f"Weaviate连接成功: {url}")
                    else:
                        raise ConnectionError(
                            f"Weaviate服务响应异常: {response.status_code}"
                        )
                except Exception as api_error:
                    raise ConnectionError(f"Weaviate服务未就绪: {api_error}")

        except Exception as e:
            print(f"Weaviate连接失败: {e}")
            self._client = None
            raise

    def disconnect(self):
        """断开Weaviate连接"""
        if self._client:
            try:
                # 使用 Weaviate v4 客户端推荐的关闭方式
                # 优先使用上下文管理器的退出方法，这是最安全的方式
                if hasattr(self._client, '__exit__'):
                    self._client.__exit__(None, None, None)
                # 如果不支持上下文管理器，则使用 close() 方法
                elif hasattr(self._client, 'close'):
                    self._client.close()
                    
            except Exception as e:
                # 记录警告但不中断程序，因为连接可能已经关闭
                logger.warning(f"Weaviate连接关闭时出现警告: {e}")
            finally:
                self._client = None
            logger.info("Weaviate连接已关闭")

    def is_connected(self) -> bool:
        """检查Weaviate连接状态"""
        if self._client:
            return self._client.is_ready()
        return False

    def execute(self, query: str, params: Optional[Dict[str, Any]] = None):
        pass
