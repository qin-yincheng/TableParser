"""
位置映射管理器，负责管理原始chunk和分片chunk之间的位置关系
"""

from typing import List, Dict, Optional
from utils.logger import logger


class PositionMapper:
    """位置映射管理器"""
    
    def __init__(self):
        self.original_positions: Dict[int, int] = {}    # 原始位置映射 {chunk_index: original_position}
        self.fragment_positions: Dict[int, List[int]] = {}    # 分片位置映射 {original_position: [fragment_positions]}
        self.paragraph_mapping: Dict[int, List[int]] = {}     # 段落映射关系 {paragraph_index: [chunk_positions]}
    
    def build_mapping(self, original_chunks: List[dict], fragmented_chunks: List[dict]) -> None:
        """构建位置映射关系"""
        self.original_positions.clear()
        self.fragment_positions.clear()
        self.paragraph_mapping.clear()
        
        # 构建原始位置映射
        for i, chunk in enumerate(original_chunks):
            self.original_positions[i] = i
        
        # 构建分片位置映射
        current_original_pos = 0
        fragment_positions = []
        
        for i, chunk in enumerate(fragmented_chunks):
            if chunk.get("metadata", {}).get("is_fragment"):
                # 这是一个分片
                original_pos = chunk["metadata"]["original_position"]
                if original_pos not in self.fragment_positions:
                    self.fragment_positions[original_pos] = []
                self.fragment_positions[original_pos].append(i)
            else:
                # 这是一个原始chunk
                self.original_positions[current_original_pos] = i
                current_original_pos += 1
        
        # 构建段落映射
        for i, chunk in enumerate(fragmented_chunks):
            para_idx = chunk.get("metadata", {}).get("paragraph_index")
            if para_idx:
                if para_idx not in self.paragraph_mapping:
                    self.paragraph_mapping[para_idx] = []
                self.paragraph_mapping[para_idx].append(i)
        
        logger.info(f"位置映射构建完成: 原始chunks={len(original_chunks)}, 分片chunks={len(fragmented_chunks)}")
    
    def get_original_position(self, fragment_chunk: dict) -> Optional[int]:
        """获取分片在原始列表中的位置"""
        return fragment_chunk.get("metadata", {}).get("original_position")
    
    def get_fragment_positions(self, original_position: int) -> List[int]:
        """获取原始位置对应的所有分片位置"""
        return self.fragment_positions.get(original_position, [])
    
    def get_paragraph_fragments(self, paragraph_index: int) -> List[int]:
        """获取指定段落的所有分片位置"""
        return self.paragraph_mapping.get(paragraph_index, [])
    
    def is_fragment(self, chunk: dict) -> bool:
        """判断是否为分片chunk"""
        return chunk.get("metadata", {}).get("is_fragment", False)
    
    def get_sibling_fragments(self, fragment_chunk: dict) -> List[int]:
        """获取同段落的其他分片位置"""
        metadata = fragment_chunk.get("metadata", {})
        para_idx = metadata.get("paragraph_index")
        current_pos = metadata.get("original_position")
        
        if not para_idx or current_pos is None:
            return []
        
        # 获取同段落的所有分片
        sibling_positions = []
        for pos in self.paragraph_mapping.get(para_idx, []):
            if pos != current_pos:
                sibling_positions.append(pos)
        
        return sibling_positions 