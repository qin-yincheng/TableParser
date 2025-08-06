#!/usr/bin/env python3
"""
查询服务测试脚本
"""

import asyncio
import json
from query_service import QueryService
from utils.logger import logger


async def test_semantic_query():
    """测试语义相似度查询"""
    logger.info("=== 测试语义相似度查询 ===")

    query_service = QueryService()
    try:
        # 测试问题
        question = "2024年全国的地级市数有多少个？"
        kb_id = 1

        result = await query_service.query_by_semantic(
            question=question, kb_id=kb_id, limit=5
        )

        print(f"语义查询结果: {json.dumps(result, ensure_ascii=False, indent=2)}")

    except Exception as e:
        logger.error(f"语义查询测试失败: {str(e)}")
    finally:
        query_service.close()


def test_type_filter_query():
    """测试分块类型过滤查询"""
    logger.info("=== 测试分块类型过滤查询 ===")

    query_service = QueryService()
    try:
        # 测试单一类型查询
        logger.info("测试单一类型查询 (text)")
        result1 = query_service.query_by_type(chunk_types="text", kb_id=1, limit=5)
        print(f"单一类型查询结果: {json.dumps(result1, ensure_ascii=False, indent=2)}")

        # 测试多类型查询
        logger.info("测试多类型查询 (text, table_full)")
        result2 = query_service.query_by_type(
            chunk_types=["text", "table_full"], kb_id=1, limit=10
        )
        print(f"多类型查询结果: {json.dumps(result2, ensure_ascii=False, indent=2)}")

        # 测试表格类型查询
        logger.info("测试表格类型查询 (table_row)")
        result3 = query_service.query_by_type(chunk_types="table_row", kb_id=1, limit=5)
        print(f"表格类型查询结果: {json.dumps(result3, ensure_ascii=False, indent=2)}")

    except Exception as e:
        logger.error(f"类型过滤查询测试失败: {str(e)}")
    finally:
        query_service.close()


def test_hybrid_query():
    """测试混合查询"""
    logger.info("=== 测试混合查询 ===")

    query_service = QueryService()
    try:
        question = "表格数据"
        chunk_types = ["table_full", "table_row"]
        kb_id = 1

        result = query_service.query_hybrid(
            question=question, chunk_types=chunk_types, kb_id=kb_id, limit=5
        )

        print(f"混合查询结果: {json.dumps(result, ensure_ascii=False, indent=2)}")

    except Exception as e:
        logger.error(f"混合查询测试失败: {str(e)}")
    finally:
        query_service.close()


def test_error_cases():
    """测试错误情况"""
    logger.info("=== 测试错误情况 ===")

    query_service = QueryService()
    try:
        # 测试不存在的知识库
        logger.info("测试不存在的知识库")
        result1 = query_service.query_by_semantic(question="测试问题", kb_id=999)
        print(
            f"不存在知识库查询结果: {json.dumps(result1, ensure_ascii=False, indent=2)}"
        )

        # 测试空问题
        logger.info("测试空问题")
        result2 = query_service.query_by_semantic(question="", kb_id=1)
        print(f"空问题查询结果: {json.dumps(result2, ensure_ascii=False, indent=2)}")

        # 测试无效分块类型
        logger.info("测试无效分块类型")
        result3 = query_service.query_by_type(chunk_types="invalid_type", kb_id=1)
        print(f"无效类型查询结果: {json.dumps(result3, ensure_ascii=False, indent=2)}")

    except Exception as e:
        logger.error(f"错误情况测试失败: {str(e)}")
    finally:
        query_service.close()


def test_query_performance():
    """测试查询性能"""
    logger.info("=== 测试查询性能 ===")

    query_service = QueryService()
    try:
        import time

        # 测试语义查询性能
        start_time = time.time()
        result1 = query_service.query_by_semantic(
            question="性能测试问题", kb_id=1, limit=10
        )
        semantic_time = time.time() - start_time
        logger.info(f"语义查询耗时: {semantic_time:.2f}秒")

        # 测试类型过滤查询性能
        start_time = time.time()
        result2 = query_service.query_by_type(chunk_types="text", kb_id=1, limit=100)
        type_time = time.time() - start_time
        logger.info(f"类型过滤查询耗时: {type_time:.2f}秒")

        # 测试混合查询性能
        start_time = time.time()
        result3 = query_service.query_hybrid(
            question="混合查询测试",
            chunk_types=["text", "table_full"],
            kb_id=1,
            limit=10,
        )
        hybrid_time = time.time() - start_time
        logger.info(f"混合查询耗时: {hybrid_time:.2f}秒")

        print(f"性能测试结果:")
        print(f"  语义查询: {semantic_time:.2f}秒")
        print(f"  类型过滤: {type_time:.2f}秒")
        print(f"  混合查询: {hybrid_time:.2f}秒")

    except Exception as e:
        logger.error(f"性能测试失败: {str(e)}")
    finally:
        query_service.close()


async def main():
    """主测试函数"""
    logger.info("开始查询服务测试")

    # 运行所有测试
    await test_semantic_query()
    # test_type_filter_query()
    # test_hybrid_query()
    # test_error_cases()
    # test_query_performance()

    logger.info("查询服务测试完成")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())


if __name__ == "__main__":
    main()
