import os
import sys
import json

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from parsers.xlsx_parser import XlsxFileParser, enhance_all_chunks
from parsers.fragment_config import FragmentConfig, TableProcessingConfig
import asyncio

TEST_FILE = os.path.join(os.path.dirname(__file__), "../test_data/test11.xlsx")
OUTPUT_FILE = os.path.join(
    os.path.dirname(__file__), "../test_data/test_xlsx_result.json"
)
LLM_OUTPUT_FILE = os.path.join(
    os.path.dirname(__file__), "../test_data/test11_xlsx_md_llm_result.json"
)


def test_xlsx_parser_basic(file_path, output_file):
    """测试Excel解析器基本功能（使用Markdown格式和只生成表格块）"""
    # 创建表格配置：Markdown格式 + 只生成完整表格块
    table_config = TableProcessingConfig(
        table_format="markdown",
        table_chunking_strategy="full_only"
    )
    
    parser = XlsxFileParser(fragment_config=FragmentConfig(table_processing=table_config))
    chunks = parser.parse(file_path)
    assert isinstance(chunks, list)
    assert len(chunks) > 0, "解析结果应包含至少一个分块"
    for chunk in chunks:
        assert isinstance(chunk, dict)
        assert "type" in chunk
        assert "content" in chunk
        assert "metadata" in chunk
        assert "doc_id" in chunk["metadata"]
        assert "sheet" in chunk["metadata"]
        # 检查表格格式配置
        if chunk.get("type") == "table_full":
            assert chunk["metadata"].get("table_format") == "markdown"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    print(f"测试通过，分块数量：{len(chunks)}，结果已保存到 {output_file}")
    
    # 统计表格块数量
    table_chunks = [chunk for chunk in chunks if chunk.get("type") == "table_full"]
    row_chunks = [chunk for chunk in chunks if chunk.get("type") == "table_row"]
    print(f"表格块数量：{len(table_chunks)}，行级分块数量：{len(row_chunks)}")


def test_xlsx_parser_llm_enhance(file_path, output_file):
    """测试Excel解析器LLM增强功能（使用Markdown格式和只生成表格块）"""
    # 创建表格配置：Markdown格式 + 只生成完整表格块
    table_config = TableProcessingConfig(
        table_format="markdown",
        table_chunking_strategy="full_only"
    )
    
    parser = XlsxFileParser(fragment_config=FragmentConfig(table_processing=table_config))
    chunks = parser.parse(file_path)
    enhanced_chunks = asyncio.run(enhance_all_chunks(chunks))
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(enhanced_chunks, f, ensure_ascii=False, indent=2)
    print(
        f"LLM增强测试通过，分块数量：{len(enhanced_chunks)}，结果已保存到 {output_file}"
    )
    
    # 统计表格块数量
    table_chunks = [chunk for chunk in enhanced_chunks if chunk.get("type") == "table_full"]
    row_chunks = [chunk for chunk in enhanced_chunks if chunk.get("type") == "table_row"]
    print(f"表格块数量：{len(table_chunks)}，行级分块数量：{len(row_chunks)}")


def test_xlsx_parser_format_verification(file_path):
    """验证Excel解析器的格式配置"""
    print("=== 验证Excel解析器格式配置 ===")
    
    # 创建表格配置：Markdown格式 + 只生成完整表格块
    table_config = TableProcessingConfig(
        table_format="markdown",
        table_chunking_strategy="full_only"
    )
    
    parser = XlsxFileParser(fragment_config=FragmentConfig(table_processing=table_config))
    chunks = parser.parse(file_path)
    
    # 验证配置
    assert parser.table_config.table_format == "markdown"
    assert parser.table_config.table_chunking_strategy == "full_only"
    print("✓ 解析器配置验证通过")
    
    # 验证表格块格式
    table_chunks = [chunk for chunk in chunks if chunk.get("type") == "table_full"]
    for chunk in table_chunks:
        assert chunk["metadata"].get("table_format") == "markdown"
        # 验证Markdown格式内容
        content = chunk.get("content", "")
        if content:
            assert "|" in content or content.strip() == "", "表格内容应该是Markdown格式"
    
    print("✓ 表格格式验证通过")
    
    # 验证只生成表格块（不应该有行级分块）
    row_chunks = [chunk for chunk in chunks if chunk.get("type") == "table_row"]
    assert len(row_chunks) == 0, "配置为只生成表格块时，不应该有行级分块"
    print("✓ 分块策略验证通过")


if __name__ == "__main__":
    # 基本功能测试
    # test_xlsx_parser_basic(TEST_FILE, OUTPUT_FILE)
    
    # LLM增强测试
    test_xlsx_parser_llm_enhance(TEST_FILE, LLM_OUTPUT_FILE)
    
    # 格式验证测试
    # test_xlsx_parser_format_verification(TEST_FILE)
