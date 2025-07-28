#!/usr/bin/env python3
"""
调试查询返回的原始数据结构
"""

import json
import asyncio
from query_service import QueryService
from utils.logger import logger


async def debug_query_results():
    """调试查询返回的原始数据结构"""
    print("🔍 调试查询返回的原始数据结构")
    print("=" * 50)

    query_service = QueryService()
    try:
        question = "Cedar 大学在2005年招收了多少名本科新生？"
        kb_id = 1

        # 直接调用向量服务查看原始结果
        print("📊 查看VectorService返回的原始数据:")

        # 问题向量化
        question_vector = await query_service._vectorize_question(question)
        if question_vector is None:
            print("❌ 问题向量化失败")
            return

        print(f"✅ 问题向量化成功，向量维度: {len(question_vector)}")

        # 执行向量查询
        raw_results = query_service.vector_service.query_by_vector(
            kb_id=kb_id, vector=question_vector, limit=5
        )

        print(f"📄 原始查询结果数量: {len(raw_results)}")

        if raw_results:
            print("\n🔍 第一条原始结果:")
            first_result = raw_results[0]

            # 尝试JSON序列化
            try:
                print(
                    f"原始数据结构: {json.dumps(first_result, ensure_ascii=False, indent=2)}"
                )
            except Exception as e:
                print(f"JSON序列化失败: {str(e)}")
                print(f"数据类型: {type(first_result)}")
                print(f"数据内容: {first_result}")

            # 检查所有字段
            print(f"\n🔍 字段检查:")
            if isinstance(first_result, dict):
                for key, value in first_result.items():
                    print(f"  {key}: {type(value)} = {value}")
            else:
                print(f"  结果不是字典类型: {type(first_result)}")

        else:
            print("❌ 没有查询到原始结果")

    except Exception as e:
        print(f"❌ 调试过程出错: {str(e)}")
        import traceback

        traceback.print_exc()
    finally:
        query_service.close()


if __name__ == "__main__":
    asyncio.run(debug_query_results())
