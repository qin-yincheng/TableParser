# main_processor.py
"""
主处理流程示例，展示完整的文档解析、增强、向量化和存储流程
"""

import asyncio
import os
from typing import List, Dict, Any
from parsers.doc_parser import DocFileParser
from parsers.xlsx_parser import XlsxFileParser
from parsers.fragment_config import FragmentConfig, TableProcessingConfig
from embedding_service import EmbeddingService
from vector_service import VectorService
from utils.logger import logger
from utils.config_manager import ConfigManager


class MainProcessor:
    """主处理器，协调整个文档处理流程"""

    def __init__(self):
        """初始化主处理器"""
        # 加载配置
        self.config_manager = ConfigManager()
        fragmentation_config = self.config_manager.get_fragmentation_config()
        
        # 创建默认的表格处理配置：Markdown格式 + 只生成完整表格块
        default_table_config = TableProcessingConfig(
            table_format="markdown",
            table_chunking_strategy="full_only"
        )
        
        # 根据配置创建文档解析器
        if fragmentation_config.get("enable", False):
            # 只传递实际使用的配置项
            fragment_config = FragmentConfig(
                enable_fragmentation=True,
                max_chunk_size=fragmentation_config.get("max_chunk_size", 1000),
                min_fragment_size=fragmentation_config.get("min_fragment_size", 200),
                chunk_overlap=fragmentation_config.get("chunk_overlap", 100),
                enable_context_rebuild=fragmentation_config.get("enable_context_rebuild", True),
                table_processing=default_table_config
            )
            self.doc_parser = DocFileParser(fragment_config=fragment_config)
            logger.info("启用分片功能，使用Markdown格式和只生成完整表格块")
        else:
            # 即使不启用分片，也使用表格配置
            fragment_config = FragmentConfig(table_processing=default_table_config)
            self.doc_parser = DocFileParser(fragment_config=fragment_config)
            logger.info("未启用分片功能，使用Markdown格式和只生成完整表格块")
        
        # Excel解析器也使用相同的表格配置
        self.xlsx_parser = XlsxFileParser(fragment_config=FragmentConfig(table_processing=default_table_config))
        self.embedding_service = EmbeddingService()
        self.vector_service = VectorService()

    async def process_document(self, file_path: str, kb_id: int) -> Dict[str, Any]:
        """
        处理单个文档的完整流程

        Args:
            file_path: 文档路径
            kb_id: 知识库ID

        Returns:
            Dict[str, Any]: 处理结果
        """
        try:
            logger.info(f"开始处理文档: {file_path}")

            # 1. 解析文档
            chunks = await self._parse_document(file_path)
            if not chunks:
                return {"success": False, "error": "文档解析失败", "chunks": []}

            logger.info(f"解析完成，共生成 {len(chunks)} 个分块")

            # 2. 生成向量嵌入
            logger.info("开始生成向量嵌入...")
            vectors = await self.embedding_service.generate_embeddings_batch(chunks)

            # 统计成功生成的向量数量
            successful_vectors = [v for v in vectors if v is not None]
            failed_count = len(vectors) - len(successful_vectors)
            logger.info(
                f"向量化完成，成功生成 {len(successful_vectors)} 个向量，失败 {failed_count} 个"
            )

            # 3. 存储到向量库
            stored_count = await self._store_chunks_to_vector_db(chunks, vectors, kb_id)

            result = {
                "success": True,
                "file_path": file_path,
                "total_chunks": len(chunks),
                "successful_vectors": len(successful_vectors),
                "failed_vectors": failed_count,
                "stored_count": stored_count,
                # "chunks": chunks,
            }

            logger.info(
                f"文档处理完成: {file_path} - 分块: {len(chunks)}, 向量: {len(successful_vectors)}, 存储: {stored_count}"
            )
            return result

        except Exception as e:
            logger.error(f"处理文档失败: {file_path}, 错误: {str(e)}")
            return {"success": False, "error": str(e), "file_path": file_path}

    async def _parse_document(self, file_path: str) -> List[Dict[str, Any]]:
        """
        解析文档

        Args:
            file_path: 文档路径

        Returns:
            List[Dict[str, Any]]: 分块列表
        """
        _, ext = os.path.splitext(file_path)
        ext = ext.lower().lstrip(".")

        if ext in ["doc", "docx"]:
            return await self.doc_parser.process(file_path)
        elif ext == "xlsx":
            return self.xlsx_parser.parse(file_path)
        else:
            raise ValueError(f"不支持的文档格式: {ext}")

    async def _store_chunks_to_vector_db(
        self, chunks: List[Dict], vectors: List, kb_id: int
    ) -> int:
        """
        将分块存储到向量数据库

        Args:
            chunks: 分块列表
            vectors: 向量列表
            kb_id: 知识库ID

        Returns:
            int: 成功存储的数量
        """
        # 确保集合存在
        if not self.vector_service.collection_exists(kb_id):
            self.vector_service.create_collection(kb_id)

        stored_count = 0

        for chunk, vector in zip(chunks, vectors):
            if vector is not None:
                try:
                    # 存储分块到向量库
                    result = self.vector_service.insert_data(vector, kb_id, chunk)
                    if result:
                        stored_count += 1
                except Exception as e:
                    logger.error(
                        f"存储分块失败: {chunk.get('chunk_id', 'unknown')}, 错误: {str(e)}"
                    )

        return stored_count

    def close(self):
        """关闭资源"""
        self.vector_service.close()


# 便捷函数
async def process_single_document(file_path: str, kb_id: int) -> Dict[str, Any]:
    """
    处理单个文档的便捷函数

    Args:
        file_path: 文档路径
        kb_id: 知识库ID

    Returns:
        Dict[str, Any]: 处理结果
    """
    processor = MainProcessor()
    try:
        result = await processor.process_document(file_path, kb_id)
        return result
    finally:
        processor.close()


async def process_multiple_documents(
    file_paths: List[str], kb_id: int
) -> List[Dict[str, Any]]:
    """
    批量处理多个文档

    Args:
        file_paths: 文档路径列表
        kb_id: 知识库ID

    Returns:
        List[Dict[str, Any]]: 处理结果列表
    """
    processor = MainProcessor()
    try:
        tasks = [
            processor.process_document(file_path, kb_id) for file_path in file_paths
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    {"success": False, "error": str(result), "file_path": file_paths[i]}
                )
            else:
                processed_results.append(result)

        # 只显示处理结果摘要
        success_count = sum(1 for r in processed_results if r.get("success", False))
        total_count = len(processed_results)
        logger.info(f"批量处理完成: {success_count}/{total_count} 个文档成功")

        return processed_results
    finally:
        processor.close()


async def check_and_handle_existing_data(processor: MainProcessor, kb_id: int, file_path: str) -> bool:
    """
    检查并处理已存在的数据
    
    Args:
        processor: 主处理器实例
        kb_id: 知识库ID
        file_path: 文档路径
        
    Returns:
        bool: True表示需要继续处理，False表示跳过处理
    """
    if not processor.vector_service.collection_exists(kb_id):
        logger.info(f"知识库 {kb_id} 不存在，将创建新的知识库")
        return True
    
    # 检查该文档是否已经处理过
    doc_id = os.path.basename(file_path)
    try:
        from weaviate.classes.query import Filter
        existing_data = processor.vector_service.query_by_filter(
            kb_id=kb_id,
            filter_query=Filter.by_property("doc_id").equal(doc_id),
            limit=1
        )
        
        if existing_data:
            logger.info(f"文档 {doc_id} 在知识库 {kb_id} 中已存在数据，将进行增量更新")
            # 删除旧数据
            delete_count = processor.vector_service.delete_by_filter(
                kb_id=kb_id,
                filter_query={"path": ["doc_id"], "operator": "Equal", "valueString": doc_id}
            )
            logger.info(f"删除了 {delete_count} 条旧记录")
        else:
            logger.info(f"文档 {doc_id} 在知识库 {kb_id} 中未找到，将新增数据")
            
        return True
        
    except Exception as e:
        logger.warning(f"检查已存在数据时出错: {str(e)}，继续处理")
        return True


async def process_documents_with_kb_id(file_paths: List[str], kb_id: int, force_recreate: bool = False):
    """
    处理文档到指定知识库
    
    Args:
        file_paths: 文档路径列表
        kb_id: 知识库ID
        force_recreate: 是否强制重建知识库
    """
    processor = MainProcessor()
    
    try:
        # 检查是否需要重建知识库
        if force_recreate and processor.vector_service.collection_exists(kb_id):
            logger.info(f"强制重建知识库 {kb_id}")
            processor.vector_service.delete_collection(kb_id)
            processor.vector_service.create_collection(kb_id)
        
        logger.info(f"开始处理 {len(file_paths)} 个文档到知识库 {kb_id}")
        
        results = []
        for file_path in file_paths:
            if not os.path.exists(file_path):
                logger.error(f"文件不存在: {file_path}")
                results.append({"success": False, "error": "文件不存在", "file_path": file_path})
                continue
            
            # 检查和处理已存在数据
            should_process = await check_and_handle_existing_data(processor, kb_id, file_path)
            
            if should_process:
                result = await processor.process_document(file_path, kb_id)
                results.append(result)
                logger.info(f"✅ 处理完成: {file_path} - 分块:{result.get('total_chunks', 0)} 存储:{result.get('stored_count', 0)}")
            else:
                logger.info(f"⏭️  跳过处理: {file_path}")
                results.append({"success": True, "skipped": True, "file_path": file_path})
        
        # 统计结果
        success_count = sum(1 for r in results if r.get("success", False))
        logger.info(f"📊 批量处理完成: {success_count}/{len(results)} 个文档成功")
        
        return results
        
    finally:
        processor.close()


def print_usage():
    """打印使用说明"""
    print("""
使用方法:
  python main_processor.py --kb-id <知识库ID> [选项] <文档路径...>

参数:
  --kb-id <ID>        指定知识库ID（必需）
  --force-recreate    强制重建知识库（删除现有数据）
  --help              显示此帮助信息

示例:
  # 处理单个文档到知识库100
  python main_processor.py --kb-id 100 test_data/test.docx
  
  # 处理多个文档到知识库200
  python main_processor.py --kb-id 200 test_data/test.docx test_data/test8.xlsx
  
  # 强制重建知识库并处理文档
  python main_processor.py --kb-id 300 --force-recreate test_data/test.docx
    """)


# 命令行入口
if __name__ == "__main__":
    import sys
    import argparse
    
    # 如果没有参数，显示使用说明
    if len(sys.argv) == 1:
        print("🚀 TableParser 主处理器")
        print_usage()
        
        # 运行默认示例
        async def run_default_example():
            print("\n🔸 运行默认示例（知识库ID: 100）...")
            file_paths = ["test_data/test.docx", "test_data/test8.xlsx"]
            results = await process_documents_with_kb_id(file_paths, 100)
            
            print("\n📋 处理结果:")
            for result in results:
                if result.get("success"):
                    print(f"  ✅ {result.get('file_path')}: {result.get('total_chunks', 0)}个分块")
                else:
                    print(f"  ❌ {result.get('file_path')}: {result.get('error', '未知错误')}")
        
        asyncio.run(run_default_example())
        sys.exit(0)
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='TableParser 文档处理器')
    parser.add_argument('--kb-id', type=int, required=True, help='知识库ID')
    parser.add_argument('--force-recreate', action='store_true', help='强制重建知识库')
    parser.add_argument('files', nargs='+', help='要处理的文档文件路径')
    
    try:
        args = parser.parse_args()
    except SystemExit:
        print_usage()
        sys.exit(1)
    
    # 执行处理
    async def main():
        print(f"🚀 开始处理文档到知识库 {args.kb_id}")
        if args.force_recreate:
            print("⚠️  将强制重建知识库")
        
        results = await process_documents_with_kb_id(
            file_paths=args.files,
            kb_id=args.kb_id,
            force_recreate=args.force_recreate
        )
        
        print(f"\n📊 最终结果:")
        for result in results:
            if result.get("success"):
                if result.get("skipped"):
                    print(f"  ⏭️  {result.get('file_path')}: 跳过处理")
                else:
                    print(f"  ✅ {result.get('file_path')}: {result.get('total_chunks', 0)}个分块，{result.get('stored_count', 0)}条存储")
            else:
                print(f"  ❌ {result.get('file_path')}: {result.get('error', '未知错误')}")
    
    asyncio.run(main())
