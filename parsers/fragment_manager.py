"""
分片管理器，负责协调分片配置、位置映射和上下文重构
"""

from typing import List, Dict, Optional
from utils.logger import logger

from .fragment_config import FragmentConfig
from .position_mapper import PositionMapper
from .context_rebuilder import ContextRebuilder
from .chunker import Chunker


class FragmentManager:
    """分片管理器，负责智能分片和位置管理"""
    
    def __init__(self, config: Optional[FragmentConfig] = None):
        self.config = config or FragmentConfig()
        self.chunker = Chunker(**self.config.get_chunker_config())
        self.position_mapper = PositionMapper()
        self.context_rebuilder = ContextRebuilder(self.config)
        
        # 验证配置
        if not self.config.validate():
            errors = self.config.get_validation_errors()
            raise ValueError(f"分片配置无效: {'; '.join(errors)}")
    
    def process_chunks(self, chunks: List[dict]) -> List[dict]:
        """处理chunk列表，进行智能分片"""
        if not self.config.enable_fragmentation:
            logger.info("分片功能已禁用，返回原始chunks")
            return chunks
        
        logger.info(f"开始处理 {len(chunks)} 个chunks")
        
        # 执行分片
        fragmented_chunks = self._fragment_chunks(chunks)
        
        # 构建位置映射
        self.position_mapper.build_mapping(chunks, fragmented_chunks)
        
        # 重构上下文
        if self.config.enable_context_rebuild:
            self._rebuild_contexts(fragmented_chunks)
        
        logger.info(f"分片处理完成，生成 {len(fragmented_chunks)} 个chunks")
        return fragmented_chunks
    
    def _fragment_chunks(self, chunks: List[dict]) -> List[dict]:
        """对chunks进行分片处理"""
        fragmented_chunks = []
        
        for i, chunk in enumerate(chunks):
            if self._should_fragment(chunk):
                # 执行分片
                fragments = self._safe_fragment_chunk(chunk, i)
                fragmented_chunks.extend(fragments)
            else:
                # 保持原始chunk
                fragmented_chunks.append(chunk)
        
        return fragmented_chunks
    
    def _should_fragment(self, chunk: dict) -> bool:
        """判断是否需要分片"""
        return (
            chunk.get("type") == "text" and
            len(chunk.get("content", "")) > self.config.max_chunk_size and
            not chunk.get("metadata", {}).get("is_fragment") and
            self.config.enable_fragmentation
        )
    
    def _safe_fragment_chunk(self, chunk: dict, original_position: int) -> List[dict]:
        """安全的分片处理，包含错误处理"""
        try:
            return self._fragment_chunk(chunk, original_position)
        except Exception as e:
            logger.warning(f"分片失败，保持原始chunk: {str(e)}")
            return [chunk]  # 返回原始chunk
    
    def _fragment_chunk(self, chunk: dict, original_position: int) -> List[dict]:
        """执行分片操作"""
        original_content = chunk["content"]
        fragments = self.chunker.split_text(original_content)
        
        # 过滤掉过小的分片
        valid_fragments = [
            fragment for fragment in fragments 
            if len(fragment.strip()) >= self.config.min_fragment_size
        ]
        
        if not valid_fragments:
            logger.warning(f"分片后没有有效内容，保持原始chunk")
            return [chunk]
        
        fragment_chunks = []
        for i, fragment in enumerate(valid_fragments):
            fragment_chunk = self._create_fragment_chunk(
                original_chunk=chunk,
                fragment_content=fragment,
                fragment_index=i + 1,
                total_fragments=len(valid_fragments),
                original_position=original_position
            )
            fragment_chunks.append(fragment_chunk)
        
        logger.info(f"成功将chunk分片为 {len(fragment_chunks)} 个片段")
        return fragment_chunks
    
    def _create_fragment_chunk(self, original_chunk: dict, fragment_content: str, 
                              fragment_index: int, total_fragments: int, 
                              original_position: int) -> dict:
        """创建分片chunk"""
        original_metadata = original_chunk.get("metadata", {})
        
        # 计算分片在原文中的位置
        original_content = original_chunk["content"]
        start_pos = original_content.find(fragment_content)
        end_pos = start_pos + len(fragment_content) if start_pos != -1 else len(fragment_content)
        
        # 构建分片元数据
        fragment_metadata = {
            # 保持原始信息
            "doc_id": original_metadata.get("doc_id"),
            "paragraph_index": original_metadata.get("paragraph_index"),
            
            # 分片信息
            "is_fragment": True,
            "fragment_index": fragment_index,
            "total_fragments": total_fragments,
            "original_content": original_content,
            
            # 位置信息
            "original_position": original_position,
            "fragment_start_pos": start_pos,
            "fragment_end_pos": end_pos,
            
            # 关联信息
            "parent_paragraph_id": f"para_{original_metadata.get('paragraph_index', 'unknown')}",
        }
        
        # 创建分片chunk
        fragment_chunk = {
            "type": "text",
            "content": fragment_content,
            "metadata": fragment_metadata,
            "context": original_chunk.get("context", ""),  # 临时上下文，后续会重构
        }
        
        return fragment_chunk
    
    def _rebuild_contexts(self, chunks: List[dict]) -> None:
        """重构所有chunk的上下文"""
        # 重构分片chunk的上下文
        for chunk in chunks:
            if self.position_mapper.is_fragment(chunk):
                chunk["context"] = self.context_rebuilder.rebuild_fragment_context(
                    chunk, chunks, self.position_mapper
                )
        
        # 更新表格上下文
        table_chunks = [chunk for chunk in chunks if chunk.get("type") in ["table_full", "table_row"]]
        if table_chunks:
            self.context_rebuilder.update_table_context_for_fragments(
                table_chunks, chunks, self.position_mapper
            )
    
    def get_fragment_statistics(self, chunks: List[dict]) -> Dict:
        """获取分片统计信息"""
        total_chunks = len(chunks)
        fragment_chunks = [chunk for chunk in chunks if self.position_mapper.is_fragment(chunk)]
        original_chunks = total_chunks - len(fragment_chunks)
        
        # 统计段落分片情况
        paragraph_fragments = {}
        for chunk in fragment_chunks:
            para_idx = chunk.get("metadata", {}).get("paragraph_index")
            if para_idx:
                if para_idx not in paragraph_fragments:
                    paragraph_fragments[para_idx] = 0
                paragraph_fragments[para_idx] += 1
        
        return {
            "total_chunks": total_chunks,
            "original_chunks": original_chunks,
            "fragment_chunks": len(fragment_chunks),
            "fragmented_paragraphs": len(paragraph_fragments),
            "paragraph_fragments": paragraph_fragments
        } 