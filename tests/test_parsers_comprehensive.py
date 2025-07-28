# test_parsers_comprehensive.py
"""
综合测试doc_parser.py和xlsx_parser.py的功能
"""

import asyncio
import json
import os
from datetime import datetime
from parsers.doc_parser import DocFileParser
from parsers.xlsx_parser import XlsxFileParser
from utils.logger import logger


def test_doc_parser_comprehensive():
    """综合测试Word文档解析器"""
    print("=" * 60)
    print("Word文档解析器综合测试")
    print("=" * 60)

    parser = DocFileParser()
    test_files = ["test_data/testData.docx", "test_data/testData.doc"]

    results = {}

    for file_path in test_files:
        if not os.path.exists(file_path):
            print(f"⚠️  文件不存在: {file_path}")
            continue

        print(f"\n📄 正在解析: {file_path}")

        try:
            # 记录开始时间
            start_time = datetime.now()

            # 解析文档
            chunks = parser.process(file_path)

            # 记录结束时间
            end_time = datetime.now()
            parse_duration = (end_time - start_time).total_seconds()

            # 详细统计
            chunk_types = {}
            enhanced_chunks = 0
            total_content_length = 0

            for chunk in chunks:
                chunk_type = chunk.get("type", "unknown")
                chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1

                # 检查是否包含LLM增强内容
                metadata = chunk.get("metadata", {})
                if metadata.get("description") or metadata.get("keywords"):
                    enhanced_chunks += 1

                # 统计内容长度
                content = chunk.get("content", "")
                total_content_length += len(content)

            # 构建结果
            result_info = {
                "file_path": file_path,
                "file_size": os.path.getsize(file_path),
                "total_chunks": len(chunks),
                "chunk_types": chunk_types,
                "enhanced_chunks": enhanced_chunks,
                "total_content_length": total_content_length,
                "parse_duration_seconds": parse_duration,
                "parse_time": datetime.now().isoformat(),
                "success": True,
                "chunks": chunks,
            }

            results[file_path] = result_info

            print(f"✅ 解析成功")
            print(f"   📊 总分块数: {len(chunks)}")
            print(f"   🏷️  分块类型: {chunk_types}")
            print(f"   🧠 增强分块: {enhanced_chunks}")
            print(f"   📏 总内容长度: {total_content_length:,} 字符")
            print(f"   ⏱️  解析耗时: {parse_duration:.2f} 秒")

        except Exception as e:
            error_info = {
                "file_path": file_path,
                "error": str(e),
                "parse_time": datetime.now().isoformat(),
                "success": False,
                "chunks": [],
            }
            results[file_path] = error_info

            print(f"❌ 解析失败: {str(e)}")

    return results


def test_xlsx_parser_comprehensive():
    """综合测试Excel文档解析器"""
    print("\n" + "=" * 60)
    print("Excel文档解析器综合测试")
    print("=" * 60)

    parser = XlsxFileParser()
    test_files = ["test_data/testData.xlsx", "test_data/test.xlsx"]

    results = {}

    for file_path in test_files:
        if not os.path.exists(file_path):
            print(f"⚠️  文件不存在: {file_path}")
            continue

        print(f"\n📊 正在解析: {file_path}")

        try:
            # 记录开始时间
            start_time = datetime.now()

            # 解析文档
            chunks = parser.parse(file_path)

            # 记录结束时间
            end_time = datetime.now()
            parse_duration = (end_time - start_time).total_seconds()

            # 详细统计
            chunk_types = {}
            sheet_info = {}
            enhanced_chunks = 0
            total_content_length = 0
            merged_cells_count = 0

            for chunk in chunks:
                chunk_type = chunk.get("type", "unknown")
                chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1

                # 统计sheet信息
                metadata = chunk.get("metadata", {})
                sheet_name = metadata.get("sheet", "unknown")
                if sheet_name not in sheet_info:
                    sheet_info[sheet_name] = {
                        "chunks": 0,
                        "tables": 0,
                        "rows": 0,
                        "merged_cells": 0,
                    }
                sheet_info[sheet_name]["chunks"] += 1

                if chunk_type == "table_full":
                    sheet_info[sheet_name]["tables"] += 1
                    # 统计合并单元格
                    merged_cells = metadata.get("merged_cells", [])
                    merged_cells_count += len(merged_cells)
                    sheet_info[sheet_name]["merged_cells"] += len(merged_cells)
                elif chunk_type == "table_row":
                    sheet_info[sheet_name]["rows"] += 1

                # 检查是否包含LLM增强内容
                if metadata.get("description") or metadata.get("keywords"):
                    enhanced_chunks += 1

                # 统计内容长度
                content = chunk.get("content", "")
                total_content_length += len(content)

            # 构建结果
            result_info = {
                "file_path": file_path,
                "file_size": os.path.getsize(file_path),
                "total_chunks": len(chunks),
                "chunk_types": chunk_types,
                "sheet_info": sheet_info,
                "enhanced_chunks": enhanced_chunks,
                "total_content_length": total_content_length,
                "merged_cells_count": merged_cells_count,
                "parse_duration_seconds": parse_duration,
                "parse_time": datetime.now().isoformat(),
                "success": True,
                "chunks": chunks,
            }

            results[file_path] = result_info

            print(f"✅ 解析成功")
            print(f"   📊 总分块数: {len(chunks)}")
            print(f"   🏷️  分块类型: {chunk_types}")
            print(f"   📋 Sheet数量: {len(sheet_info)}")
            print(f"   🧠 增强分块: {enhanced_chunks}")
            print(f"   📏 总内容长度: {total_content_length:,} 字符")
            print(f"   🔗 合并单元格: {merged_cells_count}")
            print(f"   ⏱️  解析耗时: {parse_duration:.2f} 秒")

        except Exception as e:
            error_info = {
                "file_path": file_path,
                "error": str(e),
                "parse_time": datetime.now().isoformat(),
                "success": False,
                "chunks": [],
            }
            results[file_path] = error_info

            print(f"❌ 解析失败: {str(e)}")

    return results


def generate_comprehensive_report(doc_results, xlsx_results):
    """生成综合测试报告"""
    print("\n" + "=" * 80)
    print("综合测试报告")
    print("=" * 80)

    # 总体统计
    total_files = len(doc_results) + len(xlsx_results)
    successful_files = sum(
        1 for r in doc_results.values() if r.get("success", False)
    ) + sum(1 for r in xlsx_results.values() if r.get("success", False))
    failed_files = total_files - successful_files

    print(f"📈 总体统计:")
    print(f"   总文件数: {total_files}")
    print(f"   成功解析: {successful_files}")
    print(f"   解析失败: {failed_files}")
    print(
        f"   成功率: {successful_files/total_files*100:.1f}%"
        if total_files > 0
        else "   成功率: 0%"
    )

    # Word文档统计
    if doc_results:
        print(f"\n📄 Word文档统计:")
        doc_chunks = sum(
            len(r.get("chunks", []))
            for r in doc_results.values()
            if r.get("success", False)
        )
        doc_enhanced = sum(
            r.get("enhanced_chunks", 0)
            for r in doc_results.values()
            if r.get("success", False)
        )
        print(f"   总分块数: {doc_chunks}")
        print(f"   增强分块: {doc_enhanced}")
        print(
            f"   增强率: {doc_enhanced/doc_chunks*100:.1f}%"
            if doc_chunks > 0
            else "   增强率: 0%"
        )

    # Excel文档统计
    if xlsx_results:
        print(f"\n📊 Excel文档统计:")
        xlsx_chunks = sum(
            len(r.get("chunks", []))
            for r in xlsx_results.values()
            if r.get("success", False)
        )
        xlsx_enhanced = sum(
            r.get("enhanced_chunks", 0)
            for r in xlsx_results.values()
            if r.get("success", False)
        )
        xlsx_tables = sum(
            sum(sheet.get("tables", 0) for sheet in r.get("sheet_info", {}).values())
            for r in xlsx_results.values()
            if r.get("success", False)
        )
        print(f"   总分块数: {xlsx_chunks}")
        print(f"   增强分块: {xlsx_enhanced}")
        print(f"   表格数量: {xlsx_tables}")
        print(
            f"   增强率: {xlsx_enhanced/xlsx_chunks*100:.1f}%"
            if xlsx_chunks > 0
            else "   增强率: 0%"
        )

    print("=" * 80)


def save_comprehensive_results(doc_results, xlsx_results, output_file):
    """保存综合测试结果"""
    comprehensive_results = {
        "test_time": datetime.now().isoformat(),
        "doc_parser_results": doc_results,
        "xlsx_parser_results": xlsx_results,
        "summary": {
            "total_files": len(doc_results) + len(xlsx_results),
            "successful_files": sum(
                1 for r in doc_results.values() if r.get("success", False)
            )
            + sum(1 for r in xlsx_results.values() if r.get("success", False)),
            "doc_chunks": sum(
                len(r.get("chunks", []))
                for r in doc_results.values()
                if r.get("success", False)
            ),
            "xlsx_chunks": sum(
                len(r.get("chunks", []))
                for r in xlsx_results.values()
                if r.get("success", False)
            ),
        },
    }

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(comprehensive_results, f, ensure_ascii=False, indent=2)
        print(f"✅ 综合测试结果已保存到: {output_file}")
    except Exception as e:
        print(f"❌ 保存文件失败: {str(e)}")


def main():
    """主函数"""
    print("文档解析器综合测试")
    print("=" * 80)

    # 确保输出目录存在
    os.makedirs("test_results", exist_ok=True)

    # 测试Word文档解析器
    doc_results = test_doc_parser_comprehensive()

    # 测试Excel文档解析器
    xlsx_results = test_xlsx_parser_comprehensive()

    # 生成综合报告
    generate_comprehensive_report(doc_results, xlsx_results)

    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"test_results/comprehensive_parser_test_{timestamp}.json"
    save_comprehensive_results(doc_results, xlsx_results, output_file)

    print(f"\n🎉 综合测试完成！结果已保存到: {output_file}")


if __name__ == "__main__":
    main()
