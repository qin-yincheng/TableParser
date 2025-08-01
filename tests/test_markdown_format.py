#!/usr/bin/env python3
"""
测试markdown格式修复
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.xlsx_parser import XlsxFileParser
from parsers.doc_parser import DocFileParser
from parsers.fragment_config import FragmentConfig, TableProcessingConfig
import pandas as pd
import json


def test_xlsx_markdown_format():
    """测试xlsx解析器的markdown格式"""
    print("=== 测试XLSX解析器的Markdown格式 ===")

    # 创建测试配置
    config = FragmentConfig()
    config.table_processing.table_format = "markdown"
    config.table_processing.table_chunking_strategy = "full_only"

    parser = XlsxFileParser(config)

    # 测试文件路径
    test_file = "test_data/testData.xlsx"

    if os.path.exists(test_file):
        try:
            result = parser.parse(test_file)
            print(f"解析结果数量: {len(result)}")

            for i, chunk in enumerate(result):
                print(f"\n--- 分块 {i+1} ---")
                print(f"类型: {chunk.get('type')}")
                print(f"内容长度: {len(chunk.get('content', ''))}")

                # 检查markdown格式
                content = chunk.get('content', '')
                if content:
                    lines = content.split('\n')
                    print(f"行数: {len(lines)}")

                    # 检查是否有空行
                    empty_lines = [i for i, line in enumerate(lines) if line.strip() == '']
                    if empty_lines:
                        print(f"警告: 发现空行在位置: {empty_lines}")
                    else:
                        print("✓ 没有发现空行")

                    # 检查表格结构
                    if '|' in content:
                        print("✓ 包含表格分隔符")
                        # 检查每行的列数是否一致
                        table_lines = [line for line in lines if '|' in line]
                        if table_lines:
                            col_counts = [line.count('|') - 1 for line in table_lines]
                            if len(set(col_counts)) == 1:
                                print(f"✓ 所有行的列数一致: {col_counts[0]}")
                            else:
                                print(f"✗ 列数不一致: {col_counts}")
                    else:
                        print("✗ 不包含表格分隔符")

                    # 检查分隔线格式
                    separator_lines = [line for line in lines if '---' in line and '|' in line]
                    if separator_lines:
                        print("✓ 包含分隔线")
                        for sep_line in separator_lines:
                            # 检查分隔符格式
                            if ' --- ' in sep_line:
                                print("✗ 分隔符格式不规范（包含多余空格）")
                            elif '---:' in sep_line:
                                print("✓ 包含右对齐分隔符")
                            elif '---' in sep_line:
                                print("✓ 分隔符格式正确")
                    else:
                        print("✗ 不包含分隔线")

                    # 检查表头行数
                    header_lines = [line for line in lines if '|' in line and '---' not in line]
                    if len(header_lines) == 1:
                        print("✓ 单行表头（符合Markdown标准）")
                    elif len(header_lines) > 1:
                        print(f"✗ 多行表头（不符合Markdown标准）: {len(header_lines)} 行")
                    else:
                        print("✗ 没有表头")

                    # 检查表头内容是否包含层次结构
                    if header_lines:
                        header_content = header_lines[0]
                        if '/' in header_content:
                            print("✓ 表头包含层次结构分隔符")
                            # 检查具体的层次结构
                            check_header_hierarchy(header_content)
                        else:
                            print("✓ 表头格式正确")

                # 保存前几个字符用于检查
                if content:
                    print(f"内容预览: {content[:200]}...")

        except Exception as e:
            print(f"解析失败: {str(e)}")
    else:
        print(f"测试文件不存在: {test_file}")


def check_header_hierarchy(header_content: str):
    """检查表头的层次结构是否正确。"""
    # 检查是否包含期望的层次结构
    expected_patterns = [
        "营业总收入/营业总收入(元)",
        "营业总收入/同比增长(%)",
        "营业总收入/季度环比增长(%)",
        "净利润/净利润(元)",
        "净利润/同比增长(%)",
        "净利润/季度环比增长(%)"
    ]
    
    found_patterns = []
    for pattern in expected_patterns:
        if pattern in header_content:
            found_patterns.append(pattern)
    
    if found_patterns:
        print(f"✓ 发现正确的层次结构: {len(found_patterns)} 个")
        for pattern in found_patterns:
            print(f"  - {pattern}")
    else:
        print("✗ 未发现期望的层次结构")


def test_doc_markdown_format():
    """测试doc解析器的markdown格式"""
    print("\n=== 测试DOC解析器的Markdown格式 ===")

    # 创建测试配置
    config = FragmentConfig()
    config.table_processing.table_format = "markdown"
    config.table_processing.table_chunking_strategy = "full_only"

    parser = DocFileParser(config)

    # Test file paths
    test_files = ["test_data/testData.docx"] # Removed "test_data/testData.doc" as it requires LibreOffice conversion which might not be set up in all environments.

    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\n测试文件: {test_file}")
            try:
                result = parser.process(test_file)
                print(f"解析结果数量: {len(result)}")

                for i, chunk in enumerate(result):
                    print(f"\n--- 分块 {i+1} ---")
                    print(f"类型: {chunk.get('type')}")
                    print(f"内容长度: {len(chunk.get('content', ''))}")

                    # 检查markdown格式
                    content = chunk.get('content', '')
                    if content:
                        lines = content.split('\n')
                        print(f"行数: {len(lines)}")

                        # 检查是否有空行
                        empty_lines = [i for i, line in enumerate(lines) if line.strip() == '']
                        if empty_lines:
                            print(f"警告: 发现空行在位置: {empty_lines}")
                        else:
                            print("✓ 没有发现空行")

                        # 检查表格结构
                        if '|' in content:
                            print("✓ 包含表格分隔符")
                            # 检查每行的列数是否一致
                            table_lines = [line for line in lines if '|' in line]
                            if table_lines:
                                col_counts = [line.count('|') - 1 for line in table_lines]
                                if len(set(col_counts)) == 1:
                                    print(f"✓ 所有行的列数一致: {col_counts[0]}")
                                else:
                                    print(f"✗ 列数不一致: {col_counts}")
                        else:
                            print("✗ 不包含表格分隔符")

                        # 检查分隔线格式
                        separator_lines = [line for line in lines if '---' in line and '|' in line]
                        if separator_lines:
                            print("✓ 包含分隔线")
                            for sep_line in separator_lines:
                                # 检查分隔符格式
                                if ' --- ' in sep_line:
                                    print("✗ 分隔符格式不规范（包含多余空格）")
                                elif '---:' in sep_line:
                                    print("✓ 包含右对齐分隔符")
                                elif '---' in sep_line:
                                    print("✓ 分隔符格式正确")
                        else:
                            print("✗ 不包含分隔线")

                        # 检查表头行数
                        header_lines = [line for line in lines if '|' in line and '---' not in line]
                        if len(header_lines) == 1:
                            print("✓ 单行表头（符合Markdown标准）")
                        elif len(header_lines) > 1:
                            print(f"✗ 多行表头（不符合Markdown标准）: {len(header_lines)} 行")
                        else:
                            print("✗ 没有表头")

                        # 检查表头内容是否包含层次结构
                        if header_lines:
                            header_content = header_lines[0]
                            if '/' in header_content:
                                print("✓ 表头包含层次结构分隔符")
                            else:
                                print("✓ 表头格式正确")

                    # 保存前几个字符用于检查
                    if content:
                        print(f"内容预览: {content[:200]}...")

            except Exception as e:
                print(f"解析失败: {str(e)}")
        else:
            print(f"测试文件不存在: {test_file}")


def create_test_data():
    """创建测试数据用于验证"""
    print("\n=== 创建测试数据 ===")

    # 创建一个简单的测试DataFrame
    data = {
        'A': ['Header1', '', 'Data1', '', 'Data2'],
        'B': ['Header2', '', 'Value1', '', 'Value2'],
        'C': ['Header3', '', 'Info1', '', 'Info2']
    }
    df = pd.DataFrame(data)

    print("原始数据:")
    print(df)
    print("\nDataFrame信息:")
    print(f"形状: {df.shape}")
    print(f"列数: {df.shape[1]}")
    print(f"行数: {df.shape[0]}")

    # 检查空行
    empty_rows = []
    for i in range(len(df)):
        if not df.iloc[i].notna().any():
            empty_rows.append(i)

    print(f"空行索引: {empty_rows}")

    return df


if __name__ == "__main__":
    print("开始测试markdown格式修复...")

    # 创建测试数据
    test_df = create_test_data()

    # 测试xlsx解析器
    test_xlsx_markdown_format()

    # 测试doc解析器
    test_doc_markdown_format()

    print("\n测试完成!") 