#!/usr/bin/env python3
"""
问答服务测试脚本
"""

import asyncio
import json
from qa_service import QAService
from utils.logger import logger


async def test_basic_qa():
    """测试基础问答功能"""
    logger.info("=== 测试基础问答功能 ===")

    qa_service = QAService()
    try:
        # 测试一般性问题
        question = "2025年6月26日的融资融券余额是多少？"
        kb_id = 4

        result = await qa_service.answer_question(question=question, kb_id=kb_id)

        print(f"基础问答结果: {json.dumps(result, ensure_ascii=False, indent=2)}")

    except Exception as e:
        logger.error(f"基础问答测试失败: {str(e)}")
    finally:
        qa_service.close()


async def test_table_qa():
    """测试表格相关问答"""
    logger.info("=== 测试表格相关问答 ===")

    qa_service = QAService()
    try:
        # 测试表格数据问题
        question = "表格中显示了哪些大学的招生数据？"
        kb_id = 1

        result = await qa_service.answer_question(question=question, kb_id=kb_id)

        print(f"表格问答结果: {json.dumps(result, ensure_ascii=False, indent=2)}")

    except Exception as e:
        logger.error(f"表格问答测试失败: {str(e)}")
    finally:
        qa_service.close()


async def test_error_cases():
    """测试错误情况"""
    logger.info("=== 测试错误情况 ===")

    qa_service = QAService()
    try:
        # 测试空问题
        logger.info("测试空问题")
        result1 = await qa_service.answer_question(question="", kb_id=1)
        print(f"空问题结果: {json.dumps(result1, ensure_ascii=False, indent=2)}")

        # 测试不存在的知识库
        logger.info("测试不存在的知识库")
        result2 = await qa_service.answer_question(question="测试问题", kb_id=999)
        print(f"不存在知识库结果: {json.dumps(result2, ensure_ascii=False, indent=2)}")

        # 测试无相关信息的问题
        logger.info("测试无相关信息的问题")
        result3 = await qa_service.answer_question(
            question="火星上有多少人口？", kb_id=1
        )
        print(f"无相关信息结果: {json.dumps(result3, ensure_ascii=False, indent=2)}")

    except Exception as e:
        logger.error(f"错误情况测试失败: {str(e)}")
    finally:
        qa_service.close()


async def test_qa_performance():
    """测试问答性能"""
    logger.info("=== 测试问答性能 ===")

    qa_service = QAService()
    try:
        import time

        questions = [
            "Cedar 大学在2005年招收了多少名本科新生？",
            "表格中显示了哪些大学的招生数据？",
            "为什么选择Cedar大学？",
            "招生数据统计表包含哪些信息？",
        ]

        total_time = 0
        success_count = 0

        for i, question in enumerate(questions, 1):
            logger.info(f"测试问题 {i}: {question}")

            start_time = time.time()
            result = await qa_service.answer_question(question=question, kb_id=1)
            end_time = time.time()

            question_time = end_time - start_time
            total_time += question_time

            if result.get("success"):
                success_count += 1
                logger.info(f"问题 {i} 成功，耗时: {question_time:.2f}秒")
            else:
                logger.warning(f"问题 {i} 失败: {result.get('error')}")

        avg_time = total_time / len(questions)
        success_rate = success_count / len(questions) * 100

        print(f"性能测试结果:")
        print(f"  总问题数: {len(questions)}")
        print(f"  成功数: {success_count}")
        print(f"  成功率: {success_rate:.1f}%")
        print(f"  平均耗时: {avg_time:.2f}秒")
        print(f"  总耗时: {total_time:.2f}秒")

    except Exception as e:
        logger.error(f"性能测试失败: {str(e)}")
    finally:
        qa_service.close()


async def main():
    """主测试函数"""
    logger.info("开始问答服务测试")

    # 运行所有测试
    await test_basic_qa()
    # await test_table_qa()
    # await test_error_cases()
    # await test_qa_performance()

    logger.info("问答服务测试完成")


if __name__ == "__main__":
    asyncio.run(main())
