import os
from parsers.doc_parser import DocFileParser
from parsers.fragment_config import FragmentConfig, TableProcessingConfig


def test_docx_without_fragmentation():
    """测试docx解析（不启用分片，使用Markdown格式和只生成表格块）"""
    # 创建表格配置：Markdown格式 + 只生成完整表格块
    table_config = TableProcessingConfig(
        table_format="markdown",
        table_chunking_strategy="full_only"
    )
    
    parser = DocFileParser(fragment_config=FragmentConfig(table_processing=table_config))
    input_path = os.path.join(os.path.dirname(__file__), "../test_data/testData.docx")
    result = parser.process(input_path)
    output_path = os.path.join(
        os.path.dirname(__file__), "../test_data/test_docx_result_no_frag.json"
    )
    import json

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"docx解析结果（无分片，Markdown格式）已保存到: {output_path}")


def test_docx_with_fragmentation():
    """测试docx解析（启用分片，使用Markdown格式和只生成表格块）"""
    # 创建分片配置
    table_config = TableProcessingConfig(
        table_format="markdown",
        table_chunking_strategy="full_only"
    )
    
    config = FragmentConfig(
        max_chunk_size=500,        # 较小的chunk大小以触发分片
        min_fragment_size=100,     # 最小分片大小
        chunk_overlap=50,          # 分片重叠
        enable_fragmentation=True, # 启用分片
        table_processing=table_config
    )
    
    parser = DocFileParser(fragment_config=config)
    input_path = os.path.join(os.path.dirname(__file__), "../test_data/testData1.docx")
    result = parser.process(input_path)
    output_path = os.path.join(
        os.path.dirname(__file__), "../test_data/test_docx_md_result_with_frag.json"
    )
    import json

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"docx解析结果（有分片，Markdown格式）已保存到: {output_path}")


def test_doc_without_fragmentation():
    """测试doc解析（不启用分片，使用Markdown格式和只生成表格块）"""
    # 创建表格配置：Markdown格式 + 只生成完整表格块
    table_config = TableProcessingConfig(
        table_format="markdown",
        table_chunking_strategy="full_only"
    )
    
    parser = DocFileParser(fragment_config=FragmentConfig(table_processing=table_config))
    input_path = os.path.join(os.path.dirname(__file__), "../test_data/testData.doc")
    result = parser.process(input_path)
    output_path = os.path.join(
        os.path.dirname(__file__), "../test_data/test_doc_result_no_frag.json"
    )
    import json

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"doc解析结果（无分片，Markdown格式）已保存到: {output_path}")


def test_doc_with_fragmentation():
    """测试doc解析（启用分片，使用Markdown格式和只生成表格块）"""
    # 创建分片配置
    table_config = TableProcessingConfig(
        table_format="markdown",
        table_chunking_strategy="full_only"
    )
    
    config = FragmentConfig(
        max_chunk_size=500,        # 较小的chunk大小以触发分片
        min_fragment_size=100,     # 最小分片大小
        chunk_overlap=50,          # 分片重叠
        enable_fragmentation=True, # 启用分片
        table_processing=table_config
    )
    
    parser = DocFileParser(fragment_config=config)
    input_path = os.path.join(os.path.dirname(__file__), "../test_data/testData.doc")
    result = parser.process(input_path)
    output_path = os.path.join(
        os.path.dirname(__file__), "../test_data/test_doc_result_with_frag1.json"
    )
    import json

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"doc解析结果（有分片，Markdown格式）已保存到: {output_path}")


def test_fragmentation_comparison():
    """对比分片前后的效果（使用Markdown格式和只生成表格块）"""
    print("=== 分片功能对比测试（Markdown格式） ===")
    
    # 测试docx文件
    input_path = os.path.join(os.path.dirname(__file__), "../test_data/testData.docx")
    
    # 无分片
    table_config = TableProcessingConfig(
        table_format="markdown",
        table_chunking_strategy="full_only"
    )
    parser_no_frag = DocFileParser(fragment_config=FragmentConfig(table_processing=table_config))
    result_no_frag = parser_no_frag.process(input_path)
    
    # 有分片
    config = FragmentConfig(
        max_chunk_size=500,
        min_fragment_size=100,
        chunk_overlap=50,
        enable_fragmentation=True,
        table_processing=table_config
    )
    parser_with_frag = DocFileParser(fragment_config=config)
    result_with_frag = parser_with_frag.process(input_path)
    
    print(f"无分片结果: {len(result_no_frag)} 个chunks")
    print(f"有分片结果: {len(result_with_frag)} 个chunks")
    
    # 统计分片情况
    fragment_chunks = [chunk for chunk in result_with_frag if chunk.get("metadata", {}).get("is_fragment")]
    print(f"分片chunks数量: {len(fragment_chunks)}")
    
    # 显示分片详情
    for i, chunk in enumerate(fragment_chunks[:3]):  # 只显示前3个分片
        metadata = chunk["metadata"]
        print(f"分片 {i+1}: 段落{metadata['paragraph_index']} 分片{metadata['fragment_index']}/{metadata['total_fragments']}")
        print(f"  内容长度: {len(chunk['content'])} 字符")
        print(f"  内容预览: {chunk['content'][:50]}...")
    
    # 检查表格格式
    table_chunks = [chunk for chunk in result_no_frag if chunk.get("type") == "table_full"]
    if table_chunks:
        print(f"\n表格块数量: {len(table_chunks)}")
        print(f"表格格式: {table_chunks[0].get('metadata', {}).get('table_format', 'unknown')}")
        print(f"表格内容预览: {table_chunks[0].get('content', '')[:100]}...")


def test_doc():
    """兼容原有测试函数"""
    test_doc_without_fragmentation()


if __name__ == "__main__":
    # 运行所有测试
    print("=== 开始测试文档解析和分片功能（Markdown格式） ===")
    
    # 1. 测试分片对比
    # test_fragmentation_comparison()
    
    # 2. 测试docx文件（有分片）
    print("\n=== 测试DOCX文件（启用分片，Markdown格式） ===")
    test_docx_with_fragmentation()
    
    # 3. 测试doc文件（有分片）
    # print("\n=== 测试DOC文件（启用分片，Markdown格式） ===")
    # test_doc_with_fragmentation()
    
    print("\n=== 所有测试完成 ===")
    print("结果文件保存在 test_data/ 目录下")
