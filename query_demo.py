#!/usr/bin/env python3
"""
查询功能演示脚本
"""

import json
from query_service import QueryService
from utils.logger import logger


def print_result(result: dict):
    """格式化打印查询结果"""
    if not result.get("success", False):
        print(f"❌ 查询失败: {result.get('error', '未知错误')}")
        return

    print(f"✅ 查询成功")
    print(f"📊 结果数量: {result.get('total_count', 0)}")

    if "question" in result:
        print(f"❓ 问题: {result['question']}")

    if "chunk_types" in result:
        print(f"📋 查询类型: {result['chunk_types']}")

    results = result.get("results", [])
    if not results:
        print("📭 没有找到相关结果")
        return

    print(f"\n📄 查询结果:")
    for i, item in enumerate(results, 1):
        print(f"\n--- 结果 {i} ---")
        print(f"ID: {item.get('chunk_id', 'N/A')}")
        print(f"类型: {item.get('chunk_type', 'N/A')}")

        if "similarity_score" in item:
            print(f"相似度: {item.get('similarity_score', 0):.4f}")

        content = item.get("content", "")
        if len(content) > 200:
            content = content[:200] + "..."
        print(f"内容: {content}")

        metadata = item.get("metadata", {})
        if metadata:
            print(f"元数据: {json.dumps(metadata, ensure_ascii=False, indent=2)}")


def semantic_query_demo():
    """语义查询演示"""
    print("\n🔍 语义相似度查询演示")
    print("=" * 50)

    query_service = QueryService()
    try:
        questions = ["什么是人工智能？", "表格数据", "文档内容", "技术发展"]

        for question in questions:
            print(f"\n❓ 问题: {question}")
            result = query_service.query_by_semantic(
                question=question, kb_id=1, limit=3
            )
            print_result(result)

    finally:
        query_service.close()


def type_filter_demo():
    """类型过滤查询演示"""
    print("\n🔍 分块类型过滤查询演示")
    print("=" * 50)

    query_service = QueryService()
    try:
        # 测试不同分块类型
        type_tests = [
            ("text", "文本段落"),
            ("table_full", "完整表格"),
            ("table_row", "表格行"),
            (["text", "table_full"], "文本和表格"),
        ]

        for chunk_types, description in type_tests:
            print(f"\n📋 查询类型: {description} ({chunk_types})")
            result = query_service.query_by_type(
                chunk_types=chunk_types, kb_id=1, limit=3
            )
            print_result(result)

    finally:
        query_service.close()


def hybrid_query_demo():
    """混合查询演示"""
    print("\n🔍 混合查询演示")
    print("=" * 50)

    query_service = QueryService()
    try:
        # 测试混合查询场景
        hybrid_tests = [
            ("表格数据", ["table_full", "table_row"], "表格相关查询"),
            ("文档内容", ["text"], "文本内容查询"),
            ("技术信息", ["text", "table_full"], "综合信息查询"),
        ]

        for question, chunk_types, description in hybrid_tests:
            print(f"\n🔍 {description}")
            print(f"❓ 问题: {question}")
            print(f"📋 类型: {chunk_types}")

            result = query_service.query_hybrid(
                question=question, chunk_types=chunk_types, kb_id=1, limit=3
            )
            print_result(result)

    finally:
        query_service.close()


def interactive_query():
    """交互式查询"""
    print("\n🎯 交互式查询")
    print("=" * 50)
    print("输入 'quit' 退出")
    print("输入 'help' 查看帮助")

    query_service = QueryService()
    try:
        while True:
            print("\n" + "-" * 30)
            user_input = input("请输入查询问题: ").strip()

            if user_input.lower() == "quit":
                break
            elif user_input.lower() == "help":
                print(
                    """
查询帮助:
1. 直接输入问题 - 进行语义相似度查询
2. 输入 'type:text' - 查询文本类型
3. 输入 'type:table' - 查询表格类型
4. 输入 'type:all' - 查询所有类型
5. 输入 'quit' - 退出
6. 输入 'help' - 显示帮助
                """
                )
                continue
            elif user_input.startswith("type:"):
                # 类型过滤查询
                type_spec = user_input[5:].strip()
                if type_spec == "text":
                    chunk_types = "text"
                elif type_spec == "table":
                    chunk_types = ["table_full", "table_row"]
                elif type_spec == "all":
                    chunk_types = ["text", "table_full", "table_row"]
                else:
                    print("❌ 无效的类型指定，使用 'help' 查看帮助")
                    continue

                result = query_service.query_by_type(
                    chunk_types=chunk_types, kb_id=1, limit=5
                )
                print_result(result)
            else:
                # 语义查询
                result = query_service.query_by_semantic(
                    question=user_input, kb_id=1, limit=5
                )
                print_result(result)

    finally:
        query_service.close()


def main():
    """主函数"""
    print("🚀 查询服务演示")
    print("=" * 60)

    # 检查知识库是否存在
    query_service = QueryService()
    if not query_service._validate_kb_id(1):
        print("❌ 知识库 Kb_1 不存在，请先运行文档处理流程")
        return
    query_service.close()

    # 运行演示
    semantic_query_demo()
    type_filter_demo()
    hybrid_query_demo()

    # 交互式查询
    interactive_query()

    print("\n👋 演示结束")


if __name__ == "__main__":
    main()
