"""
上下文重构器，负责为分片chunk重构上下文信息
"""

from typing import List, Dict, Optional
from utils.logger import logger


class ContextRebuilder:
    """上下文重构器"""
    
    def __init__(self, config):
        self.config = config
    
    def rebuild_fragment_context(self, fragment_chunk: dict, all_chunks: List[dict], position_mapper) -> str:
        """为分片重构上下文"""
        metadata = fragment_chunk.get("metadata", {})
        original_para_idx = metadata.get("paragraph_index")
        
        if not original_para_idx:
            return fragment_chunk.get("context", "")
        
        # 获取原始段落上下文
        original_context = self._get_original_paragraph_context(original_para_idx, all_chunks)
        
        # 获取同段落内其他分片信息
        sibling_info = self._get_sibling_fragments_info(fragment_chunk, all_chunks, position_mapper)
        
        # 构建分片专用上下文
        fragment_context = f"段落分片 {metadata.get('fragment_index', 1)}/{metadata.get('total_fragments', 1)}"
        
        return f"{original_context} {fragment_context} {sibling_info}"
    
    def _get_original_paragraph_context(self, paragraph_index: int, all_chunks: List[dict]) -> str:
        """获取原始段落的上下文"""
        # 查找原始段落chunk
        original_chunk = None
        for chunk in all_chunks:
            if (chunk.get("metadata", {}).get("paragraph_index") == paragraph_index and 
                not chunk.get("metadata", {}).get("is_fragment")):
                original_chunk = chunk
                break
        
        if original_chunk:
            return original_chunk.get("context", "")
        
        return ""
    
    def _get_sibling_fragments_info(self, fragment_chunk: dict, all_chunks: List[dict], position_mapper) -> str:
        """获取同段落其他分片的信息"""
        metadata = fragment_chunk.get("metadata", {})
        para_idx = metadata.get("paragraph_index")
        current_fragment_index = metadata.get("fragment_index", 1)
        
        if not para_idx:
            return ""
        
        # 获取同段落的所有分片
        sibling_fragments = []
        for chunk in all_chunks:
            chunk_metadata = chunk.get("metadata", {})
            if (chunk_metadata.get("paragraph_index") == para_idx and 
                chunk_metadata.get("is_fragment") and
                chunk_metadata.get("fragment_index") != current_fragment_index):
                sibling_fragments.append(chunk)
        
        if not sibling_fragments:
            return ""
        
        # 构建分片信息
        fragment_info = []
        for sibling in sibling_fragments:
            sibling_metadata = sibling.get("metadata", {})
            fragment_info.append(f"分片{sibling_metadata.get('fragment_index')}: {sibling.get('content', '')[:50]}...")
        
        return f"同段落其他分片: {'; '.join(fragment_info)}"
    
    def update_table_context_for_fragments(self, table_chunks: List[dict], all_chunks: List[dict], position_mapper) -> None:
        """更新表格上下文以适配分片"""
        for table_chunk in table_chunks:
            preceding_idx = table_chunk.get("metadata", {}).get("preceding_paragraph_index")
            following_idx = table_chunk.get("metadata", {}).get("following_paragraph_index")
            
            # 查找分片后的相关段落
            preceding_fragments = self._find_paragraph_fragments(all_chunks, preceding_idx)
            following_fragments = self._find_paragraph_fragments(all_chunks, following_idx)
            
            # 更新表格上下文
            table_chunk["context"] = self._build_table_context_with_fragments(
                preceding_fragments, following_fragments
            )
    
    def _find_paragraph_fragments(self, all_chunks: List[dict], paragraph_index: Optional[int]) -> List[dict]:
        """查找指定段落的所有分片"""
        if not paragraph_index:
            return []
        
        fragments = []
        for chunk in all_chunks:
            chunk_metadata = chunk.get("metadata", {})
            if chunk_metadata.get("paragraph_index") == paragraph_index:
                fragments.append(chunk)
        
        return fragments
    
    def _build_table_context_with_fragments(self, preceding_fragments: List[dict], following_fragments: List[dict]) -> str:
        """构建包含分片的表格上下文"""
        preceding_content = ""
        following_content = ""
        
        if preceding_fragments:
            # 合并前置段落的所有分片内容
            preceding_contents = []
            for fragment in preceding_fragments:
                if fragment.get("metadata", {}).get("is_fragment"):
                    # 分片内容
                    fragment_info = f"[分片{fragment['metadata']['fragment_index']}] {fragment.get('content', '')}"
                    preceding_contents.append(fragment_info)
                else:
                    # 原始段落内容
                    preceding_contents.append(fragment.get("content", ""))
            preceding_content = " ".join(preceding_contents)
        
        if following_fragments:
            # 合并后置段落的所有分片内容
            following_contents = []
            for fragment in following_fragments:
                if fragment.get("metadata", {}).get("is_fragment"):
                    # 分片内容
                    fragment_info = f"[分片{fragment['metadata']['fragment_index']}] {fragment.get('content', '')}"
                    following_contents.append(fragment_info)
                else:
                    # 原始段落内容
                    following_contents.append(fragment.get("content", ""))
            following_content = " ".join(following_contents)
        
        return f"上一段：{preceding_content}。下一段：{following_content}" 