"""
分片配置模块，定义分片相关的配置参数
"""

from dataclasses import dataclass
from typing import Optional, List, Literal


@dataclass
class TableProcessingConfig:
    """表格处理配置类"""
    
    # 表格格式配置
    table_format: Literal["html", "markdown"] = "markdown"  # 表格输出格式
    
    # 表格分块策略配置
    table_chunking_strategy: Literal["full_only", "full_and_rows"] = "full_only"  # 分块策略
    
    # 是否启用表格处理
    enable_table_processing: bool = True
    
    def validate(self) -> bool:
        """验证表格配置的有效性"""
        return True  # 使用Literal类型已经保证了值的有效性
    
    def get_validation_errors(self) -> List[str]:
        """获取表格配置验证错误信息"""
        return []  # Literal类型已经保证了值的有效性


@dataclass
class FragmentConfig:
    """分片配置类"""
    
    # 基础分片参数
    enable_fragmentation: bool = True      # 是否启用分片
    max_chunk_size: int = 1000            # 最大chunk大小
    min_fragment_size: int = 200          # 最小分片大小
    chunk_overlap: int = 100              # 分片重叠大小
    
    # 上下文处理
    enable_context_rebuild: bool = True   # 是否重构上下文
    
    # 表格处理配置
    table_processing: TableProcessingConfig = None
    
    def __post_init__(self):
        """初始化后处理，确保表格配置存在"""
        if self.table_processing is None:
            self.table_processing = TableProcessingConfig()
    
    def validate(self) -> bool:
        """验证配置的有效性"""
        if self.max_chunk_size <= self.min_fragment_size:
            return False
        if self.chunk_overlap >= self.max_chunk_size:
            return False
        if self.chunk_overlap < 0:
            return False
        if self.max_chunk_size <= 0:
            return False
        if self.min_fragment_size <= 0:
            return False
        if not self.table_processing.validate():
            return False
        return True
    
    def get_validation_errors(self) -> List[str]:
        """获取配置验证错误信息"""
        errors = []
        if self.max_chunk_size <= self.min_fragment_size:
            errors.append(f"max_chunk_size ({self.max_chunk_size}) 必须大于 min_fragment_size ({self.min_fragment_size})")
        if self.chunk_overlap >= self.max_chunk_size:
            errors.append(f"chunk_overlap ({self.chunk_overlap}) 必须小于 max_chunk_size ({self.max_chunk_size})")
        if self.chunk_overlap < 0:
            errors.append(f"chunk_overlap 不能为负数")
        if self.max_chunk_size <= 0:
            errors.append(f"max_chunk_size 必须大于 0")
        if self.min_fragment_size <= 0:
            errors.append(f"min_fragment_size 必须大于 0")
        errors.extend(self.table_processing.get_validation_errors())
        return errors
    
    def get_chunker_config(self) -> dict:
        """获取分片器配置"""
        return {
            "chunk_size": self.max_chunk_size,
            "chunk_overlap": self.chunk_overlap
        } 