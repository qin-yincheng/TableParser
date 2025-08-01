"""
测试MainProcessor的默认配置
"""

import os
import sys
import asyncio
from unittest.mock import Mock, patch

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main_processor import MainProcessor
from parsers.fragment_config import TableProcessingConfig
from utils.logger import logger


def test_main_processor_default_config():
    """测试MainProcessor的默认配置"""
    print("=== 测试MainProcessor的默认配置 ===")
    
    # 创建MainProcessor实例
    processor = MainProcessor()
    
    # 验证Word文档解析器的配置
    assert processor.doc_parser.table_config.table_format == "markdown"
    assert processor.doc_parser.table_config.table_chunking_strategy == "full_only"
    print("✓ Word文档解析器配置测试通过")
    
    # 验证Excel文档解析器的配置
    assert processor.xlsx_parser.table_config.table_format == "markdown"
    assert processor.xlsx_parser.table_config.table_chunking_strategy == "full_only"
    print("✓ Excel文档解析器配置测试通过")
    
    # 验证配置一致性
    assert processor.doc_parser.table_config.table_format == processor.xlsx_parser.table_config.table_format
    assert processor.doc_parser.table_config.table_chunking_strategy == processor.xlsx_parser.table_config.table_chunking_strategy
    print("✓ 配置一致性测试通过")


def test_main_processor_with_fragmentation_config():
    """测试MainProcessor在启用分片时的配置"""
    print("=== 测试MainProcessor在启用分片时的配置 ===")
    
    # 模拟启用分片的配置
    with patch('main_processor.ConfigManager') as mock_config_manager:
        mock_instance = Mock()
        mock_instance.get_fragmentation_config.return_value = {
            "enable": True,
            "max_chunk_size": 1000,
            "min_fragment_size": 200,
            "chunk_overlap": 100,
            "enable_context_rebuild": True
        }
        mock_config_manager.return_value = mock_instance
        
        processor = MainProcessor()
        
        # 验证分片配置
        assert processor.doc_parser.fragment_manager is not None
        assert processor.doc_parser.table_config.table_format == "markdown"
        assert processor.doc_parser.table_config.table_chunking_strategy == "full_only"
        print("✓ 分片配置测试通过")


def test_main_processor_without_fragmentation_config():
    """测试MainProcessor在未启用分片时的配置"""
    print("=== 测试MainProcessor在未启用分片时的配置 ===")
    
    # 模拟未启用分片的配置
    with patch('main_processor.ConfigManager') as mock_config_manager:
        mock_instance = Mock()
        mock_instance.get_fragmentation_config.return_value = {
            "enable": False
        }
        mock_config_manager.return_value = mock_instance
        
        processor = MainProcessor()
        
        # 验证非分片配置
        assert processor.doc_parser.fragment_manager is None
        assert processor.doc_parser.table_config.table_format == "markdown"
        assert processor.doc_parser.table_config.table_chunking_strategy == "full_only"
        print("✓ 非分片配置测试通过")


def test_main_processor_table_config_consistency():
    """测试MainProcessor中表格配置的一致性"""
    print("=== 测试MainProcessor中表格配置的一致性 ===")
    
    processor = MainProcessor()
    
    # 验证所有解析器使用相同的表格配置
    doc_table_config = processor.doc_parser.table_config
    xlsx_table_config = processor.xlsx_parser.table_config
    
    # 检查配置对象
    assert isinstance(doc_table_config, TableProcessingConfig)
    assert isinstance(xlsx_table_config, TableProcessingConfig)
    
    # 检查配置值
    assert doc_table_config.table_format == "markdown"
    assert doc_table_config.table_chunking_strategy == "full_only"
    assert doc_table_config.enable_table_processing is True
    
    assert xlsx_table_config.table_format == "markdown"
    assert xlsx_table_config.table_chunking_strategy == "full_only"
    assert xlsx_table_config.enable_table_processing is True
    
    print("✓ 表格配置一致性测试通过")


def test_main_processor_backward_compatibility():
    """测试MainProcessor的向后兼容性"""
    print("=== 测试MainProcessor的向后兼容性 ===")
    
    # 测试MainProcessor可以正常创建
    try:
        processor = MainProcessor()
        assert processor is not None
        assert hasattr(processor, 'doc_parser')
        assert hasattr(processor, 'xlsx_parser')
        assert hasattr(processor, 'embedding_service')
        assert hasattr(processor, 'vector_service')
        print("✓ 基本功能向后兼容性测试通过")
    except Exception as e:
        print(f"❌ 向后兼容性测试失败: {str(e)}")
        raise


def test_main_processor_methods():
    """测试MainProcessor的方法"""
    print("=== 测试MainProcessor的方法 ===")
    
    processor = MainProcessor()
    
    # 测试方法存在性
    assert hasattr(processor, 'process_document')
    assert hasattr(processor, '_parse_document')
    assert hasattr(processor, '_store_chunks_to_vector_db')
    assert hasattr(processor, 'close')
    
    # 测试方法类型
    import inspect
    assert inspect.iscoroutinefunction(processor.process_document)
    assert inspect.iscoroutinefunction(processor._parse_document)
    assert inspect.iscoroutinefunction(processor._store_chunks_to_vector_db)
    assert inspect.isfunction(processor.close)
    
    print("✓ 方法存在性和类型测试通过")


def main():
    """运行所有测试"""
    print("开始测试MainProcessor的默认配置...")
    
    try:
        test_main_processor_default_config()
        test_main_processor_with_fragmentation_config()
        test_main_processor_without_fragmentation_config()
        test_main_processor_table_config_consistency()
        test_main_processor_backward_compatibility()
        test_main_processor_methods()
        
        print("\n🎉 所有MainProcessor配置测试通过！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        logger.error(f"MainProcessor配置测试失败: {str(e)}")
        raise


if __name__ == "__main__":
    main() 