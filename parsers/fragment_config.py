"""
分片配置模块，定义分片相关的配置参数
"""

from dataclasses import dataclass
from typing import Optional, List


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
        return errors
    
    def get_chunker_config(self) -> dict:
        """获取分片器配置"""
        return {
            "chunk_size": self.max_chunk_size,
            "chunk_overlap": self.chunk_overlap
        } 