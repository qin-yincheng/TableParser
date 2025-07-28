from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class DBConnector(ABC):
    """数据库连接器基类"""

    @abstractmethod
    def connect(self, **kwargs) -> None:
        """连接数据库"""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """断开数据库连接"""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """检查连接状态"""
        pass

    @abstractmethod
    def execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """执行查询"""
        pass
