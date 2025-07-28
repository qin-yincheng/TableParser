#!/usr/bin/env python3
"""
调试向量库数据结构和内容
"""

import json
from vector_service import VectorService
from utils.logger import logger


def debug_collection_data():
    """调试集合数据"""
    print("🔍 调试向量库数据")
    print("=" * 50)

    vector_service = VectorService()
    try:
        kb_id = 1
        collection_name = f"Kb_{kb_id}"

        # 检查集合是否存在
        exists = vector_service.collection_exists(kb_id)
        print(f"集合 {collection_name} 存在: {exists}")

        if not exists:
            print("❌ 集合不存在，请先运行文档处理流程")
            return

        # 获取集合信息
        info = vector_service.get_collection_info(kb_id)
        print(f"集合信息: {json.dumps(info, ensure_ascii=False, indent=2)}")

        # 尝试查询所有数据
        print("\n📊 查询所有数据:")
        try:
            # 使用空的过滤条件查询所有数据
            all_results = vector_service.query_by_filter(
                kb_id=kb_id, filter_query={}, limit=10
            )
            print(f"查询到 {len(all_results)} 条数据")

            if all_results:
                print("\n📄 第一条数据示例:")
                first_result = all_results[0]
                print(
                    f"原始数据结构: {json.dumps(first_result, ensure_ascii=False, indent=2)}"
                )

                # 检查关键字段
                print(f"\n🔍 字段检查:")
                print(f"chunk_id: {first_result.get('chunk_id', 'NOT_FOUND')}")
                print(f"chunk_type: {first_result.get('chunk_type', 'NOT_FOUND')}")
                print(f"content: {first_result.get('content', 'NOT_FOUND')[:100]}...")
                print(f"doc_id: {first_result.get('doc_id', 'NOT_FOUND')}")

                # 检查 _additional 字段
                additional = first_result.get("_additional", {})
                print(
                    f"_additional: {json.dumps(additional, ensure_ascii=False, indent=2)}"
                )

            else:
                print("❌ 没有查询到任何数据")

        except Exception as e:
            print(f"❌ 查询失败: {str(e)}")

        # 尝试向量查询
        print("\n🔍 尝试向量查询:")
        try:
            # 使用正确的向量维度
            test_vector = [0.1] * 2048  # 智普API的向量维度是2048
            vector_results = vector_service.query_by_vector(
                kb_id=kb_id, vector=test_vector, limit=5
            )
            print(f"向量查询结果数量: {len(vector_results)}")

            if vector_results:
                print("向量查询第一条结果:")
                print(json.dumps(vector_results[0], ensure_ascii=False, indent=2))
            else:
                print("❌ 向量查询没有结果")

        except Exception as e:
            print(f"❌ 向量查询失败: {str(e)}")

    except Exception as e:
        print(f"❌ 调试过程出错: {str(e)}")
    finally:
        vector_service.close()


if __name__ == "__main__":
    debug_collection_data()
